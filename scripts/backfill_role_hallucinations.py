"""Retroactively apply fix_role_hallucinations to past LLM-generated prose.

Usage:
    python scripts/backfill_role_hallucinations.py --db local --dry-run
    python scripts/backfill_role_hallucinations.py --db local
    python scripts/backfill_role_hallucinations.py --db render --dry-run
    python scripts/backfill_role_hallucinations.py --db render

Safety:
    - Dry-run is the default interaction; always run with --dry-run first
      to see counts and sample changes.
    - Writes a rollback CSV to out/role_backfill_<db>_<table>.csv with
      (id, field, before, after) for every changed row, so reversing is
      a CSV-to-UPDATE replay if needed.
    - Updates in batches of 500 rows per field; commits per batch.
    - Idempotent — running twice is a no-op on the second pass (regex
      replacement converges).
"""

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2
from psycopg2.extras import execute_batch

from core.config import config
from core.llm_utils import fix_role_hallucinations, fix_title_with_context

LOCAL_DSN = dict(
    host=config.db_host,
    port=config.db_port,
    database=config.db_name,
    user=config.db_user,
    password=config.db_password,
)
RENDER_DSN = os.environ.get("RENDER_DATABASE_URL") or (
    "postgresql://maxgenrih55:DGiBGNv89pGtRsaj5Ys2fCN4DFMEmCUb"
    "@dpg-d5uem563jp1c739ufrsg-a.frankfurt-postgres.render.com/sni_v2"
)


def _locale_for(col):
    """Infer locale from column name suffix."""
    return "de" if col.endswith("_de") else "en"


# (table, pk_column, text_columns, context_fix_pairs)
# context_fix_pairs: [(title_col, summary_col)] — pairs where we apply
# fix_title_with_context (title gets fixed if summary anchors the subject).
TARGETS = [
    (
        "events_v3",
        "id",
        ["title", "title_de", "summary", "summary_de"],
        [("title", "summary"), ("title_de", "summary_de")],
    ),
    ("daily_briefs", None, ["brief_en", "brief_de"], []),
    ("ctm", "id", ["summary_text", "summary_text_de"], []),
    (
        "narratives",
        "id",
        ["label", "label_de", "description", "description_de"],
        [("label", "description"), ("label_de", "description_de")],
    ),
    ("meta_narratives", "id", ["description", "description_de"], []),
    (
        "epics",
        "id",
        ["title", "title_de", "summary", "summary_de"],
        [("title", "summary"), ("title_de", "summary_de")],
    ),
    ("centroid_summaries", "id", ["overall_en", "overall_de"], []),
]

BATCH_SIZE = 500


def connect(db):
    if db == "local":
        return psycopg2.connect(**LOCAL_DSN, connect_timeout=30)
    if db == "render":
        return psycopg2.connect(RENDER_DSN, connect_timeout=30)
    raise ValueError("unknown db: %s" % db)


def process_table(conn, table, pk, columns, context_pairs, dry_run, changes_out):
    """Return dict of {column_name: change_count}."""
    counts = {c: 0 for c in columns}

    # daily_briefs has composite PK (ctm_id, date). Handle inline.
    if table == "daily_briefs":
        select = "SELECT ctm_id::text, date::text, %s FROM daily_briefs" % (
            ", ".join(columns)
        )
    else:
        select = "SELECT %s::text, %s FROM %s" % (pk, ", ".join(columns), table)

    context_map = dict(context_pairs)

    with conn.cursor(name="backfill_%s" % table) as cur:
        cur.itersize = 2000
        cur.execute(select)
        pending = []
        total_seen = 0
        for row in cur:
            total_seen += 1
            if table == "daily_briefs":
                ctm_id, date, *values = row
                key = (ctm_id, date)
            else:
                row_id, *values = row
                key = (row_id,)

            col_index = {c: i for i, c in enumerate(columns)}
            new_values = list(values)
            row_changed = False
            for col, val in zip(columns, values):
                if val is None:
                    continue
                loc = _locale_for(col)
                fixed = fix_role_hallucinations(val, locale=loc)
                # If this column has a summary partner, also apply the
                # context-aware title fix (headline drops the name but
                # summary anchors it).
                summary_col = context_map.get(col)
                if summary_col is not None:
                    summary_val = values[col_index[summary_col]]
                    if summary_val:
                        fixed = fix_title_with_context(fixed, summary_val, locale=loc)
                if fixed != val:
                    counts[col] += 1
                    row_changed = True
                    changes_out.append(
                        {
                            "table": table,
                            "key": "|".join(key),
                            "column": col,
                            "before": val,
                            "after": fixed,
                        }
                    )
                new_values[col_index[col]] = fixed

            if row_changed:
                pending.append((key, new_values))

        print("  scanned %d rows, %d with changes" % (total_seen, len(pending)))

    if dry_run or not pending:
        return counts

    # Apply updates in batches
    print("  applying %d row updates in batches of %d..." % (len(pending), BATCH_SIZE))
    with conn.cursor() as ucur:
        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i : i + BATCH_SIZE]
            if table == "daily_briefs":
                stmt = (
                    "UPDATE daily_briefs SET "
                    + ", ".join("%s = %%s" % c for c in columns)
                    + " WHERE ctm_id = %s AND date = %s"
                )
                params = [tuple(vals) + key for key, vals in batch]
            else:
                stmt = (
                    "UPDATE %s SET " % table
                    + ", ".join("%s = %%s" % c for c in columns)
                    + " WHERE %s = %%s" % pk
                )
                params = [tuple(vals) + key for key, vals in batch]
            execute_batch(ucur, stmt, params)
            conn.commit()
            print(
                "    committed batch %d/%d"
                % (i // BATCH_SIZE + 1, (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE)
            )

    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, choices=["local", "render"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("Connecting to %s..." % args.db)
    conn = connect(args.db)

    all_changes = []
    grand_counts = {}
    for table, pk, cols, context_pairs in TARGETS:
        print("\n== %s ==" % table)
        counts = process_table(
            conn, table, pk, cols, context_pairs, args.dry_run, all_changes
        )
        for col, n in counts.items():
            grand_counts["%s.%s" % (table, col)] = n

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / (
        "role_backfill_%s%s.csv" % (args.db, "_dryrun" if args.dry_run else "")
    )
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["table", "key", "column", "before", "after"])
        w.writeheader()
        for ch in all_changes:
            w.writerow(ch)
    print("\nChange log: %s" % csv_path)

    print(
        "\n== SUMMARY (%s %s) ==" % (args.db, "DRY-RUN" if args.dry_run else "APPLIED")
    )
    total = 0
    for key in sorted(grand_counts):
        n = grand_counts[key]
        total += n
        if n > 0:
            print("  %-50s %6d" % (key, n))
    print("  %-50s %6d" % ("TOTAL", total))

    conn.close()


if __name__ == "__main__":
    main()
