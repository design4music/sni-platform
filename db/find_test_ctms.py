"""Find test CTMs for Phase 4.2 prompt validation"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

conn = get_db_connection()

print("Finding USA geo_politics CTMs...")
print("=" * 60)

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT c.id, cent.label, c.track, c.month, c.title_count,
               jsonb_array_length(c.events_digest) as event_count
        FROM ctm c
        JOIN centroids_v3 cent ON c.centroid_id = cent.id
        WHERE cent.label LIKE 'AMERICAS-USA%'
          AND c.track = 'geo_politics'
          AND c.events_digest IS NOT NULL
        ORDER BY c.month DESC, c.title_count DESC
        LIMIT 3
    """
    )

    rows = cur.fetchall()
    for ctm_id, label, track, month, title_count, event_count in rows:
        print(f"{ctm_id} | {label} | {track} | {month} | {title_count} titles | {event_count} events")

print()
print("Finding SYS-ENERGY CTMs...")
print("=" * 60)

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT c.id, cent.label, c.track, c.month, c.title_count,
               jsonb_array_length(c.events_digest) as event_count
        FROM ctm c
        JOIN centroids_v3 cent ON c.centroid_id = cent.id
        WHERE cent.label = 'SYS-ENERGY'
          AND c.events_digest IS NOT NULL
        ORDER BY c.month DESC, c.title_count DESC
        LIMIT 3
    """
    )

    rows = cur.fetchall()
    for ctm_id, label, track, month, title_count, event_count in rows:
        print(f"{ctm_id} | {label} | {track} | {month} | {title_count} titles | {event_count} events")

conn.close()
