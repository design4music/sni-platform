"""Run Phase 4.5d daily briefs for all CTMs in a month, optionally sharded.

Per CTM: phase45d_brief(ctm_id) generates one LLM brief per qualifying day
(>=5 promoted clusters on that day). Ignores is_frozen.

Sharding: launch N processes with --shard-idx 0..N-1 --shard-count N.
CTMs distributed across shards; largest-first within each shard.

Usage:
    # Single process
    python scripts/briefs_month.py --month 2026-02-01

    # 3-way parallel
    python scripts/briefs_month.py --month 2026-02-01 --shard-idx 0 --shard-count 3
    python scripts/briefs_month.py --month 2026-02-01 --shard-idx 1 --shard-count 3
    python scripts/briefs_month.py --month 2026-02-01 --shard-idx 2 --shard-count 3
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
from pipeline.phase_4.generate_daily_brief_4_5d import process_ctm as phase45d_brief


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
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    month_start = args.month if len(args.month) > 7 else f"{args.month}-01"
    month_short = month_start[:7]

    log_dir = Path("out") / f"{month_short.replace('-', '_')}_reprocess"
    suffix = (
        f".shard{args.shard_idx}of{args.shard_count}" if args.shard_count > 1 else ""
    )
    log = make_logger(log_dir / f"briefs{suffix}.log")

    log(f"=== briefs_month {month_short} shard {args.shard_idx}/{args.shard_count} ===")

    # Only CTMs that could have qualifying brief days (>=5 promoted on any date)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT c.id::text, c.centroid_id, c.track, c.title_count
             FROM ctm c
            WHERE c.month = %s
              AND EXISTS (
                SELECT 1 FROM (
                  SELECT date, COUNT(*) AS n FROM events_v3
                   WHERE ctm_id = c.id AND is_promoted = true
                   GROUP BY date HAVING COUNT(*) > 5
                ) q
              )
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
            stats = asyncio.run(phase45d_brief(ctm_id))
            log(
                f"[{idx}/{len(ctms)}] DONE  {label} in {time.time() - t:.0f}s "
                f"qualifying={stats.get('qualifying', 0)} written={stats.get('written', 0)}"
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
