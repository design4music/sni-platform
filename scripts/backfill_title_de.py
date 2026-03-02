"""Backfill title_de for existing events that have an English title but no German title.

Usage:
  python scripts/backfill_title_de.py                    # All events, newest first
  python scripts/backfill_title_de.py --limit 500        # Only 500 events
  python scripts/backfill_title_de.py --min-sources 5    # Only events with 5+ sources
  python scripts/backfill_title_de.py --days 7           # Only last 7 days
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config
from pipeline.phase_4.generate_event_summaries_4_5a import translate_title_de

BATCH_SIZE = 50
CONCURRENCY = 5


async def backfill(
    limit: int | None = None, min_sources: int = 0, days: int | None = None
):
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    where = "WHERE title IS NOT NULL AND title_de IS NULL"
    params: list = []
    if min_sources > 0:
        where += " AND source_batch_count >= %s"
        params.append(min_sources)
    if days:
        where += " AND date >= NOW() - INTERVAL '%s days'" % days

    sql = "SELECT id, title FROM events_v3 %s ORDER BY date DESC NULLS LAST" % where
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    total = len(rows)
    print("Found %d events needing title_de" % total)
    if total == 0:
        conn.close()
        return

    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0
    errors = 0

    async def translate_one(event_id, title):
        nonlocal done, errors
        async with sem:
            title_de = await translate_title_de(title)
            if title_de:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE events_v3 SET title_de = %s WHERE id = %s",
                        (title_de, event_id),
                    )
                conn.commit()
                done += 1
            else:
                errors += 1

            if (done + errors) % 50 == 0:
                print("  Progress: %d/%d (errors: %d)" % (done + errors, total, errors))

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        tasks = [translate_one(eid, t) for eid, t in batch]
        await asyncio.gather(*tasks)

    conn.close()
    print("Done. Translated: %d, Errors: %d" % (done, errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill title_de for events")
    parser.add_argument(
        "--limit", type=int, default=None, help="Max events to translate"
    )
    parser.add_argument(
        "--min-sources", type=int, default=0, help="Min source_batch_count filter"
    )
    parser.add_argument(
        "--days", type=int, default=None, help="Only events from last N days"
    )
    args = parser.parse_args()
    asyncio.run(backfill(args.limit, args.min_sources, args.days))
