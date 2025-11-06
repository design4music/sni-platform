"""Execute Kurdish cross-regional taxonomy insert SQL"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def run_kurdish_taxonomy_insert():
    """Execute the Kurdish taxonomy SQL file"""
    sql_file = Path(__file__).parent / "insert_kurdish_taxonomy.sql"

    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}")
        return False

    print(f"Loading SQL from: {sql_file}")

    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        conn.autocommit = False

        with conn.cursor() as cur:
            print("Executing Kurdish taxonomy inserts...")
            cur.execute(sql)

            # Get verification results
            try:
                # First result: Total count
                results = cur.fetchall()
                if results:
                    print(f"\n{results[0][0]}: {results[0][1]}")

                # Move to next result set: Distribution
                if cur.nextset():
                    results = cur.fetchall()
                    if results:
                        print("\nDistribution across centroids:")
                        for centroid_id, count in results:
                            print(f"  {centroid_id:25} -> {count} items")
            except Exception as e:
                print(f"Warning: Could not fetch verification results: {e}")

        conn.commit()
        print("\nKurdish taxonomy inserts completed successfully!")

        conn.close()
        return True

    except Exception as e:
        print(f"Insert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_kurdish_taxonomy_insert()
    sys.exit(0 if success else 1)
