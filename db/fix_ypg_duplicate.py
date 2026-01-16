"""Fix YPG duplicate entry"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def fix_ypg_duplicate():
    """Remove YPG entry with null centroid_ids"""
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
            # Show all YPG entries
            cur.execute(
                """
                SELECT id, item_raw, centroid_ids
                FROM taxonomy_v3
                WHERE item_raw = 'YPG'
                ORDER BY created_at
            """
            )
            results = cur.fetchall()
            print(f"Found {len(results)} YPG entries:\n")
            for id, item_raw, centroid_ids in results:
                print(f"  ID: {id}")
                print(f"  Centroids: {centroid_ids}")
                print()

            # Delete the one with null or empty centroid_ids
            cur.execute(
                """
                DELETE FROM taxonomy_v3
                WHERE item_raw = 'YPG'
                AND (centroid_ids IS NULL OR centroid_ids = '{}')
                RETURNING id
            """
            )
            deleted = cur.fetchall()

            if deleted:
                print(f"Deleted {len(deleted)} invalid YPG entry/entries:")
                for (id,) in deleted:
                    print(f"  - {id}")
            else:
                print("No invalid YPG entries found to delete.")

            conn.commit()

            # Verify
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE item_raw = 'YPG'
            """
            )
            count = cur.fetchone()[0]
            print(f"\nRemaining YPG entries: {count}")

        conn.close()
        return True

    except Exception as e:
        print(f"Fix failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = fix_ypg_duplicate()
    sys.exit(0 if success else 1)
