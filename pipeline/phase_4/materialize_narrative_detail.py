"""Materialize per-(narrative_id, locale) NarrativeDetail blobs into
mv_narrative_detail.

Backs the /narratives/[id] page. Replaces 4 live queries:
  - getStrategicNarrativeById     (narrative metadata + event_count)
  - getNarrativeWeeklyActivity    (90d weekly aggregation)
  - getNarrativeEvents            (top 50 events with title, locale-aware)
  - getCompetingNarratives        (top 10 narratives sharing events)

Materializer batches per locale: one combined SQL per locale fetches
all four shapes in a few large reads, assembled in Python. ~520 rows
total (260 active narratives × 2 locales). Each blob 5-20 KB.

Refresh cadence 12h, no frozen-skip — narrative attributions are
rolling. When matching quality improves, the next cycle picks up the
new event_strategic_narratives rows automatically.
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

DEFAULT_MAX_AGE_HOURS = 12
LOCALES = ("en", "de")
EVENTS_LIMIT = 50
COMPETING_LIMIT = 10
WEEKLY_DAYS = 90
BATCH_SIZE = 50


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
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_narrative_detail"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def fetch_active_narrative_ids(cur):
    cur.execute(
        "SELECT id FROM strategic_narratives WHERE is_active = true ORDER BY id"
    )
    return [r[0] for r in cur.fetchall()]


def fetch_narrative_meta_all(cur, locale):
    """All active narratives' metadata (with event_count) in one shot.
    Mirrors getStrategicNarrativeById's columns. Returns dict keyed by id."""
    sn_name = "name_de" if locale == "de" else "name"
    sn_claim = "claim_de" if locale == "de" else "claim"
    mn_name = "name_de" if locale == "de" else "name"
    cur.execute(
        f"""SELECT sn.id::text,
                   sn.meta_narrative_id,
                   COALESCE(mn.{mn_name}, mn.name) AS meta_name,
                   sn.category,
                   sn.actor_centroid,
                   c.label AS actor_label,
                   COALESCE(sn.{sn_name}, sn.name) AS name,
                   COALESCE(sn.{sn_claim}, sn.claim) AS claim,
                   sn.normative_conclusion,
                   sn.keywords,
                   sn.action_classes,
                   sn.domains,
                   COUNT(DISTINCT esn.event_id)
                     FILTER (WHERE ev.merged_into IS NULL)::int AS event_count
              FROM strategic_narratives sn
              JOIN meta_narratives mn ON mn.id = sn.meta_narrative_id
              LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
              LEFT JOIN event_strategic_narratives esn ON esn.narrative_id = sn.id
              LEFT JOIN events_v3 ev ON ev.id = esn.event_id
             WHERE sn.is_active = true
             GROUP BY sn.id, mn.id, c.label, mn.name, mn.name_de"""
    )
    out = {}
    for row in cur.fetchall():
        (
            sid,
            meta_id,
            meta_name,
            category,
            actor_centroid,
            actor_label,
            name,
            claim,
            normative,
            keywords,
            action_classes,
            domains,
            event_count,
        ) = row
        out[sid] = {
            "id": sid,
            "meta_narrative_id": meta_id,
            "meta_name": meta_name,
            "category": category,
            "actor_centroid": actor_centroid,
            "actor_label": actor_label,
            "name": name,
            "claim": claim,
            "normative_conclusion": normative,
            "keywords": keywords,
            "action_classes": action_classes,
            "domains": domains,
            "event_count": int(event_count or 0),
        }
    return out


def fetch_weekly_activity_all(cur):
    """Locale-neutral. Bulk fetch 90-day weekly counts per narrative.
    Returns dict[narrative_id] -> [{week, count}, ...] ordered by week."""
    cur.execute(
        f"""SELECT esn.narrative_id::text,
                   date_trunc('week', e.date::date)::text AS week,
                   COUNT(*)::int AS count
              FROM event_strategic_narratives esn
              JOIN events_v3 e ON e.id = esn.event_id
              JOIN strategic_narratives sn ON sn.id = esn.narrative_id
             WHERE sn.is_active = true
               AND e.date >= NOW() - INTERVAL '{WEEKLY_DAYS} days'
             GROUP BY esn.narrative_id, week
             ORDER BY esn.narrative_id, week"""
    )
    out = defaultdict(list)
    for nid, week, count in cur.fetchall():
        out[nid].append({"week": week, "count": int(count)})
    return out


def fetch_events_all(cur, locale):
    """Top EVENTS_LIMIT events per narrative ordered by date desc, locale-
    aware title. Single query with ROW_NUMBER OVER PARTITION."""
    title_expr = "COALESCE(e.title_de, e.title)" if locale == "de" else "e.title"
    cur.execute(
        f"""WITH ranked AS (
              SELECT esn.narrative_id::text AS narrative_id,
                     e.id::text AS event_id,
                     e.date::text AS date,
                     {title_expr} AS title,
                     esn.confidence,
                     ROW_NUMBER() OVER (
                         PARTITION BY esn.narrative_id
                         ORDER BY e.date DESC, e.id
                     ) AS rnk
                FROM event_strategic_narratives esn
                JOIN events_v3 e ON e.id = esn.event_id
                JOIN strategic_narratives sn ON sn.id = esn.narrative_id
               WHERE sn.is_active = true
                 AND e.title IS NOT NULL
                 AND e.merged_into IS NULL
            )
            SELECT narrative_id, event_id, date, title, confidence
              FROM ranked
             WHERE rnk <= %s
             ORDER BY narrative_id, rnk""",
        (EVENTS_LIMIT,),
    )
    out = defaultdict(list)
    for nid, eid, date, title, conf in cur.fetchall():
        out[nid].append(
            {
                "id": eid,
                "date": date,
                "title": title or "",
                "confidence": float(conf) if conf is not None else 0.0,
            }
        )
    return out


def fetch_competing_all(cur):
    """Locale-neutral (uses default name; the panel only renders names without
    DE variants today). Top COMPETING_LIMIT per narrative by shared event
    count, excluding same-actor narratives."""
    cur.execute(
        """WITH co AS (
              SELECT esn1.narrative_id::text AS source_id,
                     sn2.id::text AS competing_id,
                     sn2.name AS name,
                     sn2.actor_centroid,
                     c.label AS actor_label,
                     sn2.meta_narrative_id,
                     sn2.claim,
                     COUNT(*)::int AS shared_events,
                     ROW_NUMBER() OVER (
                         PARTITION BY esn1.narrative_id
                         ORDER BY COUNT(*) DESC, sn2.id
                     ) AS rnk
                FROM event_strategic_narratives esn1
                JOIN event_strategic_narratives esn2
                     ON esn2.event_id = esn1.event_id
                    AND esn2.narrative_id != esn1.narrative_id
                JOIN strategic_narratives sn1 ON sn1.id = esn1.narrative_id
                JOIN strategic_narratives sn2 ON sn2.id = esn2.narrative_id
                LEFT JOIN centroids_v3 c ON c.id = sn2.actor_centroid
               WHERE sn1.is_active = true
                 AND sn2.is_active = true
                 AND sn2.actor_centroid IS DISTINCT FROM sn1.actor_centroid
               GROUP BY esn1.narrative_id, sn2.id, c.label
            )
            SELECT source_id, competing_id, name, actor_centroid, actor_label,
                   meta_narrative_id, claim, shared_events
              FROM co
             WHERE rnk <= %s
             ORDER BY source_id, rnk""",
        (COMPETING_LIMIT,),
    )
    out = defaultdict(list)
    for row in cur.fetchall():
        (
            source_id,
            competing_id,
            name,
            actor_centroid,
            actor_label,
            meta_id,
            claim,
            shared,
        ) = row
        out[source_id].append(
            {
                "id": competing_id,
                "name": name,
                "actor_centroid": actor_centroid,
                "actor_label": actor_label,
                "meta_narrative_id": meta_id,
                "claim": claim,
                "shared_events": int(shared),
            }
        )
    return out


def upsert_batch(cur, rows):
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_narrative_detail (narrative_id, locale, view, updated_at)
           VALUES %s
           ON CONFLICT (narrative_id, locale) DO UPDATE
             SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
        [(nid, loc, json.dumps(v)) for nid, loc, v in rows],
        template="(%s, %s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_narrative_detail"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_narrative_detail refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()
            ids = fetch_active_narrative_ids(cur)
            print("Active narratives: %d" % len(ids))

            # Locale-neutral fetches once.
            weekly = fetch_weekly_activity_all(cur)
            competing = fetch_competing_all(cur)

            done = 0
            batch = []
            for locale in LOCALES:
                meta = fetch_narrative_meta_all(cur, locale)
                events = fetch_events_all(cur, locale)
                for nid in ids:
                    nid_str = str(nid)
                    if nid_str not in meta:
                        continue
                    view = {
                        "narrative": meta[nid_str],
                        "weekly_activity": weekly.get(nid_str, []),
                        "events": events.get(nid_str, []),
                        "competing": competing.get(nid_str, []),
                    }
                    batch.append((nid_str, locale, view))
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
        description="Materialize per-(narrative_id, locale) NarrativeDetail blobs"
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
