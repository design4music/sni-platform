"""Mechanical track assignment using SECTOR_TO_TRACK mapping.

Replaces LLM-based Phase 3.3 (intel gating + track assignment).
NON_STRATEGIC sector titles are rejected. All others get mechanical track assignment.

Implementation note: this is a pure SQL operation (no per-row Python iteration).
A temp table holds the picked title snapshot; four statements then mark
NON_STRATEGIC titles, create missing CTMs, bulk-insert title_assignments,
and recompute title_count on affected CTMs. ~100x faster than the old
Python loop — proven on Feb + Jan backfills (~50k titles in 10 seconds).
"""

import psycopg2

from core.config import config

SECTOR_TO_TRACK = {
    "MILITARY": "geo_security",
    "INTELLIGENCE": "geo_security",
    "SECURITY": "geo_security",
    "DIPLOMACY": "geo_politics",
    "GOVERNANCE": "geo_politics",
    "ECONOMY": "geo_economy",
    "ENERGY_RESOURCES": "geo_economy",
    "TECHNOLOGY": "geo_economy",
    "INFRASTRUCTURE": "geo_economy",
    "HEALTH_ENVIRONMENT": "geo_society",
    "SOCIETY": "geo_society",
}

# SQL CASE expression mirroring SECTOR_TO_TRACK. Kept here so a change in the
# Python dict is a nudge to update this too; they stay in lockstep.
_SECTOR_CASE_SQL = """CASE tl.sector
  WHEN 'MILITARY' THEN 'geo_security'
  WHEN 'INTELLIGENCE' THEN 'geo_security'
  WHEN 'SECURITY' THEN 'geo_security'
  WHEN 'DIPLOMACY' THEN 'geo_politics'
  WHEN 'GOVERNANCE' THEN 'geo_politics'
  WHEN 'ECONOMY' THEN 'geo_economy'
  WHEN 'ENERGY_RESOURCES' THEN 'geo_economy'
  WHEN 'TECHNOLOGY' THEN 'geo_economy'
  WHEN 'INFRASTRUCTURE' THEN 'geo_economy'
  WHEN 'HEALTH_ENVIRONMENT' THEN 'geo_society'
  WHEN 'SOCIETY' THEN 'geo_society'
  ELSE 'geo_politics' END"""


def process_batch(max_titles=500, **kwargs):
    """Assign tracks mechanically from sector labels via bulk SQL.

    Picks up to `max_titles` titles that are 'assigned' with labels but not
    yet in title_assignments (newest-first), then:
      1. Marks NON_STRATEGIC titles as blocked_llm.
      2. Creates any missing (centroid, track, month) CTMs.
      3. Bulk-inserts title_assignments (1 row per non-SYS centroid per title).
      4. Recomputes title_count for affected CTMs.

    All four steps share a single snapshot of picked titles via a temp
    table, so a title marked NON_STRATEGIC in step 1 does not re-enter
    steps 2-3 with a different set.

    Returns a stats dict. Keeps the daemon-friendly stdout print.
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    try:
        # Snapshot the titles to process in a temp table. ON COMMIT DROP so
        # any explicit COMMIT below cleans it up; CREATE inside the current
        # transaction means it lives only as long as we need it.
        cur.execute(
            """CREATE TEMP TABLE picked_titles ON COMMIT DROP AS
               SELECT t.id AS title_id, t.centroid_ids, tl.sector,
                      date_trunc('month', t.pubdate_utc)::date AS month_start
                 FROM titles_v3 t
                 JOIN title_labels tl ON tl.title_id = t.id
                WHERE t.processing_status = 'assigned'
                  AND t.centroid_ids IS NOT NULL
                  AND tl.sector IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM title_assignments ta WHERE ta.title_id = t.id
                  )
                ORDER BY t.pubdate_utc DESC
                LIMIT %s""",
            (max_titles,),
        )
        cur.execute("SELECT COUNT(*) FROM picked_titles")
        total = cur.fetchone()[0]

        if total == 0:
            conn.commit()
            return {
                "total": 0,
                "assigned": 0,
                "rejected": 0,
                "new_ctms": 0,
                "new_assignments": 0,
            }

        # 1. Mark NON_STRATEGIC titles as blocked_llm
        cur.execute(
            """UPDATE titles_v3 SET processing_status = 'blocked_llm'
                WHERE id IN (SELECT title_id FROM picked_titles WHERE sector = 'NON_STRATEGIC')"""
        )
        rejected = cur.rowcount

        # 2. Create missing (centroid, track, month) CTMs.
        #    unnest() is in an inner subquery; outer WHERE filters SYS-* rows.
        cur.execute(
            f"""INSERT INTO ctm (centroid_id, track, month, title_count)
                SELECT DISTINCT x.centroid_id, x.track, x.month, 0
                  FROM (
                    SELECT unnest(pt.centroid_ids) AS centroid_id,
                           {_SECTOR_CASE_SQL} AS track,
                           pt.month_start AS month
                      FROM picked_titles pt
                      JOIN title_labels tl ON tl.title_id = pt.title_id
                     WHERE pt.sector IS NOT NULL AND pt.sector <> 'NON_STRATEGIC'
                  ) x
                 WHERE x.centroid_id NOT LIKE 'SYS-%%'
                ON CONFLICT (centroid_id, track, month) DO NOTHING"""
        )
        new_ctms = cur.rowcount

        # 3. Bulk-insert title_assignments. `RETURNING ctm_id` captures which
        #    CTMs actually got new rows (ON CONFLICT DO NOTHING suppresses
        #    duplicates), so step 4 only touches those.
        cur.execute(
            f"""WITH expanded AS (
                  SELECT pt.title_id, unnest(pt.centroid_ids) AS centroid_id,
                         {_SECTOR_CASE_SQL} AS track,
                         pt.month_start AS month
                    FROM picked_titles pt
                    JOIN title_labels tl ON tl.title_id = pt.title_id
                   WHERE pt.sector IS NOT NULL AND pt.sector <> 'NON_STRATEGIC'
                ),
                inserted AS (
                  INSERT INTO title_assignments (title_id, centroid_id, track, ctm_id)
                  SELECT e.title_id, e.centroid_id, e.track, c.id
                    FROM expanded e
                    JOIN ctm c ON c.centroid_id = e.centroid_id
                              AND c.track = e.track
                              AND c.month = e.month
                   WHERE NOT (e.centroid_id LIKE 'SYS-%%')
                  ON CONFLICT (title_id, centroid_id, track) DO NOTHING
                  RETURNING ctm_id
                )
                SELECT COUNT(*) AS total, array_agg(DISTINCT ctm_id) AS touched
                  FROM inserted"""
        )
        new_assignments, touched_ctm_ids = cur.fetchone()
        touched_ctm_ids = touched_ctm_ids or []

        # 4. Recompute title_count on touched CTMs (exact count, no drift).
        if touched_ctm_ids:
            cur.execute(
                """UPDATE ctm c SET title_count = sub.n
                     FROM (SELECT ctm_id, COUNT(*) AS n FROM title_assignments
                            WHERE ctm_id = ANY(%s::uuid[]) GROUP BY ctm_id) sub
                    WHERE c.id = sub.ctm_id""",
                (touched_ctm_ids,),
            )

        conn.commit()

        assigned = total - rejected
        print(
            "Phase 3.3 bulk: %d assigned, %d rejected (NON_STRATEGIC), "
            "%d new CTMs, %d new assignments"
            % (assigned, rejected, new_ctms, new_assignments)
        )
        return {
            "total": total,
            "assigned": assigned,
            "rejected": rejected,
            "new_ctms": new_ctms,
            "new_assignments": new_assignments,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    max_titles = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    process_batch(max_titles=max_titles)
