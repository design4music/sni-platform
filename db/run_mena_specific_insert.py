"""Execute MENA specific terms insert SQL"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def run_mena_specific_insert():
    """Execute the MENA specific terms SQL file"""
    sql_file = Path(__file__).parent / "insert_mena_specific_terms.sql"

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
            print("Executing MENA specific terms inserts...")
            cur.execute(sql)

            # Get verification results if available
            try:
                results = cur.fetchall()
                if results:
                    print("\nVerification - Key items added:")
                    for row in results:
                        if len(row) >= 2:
                            print(f"  {row[0]:25} -> {row[1]} items")
            except Exception:
                pass

        conn.commit()
        print("\nMENA specific terms inserts completed successfully!")

        # Count new items by type
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_type, COUNT(*)
                FROM taxonomy_v3
                WHERE item_raw IN (
                    'Iron Dome', 'Shahed', 'Khmeimim', 'Unit 8200',
                    'Qassam Brigades', 'Radwan Forces', 'Natanz', 'Abqaiq'
                )
                GROUP BY item_type
                ORDER BY item_type
            """
            )
            print("\nSample items added by type:")
            for item_type, count in cur.fetchall():
                print(f"  {item_type}: {count}")

            # Total MENA items
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
    success = run_mena_specific_insert()
    sys.exit(0 if success else 1)
