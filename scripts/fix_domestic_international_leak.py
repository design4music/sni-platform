"""Move international titles out of domestic events into other_international catchalls."""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import psycopg2

from core.config import config


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    # Find all domestic event titles with foreign GEO centroids
    cur.execute(
        """
        SELECT evt.title_id, e.ctm_id, evt.event_id, e.id
        FROM event_v3_titles evt
        JOIN events_v3 e ON e.id = evt.event_id
        JOIN titles_v3 t ON t.id = evt.title_id
        WHERE e.event_type = 'domestic'
          AND EXISTS (
            SELECT 1 FROM UNNEST(t.centroid_ids) cid
            WHERE cid != (SELECT centroid_id FROM ctm WHERE id = e.ctm_id)
              AND cid NOT LIKE 'SYS-%%'
              AND cid NOT LIKE 'NON-STATE-%%'
          )
    """
    )
    rows = cur.fetchall()
    print("Found %d misplaced title-event links" % len(rows))

    # Group by ctm_id
    by_ctm = {}
    for title_id, ctm_id, event_id, _ in rows:
        by_ctm.setdefault(ctm_id, []).append((title_id, event_id))

    print("Across %d CTMs" % len(by_ctm))

    moved = 0
    created_catchalls = 0

    for ctm_id, titles in by_ctm.items():
        # Find existing other_international catchall
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
            oi_catchall_id = row[0]
        else:
            # Create other_international catchall
            oi_catchall_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO events_v3 (id, ctm_id, date, summary, event_type,
                    bucket_key, source_batch_count, is_catchall)
                VALUES (%s, %s, CURRENT_DATE, 'Other coverage', 'other_international',
                    NULL, 0, true)
            """,
                (oi_catchall_id, ctm_id),
            )
            created_catchalls += 1

        for title_id, old_event_id in titles:
            # Check if title already exists in this CTM's other_international events
            cur.execute(
                """
                SELECT 1 FROM event_v3_titles evt
                JOIN events_v3 e ON e.id = evt.event_id
                WHERE evt.title_id = %s AND e.ctm_id = %s AND e.event_type != 'domestic'
            """,
                (title_id, ctm_id),
            )
            if cur.fetchone():
                # Already in an international event - just delete domestic link
                cur.execute(
                    "DELETE FROM event_v3_titles WHERE title_id = %s AND event_id = %s",
                    (title_id, old_event_id),
                )
            else:
                # Move to other_international catchall
                cur.execute(
                    "UPDATE event_v3_titles SET event_id = %s WHERE title_id = %s AND event_id = %s",
                    (oi_catchall_id, title_id, old_event_id),
                )
            moved += 1

        # Update other_international catchall count
        cur.execute(
            """
            UPDATE events_v3 SET source_batch_count = (
                SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
            ), updated_at = NOW() WHERE id = %s
        """,
            (oi_catchall_id, oi_catchall_id),
        )

    # Update source_batch_count for all affected domestic events
    cur.execute(
        """
        UPDATE events_v3 e
        SET source_batch_count = (
            SELECT COUNT(*) FROM event_v3_titles evt WHERE evt.event_id = e.id
        ), updated_at = NOW()
        WHERE e.event_type = 'domestic'
    """
    )

    # Delete empty domestic events
    cur.execute(
        """
        DELETE FROM events_v3
        WHERE event_type = 'domestic'
          AND id NOT IN (SELECT DISTINCT event_id FROM event_v3_titles)
    """
    )
    deleted = cur.rowcount

    conn.commit()
    conn.close()

    print("Moved: %d title links" % moved)
    print("Created other_international catchalls: %d" % created_catchalls)
    print("Deleted empty domestic events: %d" % deleted)


if __name__ == "__main__":
    main()
