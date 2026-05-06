"""Materialize per-(type) and per-(type, value) signal blobs into
mv_signal_category and mv_signal_detail.

Backs /signals, /signals/[type], and /signals/[type]/[value]. Replaces
4 expensive live queries:
  - getSignalHeatmap         (top signals across all 7 types + sparklines)
  - getSignalCategoryDetail  (top 25 per type + sparklines + contexts)
  - getSignalStats           (per-value: total, weekly, geo, tracks)
  - getRelationshipClusters  (per-value: 5-stage CTE — by far the heaviest)

Two phases per run:
  1. Materialize 7 category rows (top 25 per type with sparklines + contexts)
  2. Read top 25 from each category, materialize ~175 detail rows

Long-tail signal values (anything not in any category's top 25) are NOT
materialized — the frontend helper falls back to the live query for them.
This keeps the row count bounded while covering ~95%+ of actual traffic.

Period is currently fixed to 'rolling' (the only thing the page exposes).
The schema reserves the column for future per-month variants.

Refresh 12h, no frozen-skip — rolling 30d window.
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

DEFAULT_MAX_AGE_HOURS = 12
PERIOD = "rolling"
# commodities, policies, systems were retired from extraction (always written
# as empty arrays — see pipeline/phase_3_1/extract_labels.py:255-258). Dropped
# from this materializer 2026-05-04 to skip the dead types.
SIGNAL_TYPES = (
    "persons",
    "orgs",
    "places",
    "named_events",
)
TOP_PER_TYPE = 25
DATE_CLAUSE = "e.date >= CURRENT_DATE - INTERVAL '30 days'"

# Reused unnest fragment for relationship clusters — mirrors the TS
# UNNEST_ALL_SIGNALS constant.
UNNEST_ALL_SIGNALS = " UNION ALL ".join(
    f"SELECT '{col}'::text as sig_type, unnest(COALESCE(tl.{col}, '{{}}')) as value"
    for col in SIGNAL_TYPES
)


def get_connection():
    return psycopg2.connect(
        **config.db_connect_kwargs(),
    )


def is_stale(cur, max_age_hours, table):
    cur.execute(
        f"SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM {table}"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


# ─── Phase 1: category MV ──────────────────────────────────────────────


def fetch_category(cur, signal_type):
    """Top TOP_PER_TYPE entries for one signal type with sparklines + contexts.
    Mirrors getSignalCategoryDetail."""
    cur.execute(
        f"""SELECT val AS value, COUNT(DISTINCT evt.event_id)::int AS event_count
              FROM events_v3 e
              JOIN event_v3_titles evt ON evt.event_id = e.id
              JOIN title_labels tl ON tl.title_id = evt.title_id
              CROSS JOIN LATERAL unnest(tl.{signal_type}) AS val
             WHERE {DATE_CLAUSE}
               AND e.is_catchall = false
               AND e.merged_into IS NULL
             GROUP BY val
             ORDER BY event_count DESC
             LIMIT %s""",
        (TOP_PER_TYPE,),
    )
    top = [(value, int(count)) for value, count in cur.fetchall()]
    if not top:
        return []
    values = [v for v, _ in top]

    # Weekly sparklines for these values.
    cur.execute(
        f"""SELECT val AS value,
                   date_trunc('week', e.date)::date::text AS week,
                   COUNT(DISTINCT e.id)::int AS count
              FROM events_v3 e
              JOIN event_v3_titles evt ON evt.event_id = e.id
              JOIN title_labels tl ON tl.title_id = evt.title_id
              CROSS JOIN LATERAL unnest(tl.{signal_type}) AS val
             WHERE {DATE_CLAUSE}
               AND e.is_catchall = false
               AND e.merged_into IS NULL
               AND val = ANY(%s)
             GROUP BY val, week
             ORDER BY val, week""",
        (values,),
    )
    weekly_map = {}
    for value, week, count in cur.fetchall():
        weekly_map.setdefault(value, []).append({"week": week, "count": int(count)})

    # Contexts (case-insensitive) from monthly_signal_rankings.
    cur.execute(
        """SELECT value, context FROM monthly_signal_rankings
            WHERE signal_type = %s AND value = ANY(%s)
            ORDER BY month DESC""",
        (signal_type, values),
    )
    context_map = {}
    for value, context in cur.fetchall():
        # First (= most recent due to ORDER BY) wins.
        key = value.lower()
        if key not in context_map:
            context_map[key] = context

    return [
        {
            "signal_type": signal_type,
            "value": value,
            "event_count": event_count,
            "context": context_map.get(value.lower()),
            "weekly": weekly_map.get(value, []),
        }
        for value, event_count in top
    ]


def upsert_categories(cur, rows):
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_signal_category (signal_type, period, view, updated_at)
           VALUES %s
           ON CONFLICT (signal_type, period) DO UPDATE
             SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
        [(st, PERIOD, json.dumps({"entries": entries})) for st, entries in rows],
        template="(%s, %s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize_categories(cur, conn):
    rows = []
    for st in SIGNAL_TYPES:
        entries = fetch_category(cur, st)
        rows.append((st, entries))
    upsert_categories(cur, rows)
    conn.commit()
    return rows


# ─── Phase 2: detail MV ────────────────────────────────────────────────


def fetch_signal_stats(cur, signal_type, value):
    """Mirror getSignalStats: total + weekly + geo + tracks for one signal."""
    cur.execute(
        f"""WITH signal_events AS (
              SELECT DISTINCT e.id, e.date, e.ctm_id
                FROM events_v3 e
                JOIN event_v3_titles evt ON evt.event_id = e.id
                JOIN title_labels tl ON tl.title_id = evt.title_id
               WHERE {DATE_CLAUSE}
                 AND e.is_catchall = false
                 AND e.merged_into IS NULL
                 AND %s = ANY(tl.{signal_type})
            )
            SELECT
              (SELECT COUNT(*)::int FROM signal_events) AS total,
              (SELECT json_agg(w ORDER BY w.week) FROM (
                 SELECT date_trunc('week', date)::date::text AS week, COUNT(*)::int AS count
                   FROM signal_events GROUP BY 1
              ) w) AS weekly,
              (SELECT json_agg(g ORDER BY g.count DESC) FROM (
                 SELECT unnest(cv.iso_codes) AS country, COUNT(DISTINCT se.id)::int AS count
                   FROM signal_events se JOIN ctm c ON se.ctm_id = c.id
                   JOIN centroids_v3 cv ON c.centroid_id = cv.id
                  GROUP BY country ORDER BY count DESC LIMIT 20
              ) g) AS geo,
              (SELECT json_agg(t ORDER BY t.count DESC) FROM (
                 SELECT c.track, COUNT(DISTINCT se.id)::int AS count
                   FROM signal_events se JOIN ctm c ON se.ctm_id = c.id
                  GROUP BY c.track ORDER BY count DESC
              ) t) AS tracks""",
        (value,),
    )
    row = cur.fetchone()
    return {
        "total": int(row[0] or 0),
        "weekly": row[1] or [],
        "geo": row[2] or [],
        "tracks": row[3] or [],
    }


def fetch_relationship_clusters(cur, signal_type, value):
    """Mirror getRelationshipClusters. The 5-stage CTE pipeline is the
    heaviest of the lot. EN locale title fallback (DE variants are not
    rendered in this surface — kept simple)."""
    title_expr = "COALESCE(e.title, e.topic_core)"
    cur.execute(
        f"""WITH signal_events AS (
              SELECT e.id, {title_expr} AS title,
                     e.date::text AS date, e.source_batch_count
                FROM events_v3 e
               WHERE {DATE_CLAUSE}
                 AND e.is_catchall = false
                 AND e.merged_into IS NULL
                 AND (
                   SELECT COUNT(*) FILTER (WHERE %s = ANY(tl.{signal_type}))::float
                          / GREATEST(COUNT(*), 1)
                     FROM event_v3_titles evt
                     JOIN title_labels tl ON tl.title_id = evt.title_id
                    WHERE evt.event_id = e.id
                 ) >= 0.2
            ),
            event_cosigs AS (
              SELECT se.id AS event_id, expanded.sig_type AS signal_type, expanded.value
                FROM signal_events se
                JOIN event_v3_titles evt ON evt.event_id = se.id
                JOIN title_labels tl ON tl.title_id = evt.title_id
                CROSS JOIN LATERAL ({UNNEST_ALL_SIGNALS}) expanded(sig_type, value)
               WHERE NOT (expanded.sig_type = %s AND expanded.value = %s)
               GROUP BY se.id, expanded.sig_type, expanded.value
              HAVING COUNT(*)::float / GREATEST(
                       (SELECT COUNT(*) FROM event_v3_titles e2 WHERE e2.event_id = se.id), 1
                     ) >= 0.2
            ),
            top_cosigs AS (
              SELECT signal_type, value, COUNT(DISTINCT event_id)::int AS event_count
                FROM event_cosigs
               GROUP BY signal_type, value
              HAVING COUNT(DISTINCT event_id) >= 2
               ORDER BY event_count DESC LIMIT 20
            ),
            title_deduped AS (
              SELECT tc.signal_type, tc.value, tc.event_count,
                     se.id, se.title, se.date, se.source_batch_count,
                     ROW_NUMBER() OVER (
                         PARTITION BY tc.signal_type, tc.value, se.title
                         ORDER BY se.source_batch_count DESC
                     ) AS title_pick
                FROM top_cosigs tc
                JOIN event_cosigs ec ON ec.signal_type = tc.signal_type
                                    AND ec.value = tc.value
                JOIN signal_events se ON se.id = ec.event_id
            ),
            ranked AS (
              SELECT signal_type, value, event_count, id, title, date,
                     source_batch_count,
                     ROW_NUMBER() OVER (
                         PARTITION BY signal_type, value
                         ORDER BY source_batch_count DESC
                     ) AS rn
                FROM title_deduped WHERE title_pick = 1
            )
            SELECT signal_type, value, event_count,
                   MAX(title) FILTER (WHERE rn = 1) AS label,
                   json_agg(json_build_object(
                     'id', id, 'title', title, 'date', date,
                     'source_batch_count', source_batch_count
                   ) ORDER BY source_batch_count DESC) FILTER (WHERE rn <= 3) AS top_events
              FROM ranked
             GROUP BY signal_type, value, event_count
             ORDER BY event_count DESC""",
        (value, signal_type, value),
    )
    out = []
    for sig_type, val, event_count, label, top_events in cur.fetchall():
        out.append(
            {
                "signal_type": sig_type,
                "value": val,
                "event_count": int(event_count),
                "label": label,
                "top_events": top_events or [],
            }
        )
    return out


def upsert_details(cur, rows):
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_signal_detail (signal_type, value, period, view, updated_at)
           VALUES %s
           ON CONFLICT (signal_type, value, period) DO UPDATE
             SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
        [
            (st, val, PERIOD, json.dumps({"stats": stats, "clusters": clusters}))
            for st, val, stats, clusters in rows
        ],
        template="(%s, %s, %s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize_details(cur, conn, category_rows):
    """category_rows: [(signal_type, [entry, ...]), ...]"""
    pairs = []
    for st, entries in category_rows:
        for entry in entries:
            pairs.append((st, entry["value"]))

    print("Detail targets: %d (type, value) pairs" % len(pairs))
    batch = []
    done = 0
    for st, val in pairs:
        stats = fetch_signal_stats(cur, st, val)
        clusters = fetch_relationship_clusters(cur, st, val)
        batch.append((st, val, stats, clusters))
        if len(batch) >= 25:
            upsert_details(cur, batch)
            conn.commit()
            done += len(batch)
            batch = []
    if batch:
        upsert_details(cur, batch)
        conn.commit()
        done += len(batch)
    return done


# ─── Driver ────────────────────────────────────────────────────────────


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force:
                # Gate on the more frequently-checked of the two tables.
                cat_stale = is_stale(cur, max_age_hours, "mv_signal_category")
                det_stale = is_stale(cur, max_age_hours, "mv_signal_detail")
                if not cat_stale and not det_stale:
                    print(
                        "Skipped: both signals MVs refreshed within %.1fh"
                        % max_age_hours
                    )
                    return 0

            start = time.time()
            print("Phase 1: materializing categories (%d types)" % len(SIGNAL_TYPES))
            category_rows = materialize_categories(cur, conn)
            cat_elapsed = time.time() - start
            print("  done in %.1fs" % cat_elapsed)

            print("Phase 2: materializing details for top values")
            det_start = time.time()
            done = materialize_details(cur, conn, category_rows)
            det_elapsed = time.time() - det_start
            print("  done %d details in %.1fs" % (done, det_elapsed))

            total_elapsed = time.time() - start
            print(
                "Done: %d categories + %d details in %.1fs total"
                % (len(SIGNAL_TYPES), done, total_elapsed)
            )
            return len(SIGNAL_TYPES) + done
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Materialize signal category + detail blobs"
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=DEFAULT_MAX_AGE_HOURS,
        help="Skip if both tables refreshed within this window",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass staleness gate; refresh all rows",
    )
    args = parser.parse_args()
    materialize(max_age_hours=args.max_age_hours, force=args.force)


if __name__ == "__main__":
    main()
