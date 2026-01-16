"""
Check actual centroid_id lengths in taxonomy_v3
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

with conn.cursor() as cur:
    cur.execute("""
        SELECT
            centroid_ids[1] as centroid_id,
            LENGTH(centroid_ids[1]) as length
        FROM taxonomy_v3
        WHERE centroid_ids IS NOT NULL
          AND array_length(centroid_ids, 1) >= 1
        ORDER BY LENGTH(centroid_ids[1]) DESC
        LIMIT 20
    """)
    results = cur.fetchall()

    print("=" * 60)
    print("CENTROID_ID LENGTHS")
    print("=" * 60)
    print(f"\n{'Centroid ID':<30} | {'Length':<10}")
    print("-" * 60)
    for centroid_id, length in results:
        print(f"{centroid_id:<30} | {length:<10}")

    # Get max length
    cur.execute("""
        SELECT MAX(LENGTH(centroid_ids[1])) as max_length
        FROM taxonomy_v3
        WHERE centroid_ids IS NOT NULL
    """)
    max_length = cur.fetchone()[0]
    print(f"\nMax length: {max_length}")
    print(f"Recommended VARCHAR size: VARCHAR({max_length + 5})")

conn.close()
