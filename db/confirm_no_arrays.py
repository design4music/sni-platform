import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

with conn.cursor() as cur:
    # Try to use array functions - should fail if it's really VARCHAR
    try:
        cur.execute("SELECT array_length(centroid_ids, 1) FROM taxonomy_v3 LIMIT 1")
        print("ERROR: Column is still an ARRAY!")
    except Exception as e:
        print("CONFIRMED: Column is VARCHAR (array functions don't work)")
        print(f"Error was: {e}")

    # Show actual values with explicit casting to confirm type
    cur.execute("""
        SELECT
            centroid_ids,
            centroid_ids::text as explicit_text,
            pg_typeof(centroid_ids) as column_type
        FROM taxonomy_v3
        WHERE is_active = true
        LIMIT 5
    """)
    print("\nSample values with type info:")
    for row in cur.fetchall():
        print(f"  Value: '{row[0]}' | Type: {row[2]}")

conn.close()
