"""Verify Kurdish taxonomy items"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def verify_kurdish_taxonomy():
    """Check Kurdish taxonomy items"""
    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )

        with conn.cursor() as cur:
            # Get all Kurdish items
            cur.execute(
                """
                SELECT item_raw, item_type, centroid_ids, aliases
                FROM taxonomy_v3
                WHERE item_raw IN ('Kurdistan', 'Kurds', 'Kurdish', 'PKK', 'YPG', 'Peshmerga', 'Rojava')
                ORDER BY item_type, item_raw
            """
            )
            results = cur.fetchall()

            print(f"Total Kurdish items: {len(results)}\n")

            for item_raw, item_type, centroid_ids, aliases in results:
                alias_count = len(aliases) if aliases else 0
                centroids_str = ", ".join(centroid_ids) if centroid_ids else "None"
                print(f"[{item_type:8}] {item_raw:20} -> {centroids_str}")
                print(f"           {alias_count} aliases")

            # Show distribution across centroids
            print("\n" + "=" * 60)
            print("Distribution across centroids:")
            print("=" * 60)

            cur.execute(
                """
                SELECT
                    unnest(centroid_ids) as centroid_id,
                    COUNT(*) as items
                FROM taxonomy_v3
                WHERE item_raw IN ('Kurdistan', 'Kurds', 'Kurdish', 'PKK', 'YPG', 'Peshmerga', 'Rojava')
                GROUP BY unnest(centroid_ids)
                ORDER BY centroid_id
            """
            )

            for centroid_id, count in cur.fetchall():
                print(f"  {centroid_id:25} -> {count} items")

        conn.close()
        return True

    except Exception as e:
        print(f"Verification failed: {e}")
        if conn:
            conn.close()
        return False


if __name__ == "__main__":
    success = verify_kurdish_taxonomy()
    sys.exit(0 if success else 1)
