"""Materialize per-outlet OutletLanding blobs into mv_outlet_landing.

Backs the /sources/[slug] page. Replaces 8 live queries:
  - getOutletProfile               (3 internal queries with feed_pubs CTE)
  - getPublisherStats              (lifetime stats from mv_publisher_stats)
  - getOutletStanceMonths          (distinct months from outlet_entity_stance)
  - getOutletStanceTimeline        (per-(entity,month) stance rows)
  - getOutletTrackTimeline         (per-month track distribution)
  - getOutletEntityDailyVolume     (per-day entity volume; heavy CTE)
  - getOutletMinorEntities         (entities below stance threshold; heavy CTE)
  - getSiblingOutlets              (other outlets in same country)

None of the queries are locale-aware, so one row per outlet covers
both en/de. ~207 rows total. Refresh 12h, no frozen-skip (rolling).

Publisher map is read from apps/frontend/lib/queries.ts at startup so
the canonical feed_name -> publisher_name mapping stays in sync with
the TS source.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

DEFAULT_MAX_AGE_HOURS = 12
SIBLING_LIMIT = 50
MINOR_MIN_TOTAL = 5
MINOR_LIMIT = 50
TOP_CTMS_LIMIT = 20
BATCH_SIZE = 25


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def is_stale(cur, max_age_hours):
    cur.execute(
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_outlet_landing"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def load_publisher_map_pairs():
    """Parse PUBLISHER_MAP_VALUES from queries.ts. Must stay in sync with
    the TS canonical. Returns list of (feed_name, publisher_name) pairs."""
    queries_path = (
        Path(__file__).parent.parent.parent / "apps" / "frontend" / "lib" / "queries.ts"
    )
    text = queries_path.read_text(encoding="utf-8")
    m = re.search(r"const PUBLISHER_MAP_VALUES = `(.+?)`;", text, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find PUBLISHER_MAP_VALUES in queries.ts")
    body = m.group(1)
    pairs = re.findall(r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)", body)
    if not pairs:
        raise RuntimeError("PUBLISHER_MAP_VALUES is empty after parsing")
    return pairs


def build_pubs_cte(cur, pairs, feed_names):
    """Build a (one-time) VALUES string for the publisher_map CTE that
    includes both the explicit pairs AND identity rows for every active
    feed (so feed_name itself maps to publisher_name = feed_name)."""
    all_pairs = list(pairs) + [(n, n) for n in feed_names]
    values_bytes = b",".join(cur.mogrify("(%s, %s)", (f, p)) for f, p in all_pairs)
    return values_bytes.decode("utf-8")


def fetch_active_feeds(cur):
    """5 active feed names have duplicate rows (Al-Ahram, Global Times, Al
    Jazeera, El Pais, Al Arabiya) for different language variants. Collapse
    to one row per name; the page is keyed on the display name only."""
    cur.execute(
        """SELECT DISTINCT ON (name) name, country_code, slug, language_code,
                  source_domain
             FROM feeds WHERE is_active = true
            ORDER BY name, id"""
    )
    return cur.fetchall()


def fetch_profile(cur, pubs_values, feed_name):
    """Mirror getOutletProfile: 3 queries returning coverage, top_ctms,
    article_count for one outlet."""
    cte = f"""WITH all_pubs(feed_name, publisher_name) AS (VALUES {pubs_values}),
              feed_pubs AS (SELECT publisher_name FROM all_pubs WHERE feed_name = %s)"""

    cur.execute(
        cte
        + """
        SELECT ta.centroid_id, cv.label, cv.iso_codes, COUNT(*)::int AS count
          FROM titles_v3 t
          JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name
          JOIN title_assignments ta ON ta.title_id = t.id
          JOIN centroids_v3 cv ON cv.id = ta.centroid_id
         GROUP BY ta.centroid_id, cv.label, cv.iso_codes
         ORDER BY count DESC""",
        (feed_name,),
    )
    coverage = [
        {
            "centroid_id": cid,
            "label": label,
            "iso_codes": iso,
            "count": int(count),
        }
        for cid, label, iso, count in cur.fetchall()
    ]

    cur.execute(
        cte
        + """
        SELECT ta.ctm_id, c.centroid_id, c.track,
               TO_CHAR(c.month, 'YYYY-MM') AS month,
               cv.label, COUNT(*)::int AS count
          FROM titles_v3 t
          JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name
          JOIN title_assignments ta ON ta.title_id = t.id
          JOIN ctm c ON c.id = ta.ctm_id
          JOIN centroids_v3 cv ON cv.id = ta.centroid_id
         GROUP BY ta.ctm_id, c.centroid_id, c.track, c.month, cv.label
         ORDER BY count DESC
         LIMIT %s""",
        (feed_name, TOP_CTMS_LIMIT),
    )
    top_ctms = [
        {
            "ctm_id": ctm_id,
            "centroid_id": cid,
            "track": track,
            "month": month,
            "label": label,
            "count": int(count),
        }
        for ctm_id, cid, track, month, label, count in cur.fetchall()
    ]

    cur.execute(
        cte
        + """
        SELECT COUNT(*)::int AS count FROM titles_v3 t
          JOIN feed_pubs fp ON t.publisher_name = fp.publisher_name""",
        (feed_name,),
    )
    article_count = cur.fetchone()[0]
    return coverage, top_ctms, int(article_count or 0)


def fetch_lifetime_stats(cur, feed_name):
    cur.execute(
        "SELECT stats FROM mv_publisher_stats WHERE feed_name = %s",
        (feed_name,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def fetch_stance_months(cur, feed_name):
    cur.execute(
        """SELECT DISTINCT TO_CHAR(month, 'YYYY-MM') AS m
             FROM outlet_entity_stance
            WHERE outlet_name = %s
            ORDER BY m DESC""",
        (feed_name,),
    )
    return [r[0] for r in cur.fetchall()]


def fetch_stance_timeline(cur, feed_name):
    cur.execute(
        """SELECT entity_kind, entity_code, entity_country,
                  TO_CHAR(month, 'YYYY-MM') AS month,
                  stance, confidence, tone, n_headlines
             FROM outlet_entity_stance
            WHERE outlet_name = %s
            ORDER BY month, entity_code""",
        (feed_name,),
    )
    out = []
    for ek, ec, ecn, month, stance, conf, tone, n in cur.fetchall():
        out.append(
            {
                "entity_kind": ek,
                "entity_code": ec,
                "entity_country": ecn,
                "month": month,
                "stance": float(stance) if stance is not None else None,
                "confidence": conf if conf in ("low", "medium", "high") else None,
                "tone": tone,
                "n_headlines": int(n),
            }
        )
    return out


def fetch_track_timeline(cur, feed_name):
    cur.execute(
        """SELECT TO_CHAR(month, 'YYYY-MM') AS month, stats
             FROM mv_publisher_stats_monthly
            WHERE feed_name = %s
            ORDER BY month""",
        (feed_name,),
    )
    out = []
    for month, stats in cur.fetchall():
        if not isinstance(stats, dict):
            continue
        out.append(
            {
                "month": month,
                "title_count": int(stats.get("title_count", 0)),
                "track_distribution": stats.get("track_distribution", {}),
            }
        )
    return out


def fetch_entity_daily(cur, feed_name):
    cur.execute(
        """WITH stance_entities AS (
              SELECT DISTINCT entity_kind, entity_code
                FROM outlet_entity_stance
               WHERE outlet_name = %s
            ),
            country_days AS (
              SELECT 'country'::text AS entity_kind,
                     je.value AS entity_code,
                     t.pubdate_utc::date::text AS day,
                     COUNT(*)::int AS n
                FROM titles_v3 t
                JOIN title_labels tl ON tl.title_id = t.id
                CROSS JOIN LATERAL jsonb_each_text(tl.entity_countries) je
               WHERE t.publisher_name = %s
                 AND je.value IN (
                     SELECT entity_code FROM stance_entities WHERE entity_kind = 'country'
                 )
               GROUP BY je.value, t.pubdate_utc::date
            ),
            person_days AS (
              SELECT 'person'::text AS entity_kind,
                     p AS entity_code,
                     t.pubdate_utc::date::text AS day,
                     COUNT(*)::int AS n
                FROM titles_v3 t
                JOIN title_labels tl ON tl.title_id = t.id
                CROSS JOIN LATERAL unnest(tl.persons) p
               WHERE t.publisher_name = %s
                 AND p IN (
                     SELECT entity_code FROM stance_entities WHERE entity_kind = 'person'
                 )
               GROUP BY p, t.pubdate_utc::date
            )
            SELECT * FROM country_days
            UNION ALL
            SELECT * FROM person_days
            ORDER BY day, entity_kind, entity_code""",
        (feed_name, feed_name, feed_name),
    )
    return [
        {"entity_kind": ek, "entity_code": ec, "day": day, "n": int(n)}
        for ek, ec, day, n in cur.fetchall()
    ]


def fetch_minor_entities(cur, feed_name):
    cur.execute(
        """WITH stance_entities AS (
              SELECT DISTINCT entity_kind, entity_code
                FROM outlet_entity_stance
               WHERE outlet_name = %s
            ),
            country_totals AS (
              SELECT 'country'::text AS entity_kind,
                     je.value AS entity_code,
                     COUNT(*)::int AS total
                FROM titles_v3 t
                JOIN title_labels tl ON tl.title_id = t.id
                CROSS JOIN LATERAL jsonb_each_text(tl.entity_countries) je
               WHERE t.publisher_name = %s
               GROUP BY je.value
            ),
            person_totals AS (
              SELECT 'person'::text AS entity_kind,
                     p AS entity_code,
                     COUNT(*)::int AS total
                FROM titles_v3 t
                JOIN title_labels tl ON tl.title_id = t.id
                CROSS JOIN LATERAL unnest(tl.persons) p
               WHERE t.publisher_name = %s
               GROUP BY p
            ),
            all_totals AS (
              SELECT entity_kind, entity_code, total FROM country_totals
              UNION ALL
              SELECT entity_kind, entity_code, total FROM person_totals
            )
            SELECT a.entity_kind, a.entity_code, a.total
              FROM all_totals a
              LEFT JOIN stance_entities s
                ON s.entity_kind = a.entity_kind AND s.entity_code = a.entity_code
             WHERE s.entity_code IS NULL
               AND a.total >= %s
             ORDER BY a.total DESC
             LIMIT %s""",
        (feed_name, feed_name, feed_name, MINOR_MIN_TOTAL, MINOR_LIMIT),
    )
    return [
        {"entity_kind": ek, "entity_code": ec, "total": int(total)}
        for ek, ec, total in cur.fetchall()
    ]


def fetch_siblings(cur, country_code, exclude_feed_name):
    if not country_code:
        return []
    cur.execute(
        """SELECT f.name AS feed_name, f.slug, f.language_code, f.source_domain,
                  COALESCE((mvs.stats->>'title_count')::int, 0) AS title_count
             FROM feeds f
             LEFT JOIN mv_publisher_stats mvs ON mvs.feed_name = f.name
            WHERE f.country_code = %s
              AND f.is_active = true
              AND f.name <> %s
            ORDER BY title_count DESC, f.name
            LIMIT %s""",
        (country_code, exclude_feed_name, SIBLING_LIMIT),
    )
    return [
        {
            "feed_name": fn,
            "slug": slug,
            "language_code": lang,
            "source_domain": dom,
            "title_count": int(tc or 0),
        }
        for fn, slug, lang, dom, tc in cur.fetchall()
    ]


def materialize_one(cur, pubs_values, feed):
    name, country_code, slug, language_code, source_domain = feed
    coverage, top_ctms, article_count = fetch_profile(cur, pubs_values, name)
    profile = {
        "feed_name": name,
        "source_domain": source_domain,
        "country_code": country_code,
        "language_code": language_code,
        "article_count": article_count,
        "centroid_coverage": coverage,
        "top_ctms": top_ctms,
    }
    return {
        "profile": profile,
        "lifetime_stats": fetch_lifetime_stats(cur, name),
        "stance_months": fetch_stance_months(cur, name),
        "stance_timeline": fetch_stance_timeline(cur, name),
        "track_timeline": fetch_track_timeline(cur, name),
        "entity_daily": fetch_entity_daily(cur, name),
        "minor_entities": fetch_minor_entities(cur, name),
        "siblings": fetch_siblings(cur, country_code, name),
    }


def upsert_batch(cur, rows):
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_outlet_landing (feed_name, view, updated_at)
           VALUES %s
           ON CONFLICT (feed_name) DO UPDATE
             SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
        [(fn, json.dumps(v)) for fn, v in rows],
        template="(%s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_outlet_landing"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_outlet_landing refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()
            pairs = load_publisher_map_pairs()
            feeds = fetch_active_feeds(cur)
            feed_names = [f[0] for f in feeds]
            pubs_values = build_pubs_cte(cur, pairs, feed_names)
            print(
                "Active feeds: %d, publisher_map pairs: %d" % (len(feeds), len(pairs))
            )

            done = 0
            batch = []
            for feed in feeds:
                view = materialize_one(cur, pubs_values, feed)
                batch.append((feed[0], view))
                if len(batch) >= BATCH_SIZE:
                    upsert_batch(cur, batch)
                    conn.commit()
                    done += len(batch)
                    batch = []
            if batch:
                upsert_batch(cur, batch)
                conn.commit()
                done += len(batch)

            elapsed = time.time() - start
            print("Done: %d rows upserted (%.1fs)" % (done, elapsed))
            return done
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Materialize per-outlet OutletLanding blobs"
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=DEFAULT_MAX_AGE_HOURS,
        help="Skip if table was refreshed within this window (default: %(default)s)",
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
