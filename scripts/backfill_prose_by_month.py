"""Backfill LLM prose + daily briefs for a past (frozen) month.

Reuses the exact functions the daemon calls (same prompts, concurrency,
DE batching, and "needs-work" filter). Ignores is_frozen so archived
months can be brought inline with the new architecture.

Usage:
    python scripts/backfill_prose_by_month.py --month 2026-03-01
    python scripts/backfill_prose_by_month.py --month 2026-03-01 --only prose
    python scripts/backfill_prose_by_month.py --month 2026-03-01 --only briefs
    python scripts/backfill_prose_by_month.py --month 2026-03-01 --limit 3

Prose pass: calls describe_promoted_events(ctm_id) -- skips events that
already have title_de set.
Briefs pass: calls phase45d_brief(ctm_id) -- generates missing daily
briefs for dates with >= DAILY_BRIEF_MIN_CLUSTERS promoted clusters.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg2

from core.config import config
from pipeline.phase_4.generate_daily_brief_4_5d import process_ctm as phase45d_brief
from pipeline.phase_4.promote_and_describe_4_5a import (
    describe_promoted_events as phase45a_describe,
)


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def ctms_needing_prose(conn, month: str) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT c.id::text, c.centroid_id, c.track, c.title_count
                 FROM ctm c
                WHERE c.month = %s
                  AND EXISTS (SELECT 1 FROM events_v3 e
                               WHERE e.ctm_id = c.id
                                 AND e.is_promoted = true
                                 AND e.title_de IS NULL)
                ORDER BY c.title_count ASC""",
            (month,),
        )
        return cur.fetchall()


def ctms_needing_briefs(conn, month: str) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT c.id::text, c.centroid_id, c.track, c.title_count
                 FROM ctm c
                WHERE c.month = %s
                  AND EXISTS (SELECT 1 FROM events_v3 e
                               WHERE e.ctm_id = c.id AND e.is_promoted = true)
                  AND EXISTS (
                    SELECT 1 FROM (
                      SELECT e.date, COUNT(*) AS n
                        FROM events_v3 e
                       WHERE e.ctm_id = c.id AND e.is_promoted = true
                       GROUP BY e.date
                      HAVING COUNT(*) > 5
                    ) q
                    WHERE NOT EXISTS (
                      SELECT 1 FROM daily_briefs db
                       WHERE db.ctm_id = c.id AND db.date = q.date
                    )
                  )
                ORDER BY c.title_count ASC""",
            (month,),
        )
        return cur.fetchall()


def run_prose_pass(month: str, limit: int | None):
    conn = get_conn()
    try:
        ctms = ctms_needing_prose(conn, month)
    finally:
        conn.close()
    if limit:
        ctms = ctms[:limit]

    if not ctms:
        print("[prose] no CTMs need prose for %s" % month)
        return

    print("[prose] %d CTMs need prose for %s" % (len(ctms), month))
    t0 = time.time()
    ok = fail = 0
    for idx, (ctm_id, centroid, track, tc) in enumerate(ctms, 1):
        t = time.time()
        try:
            stats = asyncio.run(phase45a_describe(ctm_id))
            print(
                "[prose %d/%d] OK    %s/%s (titles=%d) %s  %.1fs"
                % (idx, len(ctms), centroid, track, tc, stats, time.time() - t)
            )
            ok += 1
        except Exception as e:
            print(
                "[prose %d/%d] FAIL  %s/%s: %s" % (idx, len(ctms), centroid, track, e)
            )
            fail += 1
    print(
        "[prose] done: %d ok, %d fail in %.1f min" % (ok, fail, (time.time() - t0) / 60)
    )


def run_briefs_pass(month: str, limit: int | None):
    conn = get_conn()
    try:
        ctms = ctms_needing_briefs(conn, month)
    finally:
        conn.close()
    if limit:
        ctms = ctms[:limit]

    if not ctms:
        print("[briefs] no CTMs need daily briefs for %s" % month)
        return

    print("[briefs] %d CTMs need daily briefs for %s" % (len(ctms), month))
    t0 = time.time()
    ok = fail = 0
    for idx, (ctm_id, centroid, track, tc) in enumerate(ctms, 1):
        t = time.time()
        try:
            stats = asyncio.run(phase45d_brief(ctm_id))
            print(
                "[briefs %d/%d] OK    %s/%s (titles=%d) %s  %.1fs"
                % (idx, len(ctms), centroid, track, tc, stats, time.time() - t)
            )
            ok += 1
        except Exception as e:
            print(
                "[briefs %d/%d] FAIL  %s/%s: %s" % (idx, len(ctms), centroid, track, e)
            )
            fail += 1
    print(
        "[briefs] done: %d ok, %d fail in %.1f min"
        % (ok, fail, (time.time() - t0) / 60)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="Month start, e.g. 2026-03-01")
    parser.add_argument(
        "--only",
        choices=["prose", "briefs"],
        default=None,
        help="Run only one pass (default: both, in order prose then briefs)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Cap CTMs per pass")
    args = parser.parse_args()

    if args.only != "briefs":
        run_prose_pass(args.month, args.limit)
    if args.only != "prose":
        run_briefs_pass(args.month, args.limit)


if __name__ == "__main__":
    main()
