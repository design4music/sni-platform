"""Insert MENA centroids into centroids_v3"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def insert_mena_centroids():
    """Insert MENA centroid structure"""

    centroids = [
        # ====================================================================
        # Level 1: Core Country-Specific Centroids (Primary Anchors)
        # ====================================================================
        {
            "id": "MIDEAST-ISRAEL",
            "label": "Israel",
            "class": "geo",
            "primary_theater": "Israel",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-IRAN",
            "label": "Iran",
            "class": "geo",
            "primary_theater": "Iran",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-SAUDI",
            "label": "Saudi Arabia",
            "class": "geo",
            "primary_theater": "Saudi Arabia",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-EGYPT",
            "label": "Egypt",
            "class": "geo",
            "primary_theater": "Egypt",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-TURKEY",
            "label": "Turkey",
            "class": "geo",
            "primary_theater": "Turkey",
            "is_macro": False,
        },
        # ====================================================================
        # Level 1: Conflict & Regional Centroids
        # ====================================================================
        {
            "id": "MIDEAST-PALESTINE",
            "label": "Palestine",
            "class": "geo",
            "primary_theater": "Palestine",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-YEMEN",
            "label": "Yemen",
            "class": "geo",
            "primary_theater": "Yemen",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-SYRIA",
            "label": "Syria",
            "class": "geo",
            "primary_theater": "Syria",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-LEBANON",
            "label": "Lebanon",
            "class": "geo",
            "primary_theater": "Lebanon",
            "is_macro": False,
        },
        {
            "id": "MIDEAST-GULF",
            "label": "Gulf States",
            "class": "geo",
            "primary_theater": "Gulf",
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
            print("Inserting MENA centroids into centroids_v3...\n")

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

            # Verify insertion
            cur.execute(
                """
                SELECT COUNT(*)
                FROM centroids_v3
                WHERE id LIKE 'MIDEAST-%'
            """
            )
            count = cur.fetchone()[0]

            print(f"\nSuccessfully inserted/updated {count} MENA centroids")

            # Show breakdown by class
            cur.execute(
                """
                SELECT class, COUNT(*)
                FROM centroids_v3
                WHERE id LIKE 'MIDEAST-%'
                GROUP BY class
                ORDER BY class
            """
            )
            breakdown = cur.fetchall()
            print("\nBreakdown by class:")
            for cls, cnt in breakdown:
                print(f"  {cls}: {cnt}")

        conn.close()
        return True

    except Exception as e:
        print(f"Insert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = insert_mena_centroids()
    sys.exit(0 if success else 1)
