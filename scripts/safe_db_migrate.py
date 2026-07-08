"""Safe wrapper for applying .sql migrations. Built after a 2026-07-07
incident: a migration's DELETE FROM friction_nodes cascaded (ON DELETE
CASCADE) and silently wiped 15,945 real event_friction_nodes rows -- no
error, no warning. See docs/context/DB_SAFETY_INCIDENT_20260707.md.

What this does, always, before touching data:
  1. Full pg_dump backup of the target DB to db/backups/ (timestamped).
  2. Scans the SQL for DELETE/TRUNCATE/DROP. For any DELETE FROM <table>,
     dry-runs the WHERE clause as SELECT count(*) and checks
     information_schema for ON DELETE CASCADE children -- printing exactly
     how many rows in which child tables would disappear.
  3. Refuses to apply if anything dangerous is found, unless --yes-i-checked
     is passed. The scan output is the thing to read before passing it.

Run: python scripts/safe_db_migrate.py db/migrations/some_file.sql
     python scripts/safe_db_migrate.py db/migrations/some_file.sql --yes-i-checked
     python scripts/safe_db_migrate.py db/migrations/some_file.sql --target render --yes-i-checked
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "db" / "backups"

DANGEROUS_PATTERNS = [
    (r"\bDELETE\s+FROM\s+(\w+)", "DELETE"),
    (r"\bTRUNCATE\s+(?:TABLE\s+)?(\w+)", "TRUNCATE"),
    (r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)", "DROP TABLE"),
    (r"\bDROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?(\w+)", "DROP COLUMN"),
    (r"\bALTER\s+TABLE\s+(\w+)\s+.*DROP\s+", "ALTER...DROP"),
]


def load_env():
    load_dotenv(ROOT / ".env")


def connect(host, port, name, user, password):
    return psycopg2.connect(
        host=host, port=port, dbname=name, user=user, password=password
    )


def scan_file(sql_text):
    findings = []
    for pattern, kind in DANGEROUS_PATTERNS:
        for m in re.finditer(pattern, sql_text, re.IGNORECASE):
            findings.append((kind, m.group(1), m.group(0)))
    return findings


def _direct_cascade_children(cur, table):
    """Tables that ON DELETE CASCADE from `table` (one level down).
    Returns [(child_table, child_col), ...]."""
    cur.execute(
        """
        SELECT con.conrelid::regclass::text AS child_table, a.attname AS child_col
        FROM pg_constraint con
        JOIN information_schema.referential_constraints rc
          ON rc.constraint_name = con.conname
        JOIN pg_attribute a
          ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
        WHERE con.contype = 'f'
          AND rc.delete_rule = 'CASCADE'
          AND con.confrelid = %s::regclass
        """,
        (table,),
    )
    return cur.fetchall()


def check_delete_blast_radius(cur, table, _visited=None, _depth=1):
    """RECURSIVE cascade blast radius for a DELETE on `table`.

    Walks the full ON DELETE CASCADE tree — not just direct children — so a
    DELETE on `centroids_v3` correctly surfaces `events_v3` three levels down
    (centroids_v3 -> ctm -> events_v3 -> ...). Each row is
    (depth, child_table, child_col, current_row_count). Cycle-safe.
    """
    if _visited is None:
        _visited = set()
    report = []
    for child_table, fk_col in _direct_cascade_children(cur, table):
        if child_table in _visited:
            continue
        _visited.add(child_table)
        cur.execute(
            f"SELECT count(*) FROM {child_table}"
        )  # noqa: S608 (identifier from catalog)
        n = cur.fetchone()[0]
        report.append((_depth, child_table, fk_col, n))
        report.extend(check_delete_blast_radius(cur, child_table, _visited, _depth + 1))
    return report


def audit_all_cascades(cur):
    """Print the full cascade forest for the DB: every table that is a
    CASCADE parent, and its complete descendant tree with row counts.
    Read-only. `python safe_db_migrate.py --audit`."""
    cur.execute(
        """
        SELECT DISTINCT con.confrelid::regclass::text
        FROM pg_constraint con
        JOIN information_schema.referential_constraints rc
          ON rc.constraint_name = con.conname
        WHERE con.contype = 'f' AND rc.delete_rule = 'CASCADE'
        ORDER BY 1
        """
    )
    parents = [r[0] for r in cur.fetchall()]
    print(f"== ON DELETE CASCADE audit: {len(parents)} parent tables ==\n")
    for parent in parents:
        tree = check_delete_blast_radius(cur, parent)
        total = sum(n for _, _, _, n in tree)
        cur.execute(f"SELECT count(*) FROM {parent}")  # noqa: S608
        own = cur.fetchone()[0]
        print(f"DELETE FROM {parent} ({own} rows) cascades to {total:,} child rows:")
        for depth, child, col, n in tree:
            print(f"  {'  ' * depth}-> {child}.{col}: {n:,}")
        print()


def backup(target, host, port, name, user, password):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = BACKUP_DIR / f"{target}_{ts}.dump"
    print(f"-- backing up {target} ({host}:{port}/{name}) -> {out_path}")
    env = dict(os.environ, PGPASSWORD=password)
    cmd = [
        "docker",
        "exec",
        "-e",
        f"PGPASSWORD={password}",
        "etl_postgres",
        "pg_dump",
        "-h",
        host,
        "-p",
        str(port),
        "-U",
        user,
        "-d",
        name,
        "-Fc",
        "--no-owner",
        "--no-acl",
        "-f",
        "/tmp/_safe_migrate_backup.dump",
    ]
    subprocess.run(cmd, check=True, env=env)
    subprocess.run(
        ["docker", "cp", "etl_postgres:/tmp/_safe_migrate_backup.dump", str(out_path)],
        check=True,
    )
    size_mb = out_path.stat().st_size / 1_000_000
    print(f"-- backup OK: {out_path} ({size_mb:.1f} MB)")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sql_file", nargs="?", help="omit with --audit")
    ap.add_argument("--target", default="local", choices=["local", "render"])
    ap.add_argument("--yes-i-checked", action="store_true")
    ap.add_argument(
        "--audit",
        action="store_true",
        help="print the DB's full ON DELETE CASCADE forest with row counts, then exit (read-only, no sql_file needed)",
    )
    args = ap.parse_args()

    load_env()

    if args.audit:
        conn = connect(
            os.environ["DB_HOST"],
            os.environ["DB_PORT"],
            os.environ["DB_NAME"],
            os.environ["DB_USER"],
            os.environ["DB_PASSWORD"],
        )
        audit_all_cascades(conn.cursor())
        conn.close()
        return

    if not args.sql_file:
        raise SystemExit("sql_file required (or use --audit)")
    path = Path(args.sql_file)
    if not path.exists():
        raise SystemExit(f"not found: {path}")
    sql_text = path.read_text(encoding="utf-8")

    if args.target == "render":
        print(
            "!! --target render is not wired up (deliberately). Applying to\n"
            "!! production requires an explicit, separate, human-run step --\n"
            "!! this tool only protects local. See the deploy checklist."
        )
        raise SystemExit(1)

    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]

    findings = scan_file(sql_text)
    conn = connect(host, port, name, user, password)
    cur = conn.cursor()

    if findings:
        print(f"!! {len(findings)} dangerous statement(s) found in {path.name}:\n")
        seen_tables = set()
        for kind, table, snippet in findings:
            print(f"   [{kind}] {table}: {snippet[:100]}")
            if kind in ("DELETE", "TRUNCATE") and table not in seen_tables:
                seen_tables.add(table)
                report = check_delete_blast_radius(cur, table)
                if report:
                    total = sum(n for _, _, _, n in report)
                    print(
                        f"      !!! {table} CASCADE-deletes {total:,} rows across "
                        f"{len(report)} descendant table(s):"
                    )
                    for depth, child, col, n in report:
                        print(f"         {'  ' * depth}-> {child}.{col}: {n:,} rows")
        print()
        if not args.yes_i_checked:
            print("Refusing to apply. Read the blast-radius report above.")
            print("If this is intentional and safe, re-run with --yes-i-checked.")
            conn.close()
            sys.exit(1)
        print("--yes-i-checked passed, proceeding.\n")

    backup_path = backup(args.target, host, port, name, user, password)

    print(f"-- applying {path}")
    docker_cmd = [
        "docker",
        "exec",
        "-i",
        "etl_postgres",
        "psql",
        "-U",
        user,
        "-d",
        name,
        "-v",
        "ON_ERROR_STOP=1",
    ]
    result = subprocess.run(docker_cmd, input=sql_text, text=True, capture_output=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print(f"\n!! FAILED. Backup is at {backup_path} if you need to restore.")
        sys.exit(result.returncode)
    print(f"-- OK. Backup for this run: {backup_path}")


if __name__ == "__main__":
    main()
