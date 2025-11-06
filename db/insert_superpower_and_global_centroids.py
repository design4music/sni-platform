"""Insert superpower domestic and global systemic centroids"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def insert_superpower_and_global_centroids():
    """Insert 4 superpower domestic + 2 global systemic centroids"""

    centroids = [
        # Superpower Domestic (Pass 3 - macro catch-alls)
        {
            "id": "US-DOMESTIC",
            "label": "United States Domestic",
            "class": "geo",
            "primary_theater": "DOMESTIC",
            "is_macro": True,
        },
        {
            "id": "RU-DOMESTIC",
            "label": "Russia Domestic",
            "class": "geo",
            "primary_theater": "DOMESTIC",
            "is_macro": True,
        },
        {
            "id": "EU-DOMESTIC",
            "label": "European Union Domestic",
            "class": "geo",
            "primary_theater": "DOMESTIC",
            "is_macro": True,
        },
        {
            "id": "CN-DOMESTIC",
            "label": "China Domestic",
            "class": "geo",
            "primary_theater": "DOMESTIC",
            "is_macro": True,
        },
        # Global Systemic (Pass 2 - cross-cutting topics)
        {
            "id": "GLOBAL-CLIMATE",
            "label": "Climate Change & Environment",
            "class": "systemic",
            "primary_theater": None,
            "is_macro": False,
        },
        {
            "id": "GLOBAL-TECH",
            "label": "Technology & Innovation",
            "class": "systemic",
            "primary_theater": None,
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
            print("Inserting superpower domestic and global systemic centroids...\n")

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

                macro_flag = "[MACRO]" if centroid["is_macro"] else ""
                print(
                    f"  [{centroid['class']:8}] {macro_flag:8} {centroid['id']:20} -> {centroid['label']}"
                )

            conn.commit()

            # Show counts by class
            cur.execute(
                """
                SELECT class, COUNT(*)
                FROM centroids_v3
                GROUP BY class
                ORDER BY class
            """
            )
            print("\nCentroid counts by class:")
            for class_name, count in cur.fetchall():
                print(f"  {class_name:10} -> {count}")

            # Show macro centroids
            cur.execute(
                """
                SELECT id, label
                FROM centroids_v3
                WHERE is_macro = true
                ORDER BY id
            """
            )
            print("\nMacro centroids (Pass 3 catch-alls):")
            for id, label in cur.fetchall():
                print(f"  {id:20} -> {label}")

            # Show systemic centroids
            cur.execute(
                """
                SELECT id, label
                FROM centroids_v3
                WHERE class = 'systemic'
                ORDER BY id
            """
            )
            print("\nSystemic centroids (Pass 2 global topics):")
            for id, label in cur.fetchall():
                print(f"  {id:20} -> {label}")

        conn.close()
        return True

    except Exception as e:
        print(f"Insert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = insert_superpower_and_global_centroids()
    sys.exit(0 if success else 1)
