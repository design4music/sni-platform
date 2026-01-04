"""
Migration: Drop obsolete is_macro column from centroids_v3

Rationale:
- is_macro was used for 3-pass system with early-exit (Pass 3 = macro centroids)
- Switched to accumulative matching (all passes run, no early-exit)
- Pass assignment logic removed from match_centroids.py
- Column no longer used anywhere in v3 code

Changes:
- DROP COLUMN centroids_v3.is_macro
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

        print("=== Drop is_macro Column Migration ===\n")

        # Step 1: Check current state
        cur.execute(
            """
            SELECT COUNT(*)
            FROM centroids_v3
            WHERE is_macro = TRUE
        """
        )
        macro_count = cur.fetchone()[0]
        print(f"Centroids with is_macro=TRUE: {macro_count}")

        cur.execute("SELECT COUNT(*) FROM centroids_v3")
        total_count = cur.fetchone()[0]
        print(f"Total centroids: {total_count}\n")

        # Step 2: Verify column exists
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'centroids_v3'
              AND column_name = 'is_macro'
        """
        )
        column_exists = cur.fetchone()

        if not column_exists:
            print("is_macro column does not exist. Migration already complete.")
            conn.close()
            return

        print("Dropping is_macro column...")
        cur.execute("ALTER TABLE centroids_v3 DROP COLUMN is_macro")
        print("  Done\n")

        # Step 3: Verify column dropped
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'centroids_v3'
            ORDER BY ordinal_position
        """
        )

        columns = [row[0] for row in cur.fetchall()]
        print(f"Current columns: {', '.join(columns)}\n")

        if "is_macro" in columns:
            print("ERROR: is_macro column still exists!")
            conn.rollback()
            return

        # Commit changes
        conn.commit()
        print("SUCCESS: Migration completed successfully!")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
