"""Execute Maghreb taxonomy insert SQL"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def run_maghreb_taxonomy_insert():
    """Execute the Maghreb taxonomy SQL file"""
    sql_file = Path(__file__).parent / "insert_maghreb_taxonomy.sql"

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
            print("Executing Maghreb taxonomy inserts...")
            cur.execute(sql)

            # Get verification results
            try:
                results = cur.fetchall()
                if results:
                    print("\nMaghreb items added:")
                    for row in results:
                        print(f"  {row[0]} items")
            except Exception:
                pass

        conn.commit()
        print("\nMaghreb taxonomy inserts completed successfully!")

        # Verify by type
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_type, COUNT(*)
                FROM taxonomy_v3
                WHERE 'MIDEAST-MAGHREB' = ANY(centroid_ids)
                GROUP BY item_type
                ORDER BY item_type
            """
            )
            print("\nMaghreb items by type:")
            for item_type, count in cur.fetchall():
                print(f"  {item_type}: {count}")

            # Total MENA items (including Maghreb)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE centroid_ids && ARRAY[
                    'MIDEAST-PALESTINE', 'MIDEAST-IRAN', 'MIDEAST-SAUDI',
                    'MIDEAST-EGYPT', 'MIDEAST-TURKEY', 'MIDEAST-YEMEN',
                    'MIDEAST-SYRIA', 'MIDEAST-LEBANON', 'MIDEAST-GULF',
                    'MIDEAST-ISRAEL', 'MIDEAST-MAGHREB'
                ]::TEXT[]
            """
            )
            total = cur.fetchone()[0]
            print(f"\nTotal MENA-linked items (all 11 centroids): {total}")

        conn.close()
        return True

    except Exception as e:
        print(f"Insert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_maghreb_taxonomy_insert()
    sys.exit(0 if success else 1)
