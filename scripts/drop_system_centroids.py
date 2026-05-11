"""Drop the 10 system (SYS-*) centroids.

They're is_active=False and have zero downstream references (no CTMs,
assignments, events, summaries, narratives) but Phase 2 still matches
them against every ingested title (55 taxonomy aliases) and writes
dead-end entries into titles_v3.centroid_ids.

Three-step cleanup:
  1) DELETE taxonomy_v3 rows for SYS-*   (stops future matching)
  2) UPDATE titles_v3 in batches to strip SYS-* from centroid_ids[]
  3) DELETE centroids_v3 rows where class='systemic'

Safety:
  - --dry-run prints affected row counts without writing
  - Step 2 runs in configurable batches (default 2000) with a per-batch
    commit, safe to interrupt and resume
  - Each step is idempotent (re-running matches nothing after first run)

Usage:
    python scripts/drop_system_centroids.py --dry-run
    python scripts/drop_system_centroids.py --execute
    python scripts/drop_system_centroids.py --execute --batch-size 2000
"""

import argparse
import sys
import time
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import config  # noqa: E402

SYS_IDS = [
    "SYS-CLIMATE",
    "SYS-DIPLOMACY",
    "SYS-ENERGY",
    "SYS-FINANCE",
    "SYS-HEALTH",
    "SYS-HUMANITARIAN",
    "SYS-MEDIA",
    "SYS-MILITARY",
    "SYS-TECH",
    "SYS-TRADE",
]


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def show_affected(conn):
    """Dry-run: count rows each step would touch."""
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM taxonomy_v3 WHERE taxonomy_function = 'centroid_anchor' AND centroid_id = ANY(%s)",
        (SYS_IDS,),
    )
    tax = cur.fetchone()[0]
    print(f"Step 1: DELETE from taxonomy_v3: {tax} rows")

    cur.execute(
        "SELECT COUNT(*) FROM titles_v3 WHERE centroid_ids && %s::text[]", (SYS_IDS,)
    )
    titles = cur.fetchone()[0]
    print(f"Step 2: UPDATE titles_v3 (strip SYS-* from centroid_ids[]): {titles} rows")

    cur.execute("SELECT COUNT(*) FROM centroids_v3 WHERE id = ANY(%s)", (SYS_IDS,))
    cent = cur.fetchone()[0]
    print(f"Step 3: DELETE from centroids_v3: {cent} rows")

    print()
    print("--- reference-integrity check (should all be zero) ---")
    for table, col in [
        ("title_assignments", "centroid_id"),
        ("ctm", "centroid_id"),
        ("strategic_narratives", "actor_centroid"),
        ("centroid_summaries", "centroid_id"),
    ]:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = ANY(%s)", (SYS_IDS,))
        print(f"  {table}.{col}: {cur.fetchone()[0]}")

    cur.close()


def delete_taxonomy(conn):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM taxonomy_v3 WHERE taxonomy_function = 'centroid_anchor' AND centroid_id = ANY(%s)",
            (SYS_IDS,),
        )
        n = cur.rowcount
    conn.commit()
    print(f"[Step 1] DELETE taxonomy_v3: {n} rows committed")
    return n


def strip_centroid_ids(conn, batch_size):
    """Batched UPDATE on titles_v3. Removes SYS-* from centroid_ids array."""
    total = 0
    batch_num = 0
    # Pre-count so we can show progress
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM titles_v3 WHERE centroid_ids && %s::text[]",
            (SYS_IDS,),
        )
        target = cur.fetchone()[0]
    print(f"[Step 2] target: {target} rows, batch_size={batch_size}")

    while True:
        batch_num += 1
        t0 = time.time()
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE titles_v3
                      SET centroid_ids = ARRAY(
                            SELECT unnest(centroid_ids)
                            EXCEPT SELECT unnest(%s::text[])
                          )
                    WHERE id IN (
                      SELECT id FROM titles_v3
                       WHERE centroid_ids && %s::text[]
                       LIMIT %s
                    )""",
                (SYS_IDS, SYS_IDS, batch_size),
            )
            n = cur.rowcount
        conn.commit()
        total += n
        dt = time.time() - t0
        print(
            f"  batch {batch_num}: {n} rows in {dt:.1f}s (total {total}/{target})",
            flush=True,
        )
        if n < batch_size:
            break
    print(f"[Step 2] UPDATE titles_v3: {total} rows stripped")
    return total


def delete_centroids(conn):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM centroids_v3 WHERE id = ANY(%s) AND class = 'systemic'",
            (SYS_IDS,),
        )
        n = cur.rowcount
    conn.commit()
    print(f"[Step 3] DELETE centroids_v3: {n} rows committed")
    return n


def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dry-run", action="store_true")
    grp.add_argument("--execute", action="store_true")
    ap.add_argument("--batch-size", type=int, default=2000)
    ap.add_argument(
        "--step",
        choices=["all", "1", "2", "3"],
        default="all",
        help="Run a single step (useful for resume). Default: all",
    )
    args = ap.parse_args()

    conn = get_conn()
    try:
        if args.dry_run:
            show_affected(conn)
            return

        if args.step in ("all", "1"):
            delete_taxonomy(conn)
        if args.step in ("all", "2"):
            strip_centroid_ids(conn, args.batch_size)
        if args.step in ("all", "3"):
            delete_centroids(conn)

        print()
        print("Post-cleanup verification:")
        show_affected(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
