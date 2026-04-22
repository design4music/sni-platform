"""Run Phase 4 incremental clustering for all CTMs in a month, optionally sharded.

For each target CTM:
  - recluster_ctm(ctm_id) from pipeline.phase_4.incremental_clustering
  - reconcile_siblings_bulk (once per month at the end)

Sharding: launch N processes with --shard-idx 0..N-1 --shard-count N. CTMs
are distributed across shards by ctm_id hash order (deterministic).
Shards operate on disjoint CTM sets, no coordination needed.

Largest CTMs are processed first within each shard so the tail shortens
fastest.

Usage:
    # Single process
    python scripts/cluster_month.py --month 2026-02-01

    # 3-way parallel
    python scripts/cluster_month.py --month 2026-02-01 --shard-idx 0 --shard-count 3
    python scripts/cluster_month.py --month 2026-02-01 --shard-idx 1 --shard-count 3
    python scripts/cluster_month.py --month 2026-02-01 --shard-idx 2 --shard-count 3

    # Smoke test
    python scripts/cluster_month.py --month 2026-02-01 --limit 3
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config
from pipeline.phase_4.incremental_clustering import recluster_ctm
from pipeline.phase_4.reconcile_siblings_bulk import bulk_merge
from pipeline.phase_4.reconcile_siblings_v4 import (
    DEFAULT_MIN_SOURCES,
    DEFAULT_THRESHOLD,
    fetch_events,
    find_cross_centroid_groups,
)


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="Month, YYYY-MM or YYYY-MM-DD")
    parser.add_argument("--shard-idx", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None, help="Cap CTMs (test mode)")
    parser.add_argument(
        "--skip-merge",
        action="store_true",
        help="Skip Phase 3.2 sibling reconciliation",
    )
    args = parser.parse_args()

    month_start = args.month if len(args.month) > 7 else f"{args.month}-01"
    month_short = month_start[:7]

    log_dir = Path("out") / f"{month_short.replace('-', '_')}_reprocess"
    suffix = (
        f".shard{args.shard_idx}of{args.shard_count}" if args.shard_count > 1 else ""
    )
    log = make_logger(log_dir / f"cluster{suffix}.log")

    log(
        f"=== cluster_month {month_short} shard {args.shard_idx}/{args.shard_count} ==="
    )

    conn = get_conn()
    cur = conn.cursor()
    # Largest CTMs first: biggest ones dominate wall-clock, processing
    # them first means the tail shortens fastest.
    cur.execute(
        """SELECT id::text, centroid_id, track, title_count
             FROM ctm
            WHERE month = %s AND title_count > 0
            ORDER BY title_count DESC, centroid_id""",
        (month_start,),
    )
    all_ctms = cur.fetchall()
    conn.close()

    # Shard-partition: deterministic by position
    if args.shard_count > 1:
        ctms = [
            c for i, c in enumerate(all_ctms) if i % args.shard_count == args.shard_idx
        ]
        log(
            f"Shard {args.shard_idx}/{args.shard_count}: {len(ctms)} CTMs (of {len(all_ctms)})"
        )
    else:
        ctms = all_ctms

    if args.limit:
        ctms = ctms[: args.limit]

    done = fail = 0
    t0 = time.time()

    for idx, (ctm_id, centroid, track, tcount) in enumerate(ctms, 1):
        label = f"{centroid}/{track}"
        t = time.time()
        log(f"[{idx}/{len(ctms)}] START {label} (titles={tcount})")
        try:
            # Clustering (wipes ctm's events, rebuilds)
            recluster_ctm(ctm_id, dry_run=False)
            log(f"[{idx}/{len(ctms)}] DONE  {label} in {time.time() - t:.0f}s")
            done += 1
        except Exception as e:
            fail += 1
            log(f"[{idx}/{len(ctms)}] FAIL  {label}: {e}")

    # One-shot sibling reconciliation for the whole month after all CTMs rebuilt.
    if not args.skip_merge and done > 0:
        log(f"=== Phase 3.2: sibling reconciliation for {month_short} ===")
        conn = get_conn()
        try:
            events = fetch_events(
                conn,
                month_short,
                min_sources=DEFAULT_MIN_SOURCES,
                promoted_only=False,
            )
            groups = find_cross_centroid_groups(events, threshold=DEFAULT_THRESHOLD)
            if groups:
                merged = bulk_merge(conn, groups, month_short)
                log(f"reconcile: {len(groups)} groups, {merged} events merged")
            else:
                log("reconcile: nothing to merge")
        except Exception as e:
            log(f"reconcile FAIL: {e}")
            log(traceback.format_exc())
        finally:
            conn.close()

    log(
        f"\nTotal: {done} succeeded, {fail} failed in {(time.time() - t0) / 60:.1f} min"
    )


if __name__ == "__main__":
    main()
