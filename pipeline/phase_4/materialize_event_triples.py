"""Materialize event triples (actor -> action_class -> target + polarity) into mv_event_triples.

Aggregates title-level labels per event into structured triples with polarity classification.
Part of the mv_* materialization pattern.
"""

import argparse
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.ontology import get_polarity


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


TRIPLE_SQL = """
    SELECT
        e.id AS event_id,
        c.centroid_id,
        c.month,
        tl.actor,
        tl.action_class,
        MODE() WITHIN GROUP (ORDER BY tl.domain) AS domain,
        COALESCE(NULLIF(tl.target, ''), 'NONE') AS target,
        COUNT(DISTINCT tl.title_id)::int AS title_count,
        AVG(tl.importance_score)::float AS importance_avg,
        e.first_seen::date AS first_seen
    FROM events_v3 e
    JOIN ctm c ON e.ctm_id = c.id
    JOIN event_v3_titles evt ON evt.event_id = e.id
    JOIN title_labels tl ON tl.title_id = evt.title_id
    WHERE c.month = %s
      AND e.is_catchall = false
      AND tl.actor IS NOT NULL
      AND tl.action_class IS NOT NULL
    GROUP BY e.id, c.centroid_id, c.month, tl.actor, tl.action_class, target, e.first_seen
"""


def materialize(month=None, all_months=False):
    """Compute and insert event triples for given months."""
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
                cur.execute(
                    "SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') FROM ctm WHERE is_frozen = false"
                )
                months = [r[0] for r in cur.fetchall()]

            if not months:
                print("No months to process")
                return

            total = 0
            for m in months:
                count = _materialize_month(cur, m)
                total += count

            conn.commit()
            print("Done: %d triples inserted across %d months" % (total, len(months)))
    finally:
        conn.close()


def _materialize_month(cur, month_str):
    """Compute triples for all events in a single month."""
    start = time.time()
    month_date = month_str + "-01"

    # Delete existing rows for this month, then re-insert
    cur.execute("DELETE FROM mv_event_triples WHERE month = %s", (month_date,))

    cur.execute(TRIPLE_SQL, (month_date,))
    rows = cur.fetchall()

    if not rows:
        print("  %s: no data" % month_str)
        return 0

    # Add polarity from ontology
    values = []
    for r in rows:
        (
            event_id,
            centroid_id,
            month,
            actor,
            action_class,
            domain,
            target,
            title_count,
            importance_avg,
            first_seen,
        ) = r
        polarity = get_polarity(action_class)
        values.append(
            (
                event_id,
                centroid_id,
                month,
                actor,
                action_class,
                domain,
                target,
                polarity,
                title_count,
                importance_avg,
                first_seen,
            )
        )

    execute_values(
        cur,
        """INSERT INTO mv_event_triples
           (event_id, centroid_id, month, actor, action_class, domain,
            target, polarity, title_count, importance_avg, first_seen)
           VALUES %s""",
        values,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
    )

    elapsed = time.time() - start
    print("  %s: %d triples (%.1fs)" % (month_str, len(values), elapsed))
    return len(values)


def main():
    parser = argparse.ArgumentParser(description="Materialize event triples")
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
