"""Remove uncommon 2-letter ISO code aliases from taxonomy_v3"""

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

# ISO codes that ARE commonly used in news articles
COMMONLY_USED_ISO_CODES = {
    "us",  # United States
    "uk",  # United Kingdom
    "gb",  # Great Britain (alternative for UK)
    "uae",  # United Arab Emirates (3-letter but commonly used)
}


def remove_uncommon_iso_aliases():
    """Remove 2-letter aliases that match ISO codes but aren't commonly used"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get all geo items with aliases
            cur.execute(
                """
                SELECT id, item_raw, aliases
                FROM taxonomy_v3
                WHERE item_type = 'geo'
                  AND aliases IS NOT NULL
            """
            )
            geo_items = cur.fetchall()

            print(
                f"Checking {len(geo_items)} geo items for uncommon ISO code aliases..."
            )

            updated_count = 0
            total_removed = 0

            for id, item_raw, aliases in geo_items:
                if not aliases:
                    continue

                modified = False
                removed_aliases = []

                # Check each language's aliases
                for lang, alias_list in aliases.items():
                    # Filter out 2-letter aliases that aren't commonly used
                    original_len = len(alias_list)
                    filtered_aliases = [
                        alias
                        for alias in alias_list
                        if len(alias) != 2 or alias.lower() in COMMONLY_USED_ISO_CODES
                    ]

                    if len(filtered_aliases) < original_len:
                        removed = [
                            alias
                            for alias in alias_list
                            if len(alias) == 2
                            and alias.lower() not in COMMONLY_USED_ISO_CODES
                        ]
                        removed_aliases.extend([(lang, r) for r in removed])
                        aliases[lang] = filtered_aliases
                        modified = True

                if modified:
                    # Update the record
                    cur.execute(
                        """
                        UPDATE taxonomy_v3
                        SET aliases = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """,
                        (Json(aliases), id),
                    )
                    updated_count += 1
                    total_removed += len(removed_aliases)

                    try:
                        print(f"\n{item_raw}:")
                        for lang, removed_alias in removed_aliases:
                            print(f"  Removed '{removed_alias}' ({lang})")
                    except UnicodeEncodeError:
                        # Skip printing if Unicode issues
                        pass

            conn.commit()

            print(f"\n{'='*70}")
            print("CLEANUP COMPLETE")
            print(f"{'='*70}")
            print(f"Items updated:       {updated_count}")
            print(f"Total aliases removed: {total_removed}")

    except Exception as e:
        print(f"Cleanup failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    remove_uncommon_iso_aliases()
