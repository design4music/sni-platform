"""Materialize top signals per centroid into mv_centroid_signals table.

Replaces the expensive 5-parallel-query LATERAL unnest in the frontend
with a simple PK lookup on pre-computed JSONB.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

SIGNAL_COLUMNS = ["persons", "orgs", "places", "commodities", "policies"]
TOP_N = 5  # top signals overall per centroid+month


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def _build_union_sql():
    """Build UNION ALL query across all signal columns for all centroids in a month."""
    parts = []
    for col in SIGNAL_COLUMNS:
        parts.append(
            f"""SELECT c.centroid_id, '{col}' AS signal_type, val AS value,
                       COUNT(DISTINCT e.id)::int AS event_count
                FROM events_v3 e
                JOIN ctm c ON e.ctm_id = c.id
                JOIN event_v3_titles evt ON evt.event_id = e.id
                JOIN title_labels tl ON tl.title_id = evt.title_id
                CROSS JOIN LATERAL unnest(tl.{col}) AS val
                WHERE c.month = %s AND e.is_catchall = false
                GROUP BY c.centroid_id, val"""
        )
    return " UNION ALL ".join(parts)


def materialize(month=None, all_months=False):
    """Compute and upsert top signals for centroids.

    Args:
        month: specific month string like '2026-02'. None = current unfrozen months.
        all_months: if True, process every distinct month in the ctm table.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if all_months:
                cur.execute(
                    "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') FROM ctm ORDER BY 1"
                )
                months = [r[0] for r in cur.fetchall()]
            elif month:
                months = [month]
            else:
                # Current unfrozen months
                cur.execute(
                    "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') FROM ctm WHERE is_frozen = false"
                )
                months = [r[0] for r in cur.fetchall()]

            if not months:
                print("No months to process")
                return

            total_upserted = 0
            for m in months:
                count = _materialize_month(cur, m)
                total_upserted += count

            conn.commit()
            print("Done: %d centroid-months upserted" % total_upserted)
    finally:
        conn.close()


def _materialize_month(cur, month_str):
    """Compute top signals for all centroids in a single month."""
    start = time.time()
    month_date = month_str + "-01"

    union_sql = _build_union_sql()
    # Rank signals per centroid, take top N overall
    sql = f"""
        WITH raw AS ({union_sql})
        SELECT centroid_id,
               json_agg(
                 json_build_object(
                   'signal_type', signal_type,
                   'value', value,
                   'event_count', event_count
                 ) ORDER BY event_count DESC
               ) FILTER (WHERE rn <= {TOP_N}) AS signals
        FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY centroid_id ORDER BY event_count DESC
            ) AS rn
            FROM raw
        ) ranked
        GROUP BY centroid_id
    """
    # Each part of the union needs the month parameter
    params = tuple([month_date] * len(SIGNAL_COLUMNS))
    cur.execute(sql, params)
    rows = cur.fetchall()

    if not rows:
        print("  %s: no data" % month_str)
        return 0

    # Upsert
    execute_values(
        cur,
        """INSERT INTO mv_centroid_signals (centroid_id, month, signals, updated_at)
           VALUES %s
           ON CONFLICT (centroid_id, month) DO UPDATE
           SET signals = EXCLUDED.signals, updated_at = NOW()""",
        [(r[0], month_date, json.dumps(r[1])) for r in rows],
        template="(%s, %s::date, %s::jsonb, NOW())",
    )
    elapsed = time.time() - start
    print("  %s: %d centroids (%.1fs)" % (month_str, len(rows), elapsed))
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Materialize top signals per centroid")
    parser.add_argument("--month", help="Specific month (YYYY-MM)")
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_months",
        help="Recompute all months (backfill)",
    )
    args = parser.parse_args()
    materialize(month=args.month, all_months=args.all_months)


if __name__ == "__main__":
    main()
