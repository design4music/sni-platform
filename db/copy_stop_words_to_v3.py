"""Copy stop words from taxonomy_terms to taxonomy_v3"""

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def copy_stop_words_to_v3():
    """
    Simple copy from taxonomy_terms to taxonomy_v3.

    Mapping:
    - id -> id (keep same UUID)
    - name_en -> item_raw
    - category_id -> DROP (not needed)
    - terms -> aliases (but extract just the aliases part)
    - is_active -> true (for all)
    - item_type -> 'stop' (for all)
    - centroid_ids -> NULL
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
            # Get only stop words from specific categories
            cur.execute(
                """
                SELECT tt.id, tt.name_en, tt.terms
                FROM taxonomy_terms tt
                JOIN taxonomy_categories tc ON tt.category_id = tc.category_id
                WHERE tc.category_id IN (
                    'culture_cinema',
                    'culture_fashion',
                    'culture_lifestyle',
                    'culture_entertainment',
                    'culture_art',
                    'culture_food',
                    'sport_general',
                    'sport_football',
                    'sport_olympics',
                    'sport_recreational'
                )
                ORDER BY tt.name_en
            """
            )
            stop_words = cur.fetchall()

            print(f"Found {len(stop_words)} stop words in taxonomy_terms")
            print("\nCopying to taxonomy_v3...")

            inserted_count = 0
            skipped_count = 0

            for id, name_en, terms_json in stop_words:
                # Extract just the aliases part, dropping head_en
                # taxonomy_terms.terms stores: {"aliases": {...}, "head_en": "..."}
                # taxonomy_v3.aliases needs just: {...}
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
                        VALUES (%s, %s, 'stop', NULL, %s, true)
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
            print(f"Total processed:       {len(stop_words)}")
            print(f"Successfully inserted: {inserted_count}")
            print(f"Skipped (duplicates):  {skipped_count}")

            # Verify
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE item_type = 'stop'
            """
            )
            total_stop_words = cur.fetchone()[0]
            print(f"\nTotal stop words in taxonomy_v3: {total_stop_words}")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    copy_stop_words_to_v3()
