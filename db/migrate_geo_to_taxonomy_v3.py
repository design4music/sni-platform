"""Migrate geographic entities (CAPITAL, COUNTRY) from data_entities to taxonomy_v3"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def migrate_geo():
    """Migrate geographic entity types to taxonomy_v3"""

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
            # First, check how many records we'll migrate
            cur.execute(
                """
                SELECT entity_type, COUNT(*)
                FROM data_entities
                WHERE entity_type IN ('CAPITAL', 'COUNTRY')
                GROUP BY entity_type
                ORDER BY entity_type
            """
            )

            counts = cur.fetchall()
            print("Entities to migrate:")
            total = 0
            for entity_type, count in counts:
                print(f"  {entity_type}: {count}")
                total += count
            print(f"\nTotal: {total} entities\n")

            # Migrate the data
            print("Migrating geographic entities to taxonomy_v3...")
            cur.execute(
                """
                INSERT INTO taxonomy_v3 (
                    id,
                    item_raw,
                    item_type,
                    centroid_ids,
                    aliases,
                    iso_code,
                    wikidata_qid,
                    is_active,
                    created_at,
                    updated_at
                )
                SELECT
                    id::uuid,
                    name_en,
                    'geo',
                    NULL,
                    COALESCE(aliases, '[]'::jsonb),
                    iso_code,
                    wikidata_qid,
                    true,
                    NOW(),
                    NOW()
                FROM data_entities
                WHERE entity_type IN ('CAPITAL', 'COUNTRY')
                AND name_en IS NOT NULL
            """
            )

            migrated = cur.rowcount
            conn.commit()

            print(
                f"Successfully migrated {migrated} geographic entities to taxonomy_v3"
            )

            # Verify migration
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE item_type = 'geo'
            """
            )
            total_geo = cur.fetchone()[0]
            print(f"Total 'geo' items in taxonomy_v3: {total_geo}")

            # Show overall totals
            cur.execute(
                """
                SELECT item_type, COUNT(*)
                FROM taxonomy_v3
                GROUP BY item_type
                ORDER BY item_type
            """
            )
            all_counts = cur.fetchall()
            print("\nCurrent taxonomy_v3 totals by item_type:")
            grand_total = 0
            for item_type, count in all_counts:
                print(f"  {item_type}: {count}")
                grand_total += count
            print(f"\nGrand total: {grand_total} items")

        conn.close()
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = migrate_geo()
    sys.exit(0 if success else 1)
