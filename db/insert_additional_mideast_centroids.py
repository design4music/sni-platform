"""Insert MIDEAST-IRAQ, MIDEAST-MAGHREB, MIDEAST-SUDAN centroids"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def insert_additional_mideast_centroids():
    """Insert Iraq, Maghreb (note: already exists), and Sudan centroids"""

    centroids = [
        {
            "id": "MIDEAST-IRAQ",
            "label": "Iraq",
            "class": "geo",
            "primary_theater": "Iraq",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-MAGHREB",
            "label": "Maghreb (North Africa)",
            "class": "geo",
            "primary_theater": "Maghreb",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-SUDAN",
            "label": "Sudan",
            "class": "geo",
            "primary_theater": "Sudan",
            "is_macro": False,
        },
    ]

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
            print("Inserting additional MIDEAST centroids...\n")

            for centroid in centroids:
                cur.execute(
                    """
                    INSERT INTO centroids_v3 (id, label, class, primary_theater, is_macro, is_active)
                    VALUES (%(id)s, %(label)s, %(class)s, %(primary_theater)s, %(is_macro)s, true)
                    ON CONFLICT (id) DO UPDATE
                    SET label = EXCLUDED.label,
                        class = EXCLUDED.class,
                        primary_theater = EXCLUDED.primary_theater,
                        is_macro = EXCLUDED.is_macro,
                        updated_at = NOW()
                """,
                    centroid,
                )

                print(
                    f"  [{centroid['class']:8}] {centroid['id']:25} -> {centroid['label']}"
                )

            conn.commit()

            # Verify
            cur.execute(
                """
                SELECT COUNT(*)
                FROM centroids_v3
                WHERE id LIKE 'MIDEAST-%'
            """
            )
            count = cur.fetchone()[0]
            print(f"\nTotal MIDEAST centroids: {count}")

        conn.close()
        return True

    except Exception as e:
        print(f"Insert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = insert_additional_mideast_centroids()
    sys.exit(0 if success else 1)
