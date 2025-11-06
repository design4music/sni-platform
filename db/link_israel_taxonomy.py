"""Link taxonomy items to MIDEAST-ISRAEL centroid"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def link_israel_taxonomy():
    """Link Israel-related taxonomy items to MIDEAST-ISRAEL centroid"""

    # List of terms that should link to MIDEAST-ISRAEL
    israel_terms = [
        # Countries
        "Israel",
        # Capitals/Cities
        "Jerusalem",
        "Tel Aviv",
        # Key Persons
        "Benjamin Netanyahu",
        "Yoav Gallant",
        "Yair Lapid",
        "Benny Gantz",
        # Key Organizations
        "IDF",
        "Israel Defense Forces",
        "Mossad",
        "Shin Bet",
        "Knesset",
        # Military branches
        "Israeli Army",
        "Israeli Navy",
        "Israeli Air Force",
        # Regions (Israeli-controlled)
        "West Bank",
        "Golan Heights",
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
            print("Linking taxonomy items to MIDEAST-ISRAEL...\n")

            updated_count = 0
            not_found = []

            for term in israel_terms:
                # Check if term exists in taxonomy_v3
                cur.execute(
                    """
                    SELECT id, item_raw, item_type, centroid_ids
                    FROM taxonomy_v3
                    WHERE item_raw = %s
                """,
                    (term,),
                )

                result = cur.fetchone()

                if result:
                    item_id, item_raw, item_type, current_centroid_ids = result

                    # Add MIDEAST-ISRAEL to centroid_ids array if not already present
                    if current_centroid_ids is None:
                        new_centroid_ids = ["MIDEAST-ISRAEL"]
                    elif "MIDEAST-ISRAEL" not in current_centroid_ids:
                        new_centroid_ids = current_centroid_ids + ["MIDEAST-ISRAEL"]
                    else:
                        # Already linked
                        print(
                            f"  [SKIP] {item_raw:30} ({item_type:8}) - already linked"
                        )
                        continue

                    # Update the record
                    cur.execute(
                        """
                        UPDATE taxonomy_v3
                        SET centroid_ids = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """,
                        (new_centroid_ids, item_id),
                    )

                    print(f"  [LINK] {item_raw:30} ({item_type:8}) -> MIDEAST-ISRAEL")
                    updated_count += 1
                else:
                    not_found.append(term)
                    print(f"  [MISS] {term:30} - not in taxonomy_v3")

            conn.commit()

            # Summary
            print(f"\n{'='*70}")
            print("Summary:")
            print(f"  Total terms checked: {len(israel_terms)}")
            print(f"  Successfully linked: {updated_count}")
            print(f"  Not found in taxonomy: {len(not_found)}")

            if not_found:
                print("\nTerms not found (need to be added to taxonomy_v3):")
                for term in not_found:
                    print(f"  - {term}")

            # Verify linkage
            cur.execute(
                """
                SELECT COUNT(*)
                FROM taxonomy_v3
                WHERE 'MIDEAST-ISRAEL' = ANY(centroid_ids)
            """
            )
            total_linked = cur.fetchone()[0]
            print(f"\nTotal taxonomy items linked to MIDEAST-ISRAEL: {total_linked}")

        conn.close()
        return True

    except Exception as e:
        print(f"Linking failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = link_israel_taxonomy()
    sys.exit(0 if success else 1)
