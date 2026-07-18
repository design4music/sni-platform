"""Finish v3.0.1 labeling for all titles of a given month.

Finds every title assigned to a CTM in the target month that lacks an
ELO_v3.0.1 label, wipes any stale v2 label rows for it, then runs Phase 3.1
with configurable concurrency and sharding.

Sharding: launch N processes with --shard-idx 0..N-1 --shard-count N. Each
process owns a disjoint slice of the title id list, so no coordination is
needed. Pre/post dedup runs only on shard 0 (SQL is idempotent either way).

Usage:
    # Single process
    python scripts/finish_month_labels.py --month 2026-01-01 --concurrency 10

    # 3-way parallel (launch 3 processes)
    python scripts/finish_month_labels.py --month 2026-01-01 --shard-idx 0 --shard-count 3 --concurrency 10
    python scripts/finish_month_labels.py --month 2026-01-01 --shard-idx 1 --shard-count 3 --concurrency 10
    python scripts/finish_month_labels.py --month 2026-01-01 --shard-idx 2 --shard-count 3 --concurrency 10

    # Smoke test
    python scripts/finish_month_labels.py --month 2026-01-01 --limit 100
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config
from pipeline.phase_3_1.extract_labels import process_titles


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def make_logger(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(msg):
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {msg}"
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")

    return log


def find_titles_needing_v3(conn, month_start: str) -> list[str]:
    """Month titles (via title_assignments) that don't have any ELO_v3.0.1 label."""
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT t.id::text
             FROM titles_v3 t
             JOIN title_assignments ta ON ta.title_id = t.id
             JOIN ctm c ON c.id = ta.ctm_id
            WHERE c.month = %s
              AND NOT EXISTS (
                SELECT 1 FROM title_labels tl
                 WHERE tl.title_id = t.id AND tl.label_version = 'ELO_v3.0.1'
              )""",
        (month_start,),
    )
    return [r[0] for r in cur.fetchall()]


def wipe_labels_for(conn, title_ids: list[str]) -> int:
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM title_labels WHERE title_id = ANY(%s::uuid[])",
        (title_ids,),
    )
    n = cur.rowcount
    conn.commit()
    return n


def dedup_labels(conn, month_start: str) -> int:
    """Keep one title_labels row per title (prefer ELO_v3.0.1, then newest)."""
    cur = conn.cursor()
    cur.execute(
        """WITH month_titles AS (
             SELECT DISTINCT t.id
               FROM titles_v3 t
               JOIN title_assignments ta ON ta.title_id = t.id
               JOIN ctm c ON c.id = ta.ctm_id
              WHERE c.month = %s
           ),
           ranked AS (
             SELECT tl.ctid,
                    ROW_NUMBER() OVER (
                      PARTITION BY tl.title_id
                      ORDER BY CASE WHEN tl.label_version='ELO_v3.0.1' THEN 0 ELSE 1 END,
                               tl.created_at DESC NULLS LAST
                    ) AS rnk
               FROM title_labels tl
               JOIN month_titles mt ON mt.id = tl.title_id
           )
           DELETE FROM title_labels
            WHERE ctid IN (SELECT ctid FROM ranked WHERE rnk > 1)""",
        (month_start,),
    )
    n = cur.rowcount
    conn.commit()
    return n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="Month, YYYY-MM or YYYY-MM-DD")
    parser.add_argument(
        "--batch", type=int, default=500, help="Titles per Phase 3.1 driver call"
    )
    parser.add_argument(
        "--concurrency", type=int, default=5, help="LLM concurrency per call"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Cap total titles (test mode)"
    )
    parser.add_argument("--shard-idx", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()

    month_start = args.month if len(args.month) > 7 else f"{args.month}-01"
    month_short = month_start[:7]

    log_dir = Path("out") / f"{month_short.replace('-', '_')}_reprocess"
    if args.shard_count > 1:
        log_path = (
            log_dir / f"label_finish.shard{args.shard_idx}of{args.shard_count}.log"
        )
    else:
        log_path = log_dir / "label_finish.log"
    log = make_logger(log_path)

    log(
        f"=== finish_month_labels {month_short} shard {args.shard_idx}/{args.shard_count} ==="
    )

    conn = get_conn()

    # Pre-dedup on shard 0 only (idempotent at SQL level; skip on others)
    if args.shard_idx == 0:
        log("Pre-dedup title_labels...")
        dedup_count = dedup_labels(conn, month_start)
        log(f"  collapsed {dedup_count} duplicate rows")

    ids = find_titles_needing_v3(conn, month_start)
    total = len(ids)

    if args.shard_count > 1:
        ids = ids[args.shard_idx :: args.shard_count]
        log(
            f"Shard {args.shard_idx}/{args.shard_count}: {len(ids)} titles (of {total} total)"
        )

    if args.limit:
        ids = ids[: args.limit]

    log(f"Titles needing v3.0.1 labels: {total} (processing {len(ids)})")

    if not ids:
        log("Nothing to do.")
        return

    wiped = wipe_labels_for(conn, ids)
    log(f"Wiped {wiped} existing label rows for {len(ids)} titles")
    conn.close()

    t_start = time.time()
    processed = 0
    for i in range(0, len(ids), args.batch):
        chunk = ids[i : i + args.batch]
        t = time.time()
        log(f"[{i}/{len(ids)}] Phase 3.1 chunk of {len(chunk)} titles...")
        try:
            result = process_titles(
                max_titles=len(chunk),
                batch_size=25,
                concurrency=args.concurrency,
                title_ids_filter=chunk,
            )
            processed += result.get("processed", len(chunk))
            log(
                f"  done in {time.time() - t:.0f}s "
                f"(success={result.get('successful', '?')} failed={result.get('failed', '?')})"
            )
        except Exception as e:
            log(f"  chunk failed: {e}")

    # Post-run dedup on shard 0 only
    if args.shard_idx == 0:
        conn = get_conn()
        log("Post-run dedup (shard 0 only)...")
        final_dedup = dedup_labels(conn, month_start)
        log(f"  collapsed {final_dedup} rows")

    log(
        f"\nDone. Processed {processed}/{len(ids)} titles in {(time.time() - t_start) / 60:.1f} min"
    )


if __name__ == "__main__":
    main()
