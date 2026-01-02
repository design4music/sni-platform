"""
Migration: Simplify taxonomy_v3 schema

Changes:
1. Remove unused columns: iso_code, wikidata_qid
2. Replace item_type with is_stop_word boolean
3. Align with consolidated taxonomy structure (items grouped by centroid)

Rationale:
- item_type distinctions (geo/person/org/domain) are obsolete with consolidated taxonomy
- Pass assignment now determined by centroid class, not item type
- Only meaningful distinction: stop word vs matching term
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def migrate():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        cur = conn.cursor()

        print("=== Taxonomy Schema Simplification Migration ===\n")

        # Step 1: Check current state
        cur.execute("SELECT COUNT(*) FROM taxonomy_v3")
        total_count = cur.fetchone()[0]
        print(f"Total taxonomy items: {total_count}")

        cur.execute("SELECT COUNT(*) FROM taxonomy_v3 WHERE item_type = 'stop'")
        stop_count = cur.fetchone()[0]
        print(f"Stop words: {stop_count}")
        print(f"Matching terms: {total_count - stop_count}\n")

        # Step 2: Add is_stop_word column
        print("Adding is_stop_word column...")
        cur.execute(
            """
            ALTER TABLE taxonomy_v3
            ADD COLUMN IF NOT EXISTS is_stop_word BOOLEAN DEFAULT FALSE
        """
        )
        print("  Done\n")

        # Step 3: Migrate data
        print("Migrating data from item_type to is_stop_word...")
        cur.execute(
            """
            UPDATE taxonomy_v3
            SET is_stop_word = (item_type = 'stop')
        """
        )
        print(f"  Updated {cur.rowcount} rows\n")

        # Step 4: Drop obsolete columns
        print("Dropping obsolete columns...")

        cur.execute("ALTER TABLE taxonomy_v3 DROP COLUMN IF EXISTS iso_code")
        print("  Dropped iso_code")

        cur.execute("ALTER TABLE taxonomy_v3 DROP COLUMN IF EXISTS wikidata_qid")
        print("  Dropped wikidata_qid")

        cur.execute("ALTER TABLE taxonomy_v3 DROP COLUMN IF EXISTS item_type")
        print("  Dropped item_type\n")

        # Step 5: Verify migration
        print("Verifying migration...")
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'taxonomy_v3'
            ORDER BY ordinal_position
        """
        )

        columns = [row[0] for row in cur.fetchall()]
        print(f"  Current columns: {', '.join(columns)}\n")

        # Verify counts
        cur.execute("SELECT COUNT(*) FROM taxonomy_v3 WHERE is_stop_word = TRUE")
        new_stop_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM taxonomy_v3 WHERE is_stop_word = FALSE")
        new_match_count = cur.fetchone()[0]

        print(f"  Stop words: {new_stop_count}")
        print(f"  Matching terms: {new_match_count}")

        if new_stop_count == stop_count:
            print("\n  SUCCESS: Data migrated correctly")
        else:
            print("\n  WARNING: Stop word count mismatch!")
            conn.rollback()
            return

        # Commit changes
        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
