"""Mechanical track assignment using SECTOR_TO_TRACK mapping.

Replaces LLM-based Phase 3.3 (intel gating + track assignment).
NON_STRATEGIC sector titles are rejected. All others get mechanical track assignment.
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


def process_batch(max_titles=500, **kwargs):
    """Assign tracks mechanically from sector labels. Drop-in replacement for phase33_process."""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    # Find titles that need track assignment (have labels but no title_assignments)
    cur.execute(
        """
        SELECT t.id, t.centroid_ids, tl.sector, t.pubdate_utc
        FROM titles_v3 t
        JOIN title_labels tl ON tl.title_id = t.id
        WHERE t.processing_status = 'assigned'
          AND t.centroid_ids IS NOT NULL
          AND t.id NOT IN (SELECT title_id FROM title_assignments)
          AND tl.sector IS NOT NULL
        ORDER BY t.pubdate_utc DESC
        LIMIT %s
    """,
        (max_titles,),
    )
    rows = cur.fetchall()

    if not rows:
        conn.close()
        return

    assigned = 0
    rejected = 0

    for title_id, centroid_ids, sector, pubdate in rows:
        # NON_STRATEGIC = reject (don't assign track)
        if sector == "NON_STRATEGIC":
            cur.execute(
                "UPDATE titles_v3 SET processing_status = 'blocked_llm' WHERE id = %s",
                (title_id,),
            )
            rejected += 1
            continue

        track = SECTOR_TO_TRACK.get(sector, "geo_politics")

        # Determine month from pubdate
        if pubdate:
            month = pubdate.strftime("%Y-%m-01")
        else:
            month = "2026-01-01"

        # Create title_assignments for each centroid
        for centroid_id in centroid_ids or []:
            if centroid_id.startswith("SYS-"):
                continue

            # Get or create CTM
            cur.execute(
                "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
                (centroid_id, track, month),
            )
            ctm_row = cur.fetchone()
            if ctm_row:
                ctm_id = ctm_row[0]
            else:
                cur.execute(
                    "INSERT INTO ctm (centroid_id, track, month, title_count) "
                    "VALUES (%s, %s, %s, 0) RETURNING id",
                    (centroid_id, track, month),
                )
                ctm_id = cur.fetchone()[0]

            # Create title_assignment
            cur.execute(
                "INSERT INTO title_assignments (title_id, centroid_id, track, ctm_id) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (title_id, centroid_id, track, ctm_id),
            )

            # Update CTM title count
            cur.execute(
                "UPDATE ctm SET title_count = title_count + 1 WHERE id = %s",
                (ctm_id,),
            )

        assigned += 1

    conn.commit()
    print(
        "Phase 3.3 mechanical: %d assigned, %d rejected (NON_STRATEGIC), %d total"
        % (assigned, rejected, len(rows))
    )
    conn.close()


if __name__ == "__main__":
    import sys

    max_titles = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    process_batch(max_titles=max_titles)
