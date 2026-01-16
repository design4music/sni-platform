import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

print("=" * 60)
print("RENAMING: centroid_ids -> centroid_id")
print("=" * 60)

try:
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE taxonomy_v3
            RENAME COLUMN centroid_ids TO centroid_id
        """)
        conn.commit()

        # Verify
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'taxonomy_v3'
              AND column_name = 'centroid_id'
        """)
        schema = cur.fetchone()

        if schema:
            print("\nRename successful!")
            print(f"  Column: {schema[0]}")
            print(f"  Type: {schema[1]}({schema[2]})")
        else:
            print("\nERROR: Column not found after rename")

except Exception as e:
    conn.rollback()
    print(f"\nERROR: {e}")
    sys.exit(1)
finally:
    conn.close()

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
