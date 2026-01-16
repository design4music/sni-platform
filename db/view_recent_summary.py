"""View most recently generated summary"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

conn = get_db_connection()

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT c.id, cent.label, c.track, c.month, c.title_count,
               c.summary_text, c.updated_at
        FROM ctm c
        JOIN centroids_v3 cent ON c.centroid_id = cent.id
        WHERE c.summary_text IS NOT NULL
        ORDER BY c.updated_at DESC
        LIMIT 1
    """
    )

    row = cur.fetchone()
    if row:
        ctm_id, label, track, month, title_count, summary, updated_at = row
        print("=" * 80)
        print(f"CTM: {ctm_id}")
        print(f"Centroid: {label}")
        print(f"Track: {track}")
        print(f"Month: {month}")
        print(f"Titles: {title_count}")
        print(f"Updated: {updated_at}")
        print("=" * 80)
        print()
        print(summary)
        print()
        print("=" * 80)
        print(f"Word count: {len(summary.split())}")

conn.close()
