"""Copy climate terms from taxonomy_terms to taxonomy_v3"""

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def copy_climate_to_v3():
    """
    Copy climate terms from taxonomy_terms to taxonomy_v3.

    Mapping:
    - Categories: environment_climate, environment_disasters
    - id -> id (keep same UUID)
    - name_en -> item_raw
    - terms -> aliases (extract just aliases, drop head_en)
    - item_type -> 'domain' (generic climate terms)
    - centroid_ids -> ['SYS-CLIMATE']
    - is_active -> true
    """

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get climate terms from environment categories
            cur.execute(
                """
                SELECT tt.id, tt.name_en, tt.terms
                FROM taxonomy_terms tt
                JOIN taxonomy_categories tc ON tt.category_id = tc.category_id
                WHERE tc.category_id IN (
                    'environment_climate',
                    'environment_disasters'
                )
                ORDER BY tt.name_en
            """
            )
            climate_terms = cur.fetchall()

            print(f"Found {len(climate_terms)} climate terms in taxonomy_terms")
            print("\nCopying to taxonomy_v3...")

            inserted_count = 0
            skipped_count = 0

            for id, name_en, terms_json in climate_terms:
                # Extract just the aliases part, dropping head_en
                if isinstance(terms_json, dict) and "aliases" in terms_json:
                    clean_aliases = terms_json["aliases"]
                else:
                    # Fallback: use as-is if already in correct format
                    clean_aliases = terms_json

                try:
                    cur.execute(
                        """
                        INSERT INTO taxonomy_v3 (
                            id,
                            item_raw,
                            item_type,
                            centroid_ids,
                            aliases,
                            is_active
                        )
                        VALUES (%s, %s, 'domain', ARRAY['SYS-CLIMATE'], %s, true)
                    """,
                        (id, name_en, Json(clean_aliases)),
                    )
                    inserted_count += 1

                except Exception as e:
                    print(f"Error inserting '{name_en}': {e}")
                    skipped_count += 1
                    continue

            conn.commit()

            print(f"\n{'='*70}")
            print("MIGRATION COMPLETE")
            print(f"{'='*70}")
            print(f"Total processed:       {len(climate_terms)}")
            print(f"Successfully inserted: {inserted_count}")
            print(f"Skipped (errors):      {skipped_count}")

            # Verify
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE item_type = 'domain' AND 'SYS-CLIMATE' = ANY(centroid_ids)
            """
            )
            total_climate = cur.fetchone()[0]
            print(f"\nTotal climate terms in taxonomy_v3: {total_climate}")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    copy_climate_to_v3()
