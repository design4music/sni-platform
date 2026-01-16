import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("""
        SELECT centroid_ids[1] as centroid_id
        FROM taxonomy_v3
        WHERE centroid_ids IS NOT NULL
          AND array_length(centroid_ids, 1) >= 1
          AND centroid_ids[1] !~ '^[A-Z]+-[A-Z]+$'
    """)
    results = cur.fetchall()
    print(f"Centroid IDs that don't match ^[A-Z]+-[A-Z]+$:")
    for row in results:
        print(f"  '{row[0]}'")
    print(f"\nTotal: {len(results)}")
conn.close()
