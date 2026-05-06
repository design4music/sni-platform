"""Materialize per-centroid coverage stats into mv_centroid_stats.

Replaces inline SUM(events_v3.source_batch_count) aggregations that
ran on every /region/* and homepage request.

Staleness gate: skips refresh if the table was updated within
--max-age-hours (default 12). Daemon can call this freely; the
script no-ops between refreshes. Run with --force to bypass.

Computed once per refresh:
  source_count        — SUM(source_batch_count) all-time per centroid
  month_source_count  — same, restricted to CURRENT calendar month
  last_article_date   — MAX(last_active|date) per centroid

Heavy SQL runs on the daemon worker, never inside a user request.
"""

import argparse
import sys
import time
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

DEFAULT_MAX_AGE_HOURS = 12


def get_connection():
    return psycopg2.connect(
        **config.db_connect_kwargs(),
    )


def is_stale(cur, max_age_hours: float) -> bool:
    """Return True iff the table is empty or older than max_age_hours."""
    cur.execute(
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_centroid_stats"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def materialize(
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS, force: bool = False
) -> int:
    """Refresh mv_centroid_stats. Returns count of centroid rows upserted, or 0 if skipped."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_centroid_stats"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_centroid_stats refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()

            # One-shot aggregation across all active centroids. Same shape as the
            # inline CTE that used to live in lib/queries.ts, but runs once on
            # the worker instead of per-request on the web service.
            cur.execute(
                """
                INSERT INTO mv_centroid_stats
                    (centroid_id, source_count, month_source_count, last_article_date, updated_at)
                SELECT c.id,
                       COALESCE(SUM(e.source_batch_count)::int, 0)                                 AS source_count,
                       COALESCE(SUM(CASE WHEN ctm.month = date_trunc('month', CURRENT_DATE)
                                         THEN e.source_batch_count ELSE 0 END)::int, 0)           AS month_source_count,
                       MAX(COALESCE(e.last_active, e.date))                                       AS last_article_date,
                       NOW()
                  FROM centroids_v3 c
                  LEFT JOIN ctm        ON ctm.centroid_id = c.id
                  LEFT JOIN events_v3 e ON e.ctm_id = ctm.id
                 WHERE c.is_active = true
                 GROUP BY c.id
                ON CONFLICT (centroid_id) DO UPDATE
                  SET source_count       = EXCLUDED.source_count,
                      month_source_count = EXCLUDED.month_source_count,
                      last_article_date  = EXCLUDED.last_article_date,
                      updated_at         = EXCLUDED.updated_at
                """
            )
            rows = cur.rowcount
            conn.commit()
            elapsed = time.time() - start
            print("Done: %d centroid rows upserted (%.1fs)" % (rows, elapsed))
            return rows
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Materialize per-centroid coverage stats"
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=DEFAULT_MAX_AGE_HOURS,
        help="Skip if table was refreshed within this window (default: %(default)s)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the staleness gate and refresh now"
    )
    args = parser.parse_args()
    materialize(max_age_hours=args.max_age_hours, force=args.force)


if __name__ == "__main__":
    main()
