import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

print("=" * 60)
print("CHECKING ACTUAL DATABASE STATE")
print("=" * 60)

# Check all columns in taxonomy_v3
with conn.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, ordinal_position
        FROM information_schema.columns
        WHERE table_name = 'taxonomy_v3'
        ORDER BY ordinal_position
    """)
    print("\nAll columns in taxonomy_v3:")
    for row in cur.fetchall():
        print(f"  {row[3]:2d}. {row[0]:<20} - {row[1]:<20} {f'({row[2]})' if row[2] else ''}")

# Check actual data
with conn.cursor() as cur:
    cur.execute("""
        SELECT id, item_raw, centroid_ids
        FROM taxonomy_v3
        WHERE is_active = true
        LIMIT 3
    """)
    print("\nSample data:")
    for row in cur.fetchall():
        print(f"  {row[2]} (type: {type(row[2])})")

conn.close()
