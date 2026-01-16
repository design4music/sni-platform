"""
Check centroid_ids usage in taxonomy_v3 table
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

# Check schema
print("=" * 60)
print("SCHEMA CHECK")
print("=" * 60)
with conn.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'taxonomy_v3'
          AND column_name = 'centroid_ids'
    """)
    schema = cur.fetchone()
    if schema:
        print(f"Column: {schema[0]}")
        print(f"Type: {schema[1]}")
        print(f"Max Length: {schema[2]}")

# Check usage patterns
print("\n" + "=" * 60)
print("USAGE PATTERNS")
print("=" * 60)
with conn.cursor() as cur:
    cur.execute("""
        SELECT
            centroid_ids,
            array_length(centroid_ids, 1) as num_centroids,
            COUNT(*) as count
        FROM taxonomy_v3
        WHERE is_active = true
        GROUP BY centroid_ids, array_length(centroid_ids, 1)
        ORDER BY array_length(centroid_ids, 1) DESC, count DESC
        LIMIT 20
    """)
    results = cur.fetchall()

    print(f"\n{'Centroid IDs':<30} | {'Num Centroids':<15} | {'Count':<10}")
    print("-" * 60)
    for centroid_ids, num_centroids, count in results:
        num_str = str(num_centroids) if num_centroids is not None else "NULL"
        print(f"{str(centroid_ids):<30} | {num_str:<15} | {count:<10}")

# Summary stats
print("\n" + "=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)
with conn.cursor() as cur:
    cur.execute("""
        SELECT
            MAX(array_length(centroid_ids, 1)) as max_centroids,
            MIN(array_length(centroid_ids, 1)) as min_centroids,
            COUNT(*) as total_records,
            COUNT(DISTINCT centroid_ids::text) as unique_patterns
        FROM taxonomy_v3
        WHERE is_active = true
    """)
    stats = cur.fetchone()
    print(f"Max centroids per record: {stats[0]}")
    print(f"Min centroids per record: {stats[1]}")
    print(f"Total active records: {stats[2]}")
    print(f"Unique centroid patterns: {stats[3]}")

# Check if ANY record has multiple centroids
print("\n" + "=" * 60)
print("RECORDS WITH MULTIPLE CENTROIDS")
print("=" * 60)
with conn.cursor() as cur:
    cur.execute("""
        SELECT COUNT(*)
        FROM taxonomy_v3
        WHERE is_active = true
          AND array_length(centroid_ids, 1) > 1
    """)
    multi_count = cur.fetchone()[0]
    print(f"Records with >1 centroid: {multi_count}")

    # Show examples if any exist
    if multi_count > 0:
        cur.execute("""
            SELECT id, item_raw, centroid_ids, array_length(centroid_ids, 1) as num_centroids
            FROM taxonomy_v3
            WHERE is_active = true
              AND array_length(centroid_ids, 1) > 1
            LIMIT 10
        """)
        examples = cur.fetchall()
        print("\nExamples:")
        for row in examples:
            print(f"  ID {row[0]}: '{row[1]}' -> {row[2]} ({row[3]} centroids)")

conn.close()

print("\n" + "=" * 60)
print("RECOMMENDATION")
print("=" * 60)
if multi_count == 0:
    print("No records have multiple centroids.")
    print("SAFE to migrate to TEXT or VARCHAR field.")
    print("\nRecommended type: VARCHAR(20)")
    print("  - Efficient storage and indexing")
    print("  - Suitable for centroid ID format (e.g., 'SYS-TECH')")
    print("  - Simple equality comparisons")
else:
    print(f"WARNING: {multi_count} records have multiple centroids!")
    print("Need to resolve multi-centroid records before migration.")
