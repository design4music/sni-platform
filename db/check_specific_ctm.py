"""Check specific CTM status"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

ctm_id = "f1213439-d010-4e59-92f5-7ae80653fc53"

conn = get_db_connection()

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT c.id, cent.label, c.track, c.month, c.title_count,
               CASE WHEN c.events_digest IS NOT NULL THEN jsonb_array_length(c.events_digest) ELSE 0 END as event_count,
               CASE WHEN c.summary_text IS NOT NULL THEN 'YES' ELSE 'NO' END as has_summary
        FROM ctm c
        JOIN centroids_v3 cent ON c.centroid_id = cent.id
        WHERE c.id = %s
    """,
        (ctm_id,),
    )

    row = cur.fetchone()
    if row:
        ctm_id, label, track, month, title_count, event_count, has_summary = row
        print(f"CTM ID:       {ctm_id}")
        print(f"Centroid:     {label}")
        print(f"Track:        {track}")
        print(f"Month:        {month}")
        print(f"Titles:       {title_count}")
        print(f"Events:       {event_count}")
        print(f"Has summary:  {has_summary}")
    else:
        print(f"CTM {ctm_id} not found")

conn.close()
