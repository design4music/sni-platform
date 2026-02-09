"""Route orphaned titles (in title_assignments but not event_v3_titles) to catchalls."""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import psycopg2

from core.config import config


def is_geo_centroid(cid):
    return not cid.startswith("SYS-") and not cid.startswith("NON-STATE-")


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    # Find all orphaned titles with their CTM info
    cur.execute(
        """
        SELECT ta.title_id, ta.ctm_id, c.centroid_id, t.centroid_ids
        FROM title_assignments ta
        JOIN ctm c ON c.id = ta.ctm_id
        JOIN titles_v3 t ON t.id = ta.title_id
        WHERE NOT EXISTS (
            SELECT 1 FROM event_v3_titles evt
            JOIN events_v3 e ON e.id = evt.event_id
            WHERE evt.title_id = ta.title_id
              AND e.ctm_id = ta.ctm_id
        )
    """
    )
    rows = cur.fetchall()
    print("Found %d orphaned titles" % len(rows))

    # Group by ctm_id
    by_ctm = {}
    for title_id, ctm_id, home_centroid, centroid_ids in rows:
        by_ctm.setdefault(ctm_id, []).append(
            (title_id, home_centroid, centroid_ids or [])
        )

    print("Across %d CTMs" % len(by_ctm))

    routed_domestic = 0
    routed_international = 0
    created_catchalls = 0

    for ctm_id, titles in by_ctm.items():
        home_centroid = titles[0][1]  # same for all titles in CTM
        domestic_ids = []
        international_ids = []

        for title_id, _, centroid_ids in titles:
            foreign_geo = [
                c for c in centroid_ids if c != home_centroid and is_geo_centroid(c)
            ]
            if foreign_geo:
                international_ids.append(title_id)
            else:
                domestic_ids.append(title_id)

        # Route domestic orphans to domestic catchall
        if domestic_ids:
            cur.execute(
                """
                SELECT id FROM events_v3
                WHERE ctm_id = %s AND event_type = 'domestic' AND is_catchall = true
                LIMIT 1
            """,
                (ctm_id,),
            )
            row = cur.fetchone()
            if row:
                ca_id = row[0]
            else:
                ca_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO events_v3 (id, ctm_id, date, summary, event_type,
                        source_batch_count, is_catchall)
                    VALUES (%s, %s, CURRENT_DATE, 'Other coverage', 'domestic', 0, true)
                """,
                    (ca_id, ctm_id),
                )
                created_catchalls += 1

            for tid in domestic_ids:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                """,
                    (ca_id, tid),
                )
            routed_domestic += len(domestic_ids)

            cur.execute(
                """
                UPDATE events_v3 SET source_batch_count = (
                    SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
                ), updated_at = NOW() WHERE id = %s
            """,
                (ca_id, ca_id),
            )

        # Route international orphans to other_international catchall
        if international_ids:
            cur.execute(
                """
                SELECT id FROM events_v3
                WHERE ctm_id = %s AND event_type = 'other_international' AND is_catchall = true
                LIMIT 1
            """,
                (ctm_id,),
            )
            row = cur.fetchone()
            if row:
                ca_id = row[0]
            else:
                ca_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO events_v3 (id, ctm_id, date, summary, event_type,
                        source_batch_count, is_catchall)
                    VALUES (%s, %s, CURRENT_DATE, 'Other coverage', 'other_international',
                        0, true)
                """,
                    (ca_id, ctm_id),
                )
                created_catchalls += 1

            for tid in international_ids:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                """,
                    (ca_id, tid),
                )
            routed_international += len(international_ids)

            cur.execute(
                """
                UPDATE events_v3 SET source_batch_count = (
                    SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
                ), updated_at = NOW() WHERE id = %s
            """,
                (ca_id, ca_id),
            )

    conn.commit()
    conn.close()

    print("Routed domestic: %d" % routed_domestic)
    print("Routed international: %d" % routed_international)
    print("Created catchalls: %d" % created_catchalls)
    print("Total: %d" % (routed_domestic + routed_international))


if __name__ == "__main__":
    main()
