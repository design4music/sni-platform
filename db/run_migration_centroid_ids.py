"""
Run migration: taxonomy_v3.centroid_ids ARRAY -> VARCHAR
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

# Read migration SQL
migration_file = Path(__file__).parent / 'migrations' / 'migrate_centroid_ids_to_varchar.sql'
with open(migration_file, 'r', encoding='utf-8') as f:
    migration_sql = f.read()

print("=" * 60)
print("MIGRATION: taxonomy_v3.centroid_ids ARRAY -> VARCHAR")
print("=" * 60)

conn = get_db_connection()

try:
    with conn.cursor() as cur:
        print("\nExecuting migration SQL...")
        cur.execute(migration_sql)

        # Check final schema
        print("\n" + "=" * 60)
        print("VERIFYING SCHEMA CHANGE")
        print("=" * 60)
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'taxonomy_v3'
              AND column_name = 'centroid_ids'
        """)
        schema = cur.fetchone()
        print(f"\nNew schema:")
        print(f"  Column: {schema[0]}")
        print(f"  Type: {schema[1]}")
        print(f"  Max Length: {schema[2]}")

        # Check sample data
        print("\n" + "=" * 60)
        print("SAMPLE DATA AFTER MIGRATION")
        print("=" * 60)
        cur.execute("""
            SELECT id, item_raw, centroid_ids
            FROM taxonomy_v3
            WHERE is_active = true
            ORDER BY created_at DESC
            LIMIT 5
        """)
        print("\nSample records:")
        for row in cur.fetchall():
            print(f"  ID {row[0]}: '{row[1][:50]}' -> '{row[2]}'")

        # Check for NULL values
        cur.execute("""
            SELECT COUNT(*) FROM taxonomy_v3 WHERE centroid_ids IS NULL
        """)
        null_count = cur.fetchone()[0]
        print(f"\nRecords with NULL centroid_ids: {null_count}")

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

except Exception as e:
    print("\n" + "=" * 60)
    print("MIGRATION FAILED")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    conn.close()
