"""Materialize per-locale NarrativesLanding blobs into mv_narratives_landing.

Backs the /narratives page. Replaces 3 live queries:
  - getAllMetaNarratives(locale)
  - getStrategicNarratives(locale)
  - getNarrativeSparklines()  (locale-neutral; folded into both rows)

Frontend filtering (actor / meta / q) is server-side after the warm fetch,
so one row per locale serves every filter combination.

Staleness gate only — no frozen-skip applies. Narrative content is
rolling: new matches arrive every cycle. Default 12h gate. --force
bypasses the gate (for JSONB shape changes).
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
LOCALES = ("en", "de")
SPARKLINE_DAYS = 90


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
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_narratives_landing"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def fetch_meta_narratives(cur, locale):
    name_col = "name_de" if locale == "de" else "name"
    desc_col = "description_de" if locale == "de" else "description"
    cur.execute(
        f"""SELECT id,
                   COALESCE({name_col}, name)        AS name,
                   COALESCE({desc_col}, description) AS description,
                   signals,
                   sort_order
              FROM meta_narratives
             ORDER BY sort_order"""
    )
    out = []
    for mid, name, description, signals, sort_order in cur.fetchall():
        out.append(
            {
                "id": mid,
                "name": name,
                "description": description,
                "signals": signals,
                "sort_order": sort_order,
            }
        )
    return out


def fetch_strategic_narratives(cur, locale):
    sn_name = "name_de" if locale == "de" else "name"
    sn_claim = "claim_de" if locale == "de" else "claim"
    mn_name = "name_de" if locale == "de" else "name"
    sql = f"""SELECT sn.id,
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
                     sn.tier,
                     sn.aligned_with,
                     sn.opposes,
                     COUNT(DISTINCT esn.event_id)
                       FILTER (WHERE ev.merged_into IS NULL)::int AS event_count
                FROM strategic_narratives sn
                JOIN meta_narratives mn ON mn.id = sn.meta_narrative_id
                LEFT JOIN centroids_v3 c ON c.id = sn.actor_centroid
                LEFT JOIN event_strategic_narratives esn ON esn.narrative_id = sn.id
                LEFT JOIN events_v3 ev ON ev.id = esn.event_id
               WHERE sn.is_active = true
               GROUP BY sn.id, mn.id, c.label, mn.name, mn.name_de
               ORDER BY mn.sort_order, sn.name"""
    cur.execute(sql)
    out = []
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
            tier,
            aligned_with,
            opposes,
            event_count,
        ) = row
        out.append(
            {
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
                "tier": tier,
                "aligned_with": aligned_with,
                "opposes": opposes,
                "event_count": int(event_count or 0),
            }
        )
    return out


def fetch_sparklines(cur):
    """Locale-neutral — same payload stored in both rows."""
    cur.execute(
        f"""SELECT narrative_id, week, event_count AS count
              FROM narrative_weekly_activity
             WHERE week >= (NOW() - INTERVAL '{SPARKLINE_DAYS} days')::date::text
             ORDER BY week"""
    )
    out = {}
    for narrative_id, week, count in cur.fetchall():
        out.setdefault(narrative_id, []).append({"week": week, "count": int(count)})
    return out


def fetch_meta_activity(cur):
    """90-day weekly event counts per meta-narrative. Locale-neutral.
    Backs the timeline on /narratives/meta/[id]."""
    cur.execute(
        f"""SELECT sn.meta_narrative_id,
                   date_trunc('week', e.date::date)::text AS week,
                   COUNT(*)::int AS count
              FROM event_strategic_narratives esn
              JOIN strategic_narratives sn ON sn.id = esn.narrative_id
              JOIN events_v3 e ON e.id = esn.event_id
             WHERE sn.is_active = true
               AND e.date >= NOW() - INTERVAL '{SPARKLINE_DAYS} days'
             GROUP BY sn.meta_narrative_id, week
             ORDER BY sn.meta_narrative_id, week"""
    )
    out = {}
    for meta_id, week, count in cur.fetchall():
        out.setdefault(meta_id, []).append({"week": week, "count": int(count)})
    return out


def materialize_one(cur, locale, sparklines, meta_activity):
    return {
        "meta_narratives": fetch_meta_narratives(cur, locale),
        "narratives": fetch_strategic_narratives(cur, locale),
        "sparklines": sparklines,
        "meta_activity": meta_activity,
    }


def upsert_batch(cur, rows):
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_narratives_landing (locale, view, updated_at)
           VALUES %s
           ON CONFLICT (locale) DO UPDATE
             SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
        [(loc, json.dumps(v)) for loc, v in rows],
        template="(%s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_narratives_landing"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_narratives_landing refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()
            sparklines = fetch_sparklines(cur)
            meta_activity = fetch_meta_activity(cur)

            rows = []
            for locale in LOCALES:
                view = materialize_one(cur, locale, sparklines, meta_activity)
                rows.append((locale, view))

            upsert_batch(cur, rows)
            conn.commit()

            elapsed = time.time() - start
            print(
                "Done: %d rows upserted (%d narratives, %d meta, %d sparklines, %d meta_activity) in %.1fs"
                % (
                    len(rows),
                    len(rows[0][1]["narratives"]),
                    len(rows[0][1]["meta_narratives"]),
                    len(sparklines),
                    len(meta_activity),
                    elapsed,
                )
            )
            return len(rows)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Materialize per-locale NarrativesLanding blobs"
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
        help="Bypass staleness gate; refresh both rows",
    )
    args = parser.parse_args()
    materialize(max_age_hours=args.max_age_hours, force=args.force)


if __name__ == "__main__":
    main()
