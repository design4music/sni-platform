"""Backfill monthly centroid summaries for a target month.

Iterates all centroids, generates monthly summary (tier-aware). Shard-able
for parallelism since centroids are independent.

Usage:
    python scripts/backfill_centroid_summaries.py --month 2026-03
    python scripts/backfill_centroid_summaries.py --month 2026-03 --shard-idx 0 --shard-count 3
    python scripts/backfill_centroid_summaries.py --month 2026-03 --limit 3   # smoke test
"""

import argparse
import asyncio
import sys
import time
import traceback
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config
from pipeline.phase_5.generate_centroid_summary import generate_centroid_summary


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def month_end(ym: str) -> date:
    """Convert 'YYYY-MM' or 'YYYY-MM-DD' to the last day of that month."""
    if len(ym) == 7:
        y, m = ym.split("-")
        y, m = int(y), int(m)
    else:
        d = date.fromisoformat(ym)
        y, m = d.year, d.month
    # First day of next month minus 1
    if m == 12:
        return date(y + 1, 1, 1) - __import__("datetime").timedelta(days=1)
    return date(y, m + 1, 1) - __import__("datetime").timedelta(days=1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM or YYYY-MM-DD")
    parser.add_argument("--shard-idx", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    period_end = month_end(args.month)
    month_short = f"{period_end.year}-{period_end.month:02d}"
    print(
        f"Backfilling monthly centroid summaries for {month_short} (period_end={period_end})",
        flush=True,
    )

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT c.centroid_id, COALESCE(cv.label, c.centroid_id) AS label
             FROM ctm c
             JOIN centroids_v3 cv ON cv.id = c.centroid_id
            WHERE c.month = %s AND c.title_count > 0
            ORDER BY c.centroid_id""",
        (date(period_end.year, period_end.month, 1),),
    )
    centroids = cur.fetchall()
    conn.close()

    if args.shard_count > 1:
        centroids = [
            c for i, c in enumerate(centroids) if i % args.shard_count == args.shard_idx
        ]
        print(
            f"Shard {args.shard_idx}/{args.shard_count}: {len(centroids)} centroids",
            flush=True,
        )

    if args.limit:
        centroids = centroids[: args.limit]

    t0 = time.time()
    tier_counts = {1: 0, 2: 0, 3: 0}
    ok = fail = 0

    for idx, (centroid_id, label) in enumerate(centroids, 1):
        t = time.time()
        try:
            result = await generate_centroid_summary(
                centroid_id=centroid_id,
                period_end=period_end,
                period_kind="monthly",
                country_label=label,
            )
            tier_counts[result["tier"]] = tier_counts.get(result["tier"], 0) + 1
            ok += 1
            print(
                f"[{idx}/{len(centroids)}] OK    {centroid_id} "
                f"(tier={result['tier']}, events={result['source_event_count']}) "
                f"{time.time() - t:.1f}s",
                flush=True,
            )
        except Exception as e:
            fail += 1
            print(f"[{idx}/{len(centroids)}] FAIL  {centroid_id}: {e}", flush=True)
            traceback.print_exc()

    total = time.time() - t0
    print(
        f"\nDone: {ok} ok, {fail} fail in {total / 60:.1f} min. "
        f"Tiers: 1={tier_counts[1]} 2={tier_counts[2]} 3={tier_counts[3]}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
