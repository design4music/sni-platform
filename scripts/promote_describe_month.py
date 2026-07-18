"""Run Phase 4.5a (promote + LLM prose EN+DE) for all CTMs in a month,
optionally sharded.

Per CTM:
  - promote_top_clusters: marks top-N unpromoted events per day (mechanical)
  - describe_promoted_events: LLM prose for promoted events that lack title_de
    (same prompts/concurrency/DE batching as the live daemon)

Sharding: launch N processes with --shard-idx 0..N-1 --shard-count N. CTMs
are distributed across shards; largest-first within each shard. Each shard's
describe_promoted_events uses LLM_CONCURRENCY=6 internally, so total
concurrent LLM calls = N * 6.

Usage:
    # Single process
    python scripts/promote_describe_month.py --month 2026-02-01

    # 3-way parallel (18 concurrent LLM calls)
    python scripts/promote_describe_month.py --month 2026-02-01 --shard-idx 0 --shard-count 3
    python scripts/promote_describe_month.py --month 2026-02-01 --shard-idx 1 --shard-count 3
    python scripts/promote_describe_month.py --month 2026-02-01 --shard-idx 2 --shard-count 3

    # Smoke test
    python scripts/promote_describe_month.py --month 2026-02-01 --limit 3
"""

import argparse
import asyncio
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config
from pipeline.phase_4.promote_and_describe_4_5a import process_ctm as phase45a_process


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
    args = parser.parse_args()

    month_start = args.month if len(args.month) > 7 else f"{args.month}-01"
    month_short = month_start[:7]

    log_dir = Path("out") / f"{month_short.replace('-', '_')}_reprocess"
    suffix = (
        f".shard{args.shard_idx}of{args.shard_count}" if args.shard_count > 1 else ""
    )
    log = make_logger(log_dir / f"promote_describe{suffix}.log")

    log(
        f"=== promote_describe_month {month_short} shard {args.shard_idx}/{args.shard_count} ==="
    )

    # Select CTMs that have events; largest first
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT c.id::text, c.centroid_id, c.track, c.title_count
             FROM ctm c
            WHERE c.month = %s
              AND EXISTS (SELECT 1 FROM events_v3 WHERE ctm_id = c.id)
            ORDER BY c.title_count DESC, c.centroid_id""",
        (month_start,),
    )
    all_ctms = cur.fetchall()
    conn.close()

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
            stats = asyncio.run(phase45a_process(ctm_id))
            log(
                f"[{idx}/{len(ctms)}] DONE  {label} in {time.time() - t:.0f}s "
                f"promoted={stats.get('promoted', 0)} written={stats.get('written', 0)}"
            )
            done += 1
        except Exception as e:
            fail += 1
            log(f"[{idx}/{len(ctms)}] FAIL  {label}: {e}")
            log(traceback.format_exc())

    log(
        f"\nTotal: {done} succeeded, {fail} failed in {(time.time() - t0) / 60:.1f} min"
    )


if __name__ == "__main__":
    main()
