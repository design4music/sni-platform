import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

print("AFRICA-KENYA Results:")
print("=" * 60)

with conn.cursor() as cur:
    # Get breakdown by status and track
    cur.execute("""
        SELECT
            processing_status,
            COUNT(*) FILTER (WHERE track IS NOT NULL) as with_track,
            COUNT(*) FILTER (WHERE track IS NULL) as without_track,
            COUNT(*) as total
        FROM titles_v3
        WHERE 'AFRICA-KENYA' = ANY(centroid_ids)
        GROUP BY processing_status
        ORDER BY processing_status
    """)

    for row in cur.fetchall():
        status, with_track, without_track, total = row
        print(f"{status:20} | With track: {with_track}, Without track: {without_track}, Total: {total}")

print()
print("Titles details:")
print("-" * 60)

with conn.cursor() as cur:
    cur.execute("""
        SELECT title_display, processing_status, track, centroid_ids
        FROM titles_v3
        WHERE 'AFRICA-KENYA' = ANY(centroid_ids)
        ORDER BY processing_status, title_display
    """)

    for row in cur.fetchall():
        title, status, track, centroids = row
        print(f"{title[:50]:50} | {status:15} | {track or 'NULL':20}")

conn.close()
