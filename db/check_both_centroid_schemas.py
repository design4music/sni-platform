"""
Check centroid_ids schema in both taxonomy_v3 and titles_v3
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

print("=" * 60)
print("SCHEMA COMPARISON: centroid_ids")
print("=" * 60)

# Check taxonomy_v3
print("\n1. taxonomy_v3.centroid_ids:")
with conn.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'taxonomy_v3'
          AND column_name = 'centroid_ids'
    """)
    schema = cur.fetchone()
    if schema:
        print(f"   Type: {schema[1]}")
        print(f"   Max Length: {schema[2]}")

    # Sample data
    cur.execute("""
        SELECT id, item_raw, centroid_ids
        FROM taxonomy_v3
        WHERE is_active = true
        LIMIT 5
    """)
    print("\n   Sample data:")
    for row in cur.fetchall():
        print(f"     ID {row[0]}: '{row[1]}' -> {row[2]}")

# Check titles_v3
print("\n2. titles_v3.centroid_ids:")
with conn.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'titles_v3'
          AND column_name = 'centroid_ids'
    """)
    schema = cur.fetchone()
    if schema:
        print(f"   Type: {schema[1]}")
        print(f"   Max Length: {schema[2]}")

    # Sample data
    cur.execute("""
        SELECT id, title_display, centroid_ids, array_length(centroid_ids, 1) as num_centroids
        FROM titles_v3
        WHERE processing_status = 'assigned'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    print("\n   Sample data:")
    for row in cur.fetchall():
        title_preview = row[1][:40] if row[1] else ""
        num_centroids = row[3] if row[3] else 0
        print(f"     ID {row[0]}: {num_centroids} centroids -> {row[2]}")

# Check titles_v3 with multiple centroids
print("\n3. titles_v3 - Records with multiple centroids:")
with conn.cursor() as cur:
    cur.execute("""
        SELECT
            array_length(centroid_ids, 1) as num_centroids,
            COUNT(*) as count
        FROM titles_v3
        WHERE processing_status = 'assigned'
        GROUP BY array_length(centroid_ids, 1)
        ORDER BY array_length(centroid_ids, 1) DESC
    """)
    results = cur.fetchall()
    print("\n   Distribution:")
    for num_centroids, count in results:
        print(f"     {num_centroids} centroids: {count} titles")

conn.close()

print("\n" + "=" * 60)
print("KEY INSIGHT")
print("=" * 60)
print("- taxonomy_v3: Each CSC has ONE centroid (source of truth)")
print("- titles_v3: Each title can match MULTIPLE centroids (accumulative)")
print("\nMigration strategy:")
print("  1. taxonomy_v3.centroid_ids: ARRAY -> VARCHAR (1-to-1 relationship)")
print("  2. titles_v3.centroid_ids: Keep as ARRAY (1-to-many relationship)")
