"""Migrate organizational entities from data_entities to taxonomy_v3"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def migrate_orgs():
    """Migrate organizational entity types to taxonomy_v3"""

    org_types = [
        "AppPlatform",
        "CentralBank",
        "Company",
        "IntelligenceAgency",
        "LegislativeBody",
        "MilitantGroup",
        "MultilateralDevelopmentBank",
        "NGO",
        "ORG",
        "Paramilitary",
        "ParliamentaryCaucus",
        "PMC",
        "PoliticalAlliance",
        "PoliticalMovement",
        "PoliticalParty",
        "RegionalOrganization",
        "ThinkTank",
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
            # First, check how many records we'll migrate
            placeholders = ",".join(["%s"] * len(org_types))
            cur.execute(
                f"""
                SELECT entity_type, COUNT(*)
                FROM data_entities
                WHERE entity_type IN ({placeholders})
                GROUP BY entity_type
                ORDER BY entity_type
            """,
                org_types,
            )

            counts = cur.fetchall()
            print("Entities to migrate:")
            total = 0
            for entity_type, count in counts:
                print(f"  {entity_type}: {count}")
                total += count
            print(f"\nTotal: {total} entities\n")

            # Migrate the data
            print("Migrating organizations to taxonomy_v3...")
            cur.execute(
                f"""
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
                    'org',
                    NULL,
                    COALESCE(aliases, '[]'::jsonb),
                    iso_code,
                    wikidata_qid,
                    true,
                    NOW(),
                    NOW()
                FROM data_entities
                WHERE entity_type IN ({placeholders})
                AND name_en IS NOT NULL
            """,
                org_types,
            )

            migrated = cur.rowcount
            conn.commit()

            print(
                f"Successfully migrated {migrated} organizational entities to taxonomy_v3"
            )

            # Verify migration
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE item_type = 'org'
            """
            )
            total_orgs = cur.fetchone()[0]
            print(f"Total 'org' items in taxonomy_v3: {total_orgs}")

        conn.close()
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = migrate_orgs()
    sys.exit(0 if success else 1)
