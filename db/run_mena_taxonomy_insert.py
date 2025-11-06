"""Execute MENA taxonomy insert SQL"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def run_mena_taxonomy_insert():
    """Execute the MENA taxonomy SQL file"""
    sql_file = Path(__file__).parent / "insert_mena_taxonomy.sql"

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
            print("Executing MENA taxonomy inserts...")
            cur.execute(sql)

            # Process all result sets
            try:
                # First SELECT: items per centroid
                print("\nItems per centroid:")
                results = cur.fetchall()
                for row in results:
                    if len(row) >= 2:
                        centroid_id, count = row[0], row[1]
                        print(f"  {centroid_id:25} -> {count:3} items")

                # Move to next result set if available
                if cur.nextset():
                    # Second SELECT: total count
                    results = cur.fetchall()
                    if results and len(results[0]) >= 1:
                        print(f"\nTotal from SQL: {results[0][0]} items")
            except Exception:
                pass  # No more result sets

        conn.commit()
        print("\nMENA taxonomy inserts completed successfully!")

        # Final verification
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE centroid_ids && ARRAY[
                    'MIDEAST-PALESTINE', 'MIDEAST-IRAN', 'MIDEAST-SAUDI',
                    'MIDEAST-EGYPT', 'MIDEAST-TURKEY', 'MIDEAST-YEMEN',
                    'MIDEAST-SYRIA', 'MIDEAST-LEBANON', 'MIDEAST-GULF', 'MIDEAST-ISRAEL'
                ]::TEXT[]
            """
            )
            total = cur.fetchone()[0]
            print(f"\nTotal MENA-linked items in taxonomy_v3: {total}")

        conn.close()
        return True

    except Exception as e:
        print(f"Insert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_mena_taxonomy_insert()
    sys.exit(0 if success else 1)
