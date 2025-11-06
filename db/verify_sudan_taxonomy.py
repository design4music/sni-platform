"""Verify Sudan taxonomy items"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def verify_sudan_taxonomy():
    """Check Sudan taxonomy items"""
    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )

        with conn.cursor() as cur:
            # Get all Sudan items
            cur.execute(
                """
                SELECT item_raw, item_type, aliases
                FROM taxonomy_v3
                WHERE 'MIDEAST-SUDAN' = ANY(centroid_ids)
                ORDER BY item_type, item_raw
            """
            )
            results = cur.fetchall()

            print(f"Total Sudan items: {len(results)}\n")

            for item_raw, item_type, aliases in results:
                alias_count = len(aliases) if aliases else 0
                print(f"[{item_type:8}] {item_raw:40} ({alias_count} aliases)")

            # Count by type
            cur.execute(
                """
                SELECT item_type, COUNT(*)
                FROM taxonomy_v3
                WHERE 'MIDEAST-SUDAN' = ANY(centroid_ids)
                GROUP BY item_type
                ORDER BY item_type
            """
            )
            print("\nBy type:")
            for item_type, count in cur.fetchall():
                print(f"  {item_type}: {count}")

        conn.close()
        return True

    except Exception as e:
        print(f"Verification failed: {e}")
        if conn:
            conn.close()
        return False


if __name__ == "__main__":
    success = verify_sudan_taxonomy()
    sys.exit(0 if success else 1)
