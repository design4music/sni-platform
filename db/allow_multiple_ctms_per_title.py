"""Update titles_v3 to support multiple CTMs per title"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def update_schema():
    """Change ctm_id to ctm_ids array"""
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
            print("Updating titles_v3 to support multiple CTMs...")

            # Drop the foreign key constraint first
            print("1. Dropping foreign key constraint...")
            cur.execute(
                """
                ALTER TABLE titles_v3
                DROP CONSTRAINT IF EXISTS titles_v3_ctm_id_fkey
            """
            )

            # Change ctm_id (UUID) to ctm_ids (UUID[])
            print("2. Converting ctm_id to ctm_ids array...")
            cur.execute(
                """
                ALTER TABLE titles_v3
                RENAME COLUMN ctm_id TO ctm_ids
            """
            )

            cur.execute(
                """
                ALTER TABLE titles_v3
                ALTER COLUMN ctm_ids TYPE UUID[]
                USING CASE
                    WHEN ctm_ids IS NULL THEN NULL
                    ELSE ARRAY[ctm_ids]
                END
            """
            )

            # Drop old index and create new one for array
            print("3. Updating indexes...")
            cur.execute(
                """
                DROP INDEX IF EXISTS idx_titles_v3_ctm
            """
            )

            cur.execute(
                """
                CREATE INDEX idx_titles_v3_ctm_ids
                ON titles_v3 USING GIN(ctm_ids)
            """
            )

            # Update column comment
            cur.execute(
                """
                COMMENT ON COLUMN titles_v3.ctm_ids IS
                'Array of CTM IDs this title belongs to. One CTM per (centroid, track, month) combination.'
            """
            )

            conn.commit()
            print("\nSuccessfully updated titles_v3!")
            print("- ctm_id -> ctm_ids (UUID[])")
            print("- Supports multiple CTMs per title")
            print("- Updated indexes for array queries")

        conn.close()
        return True

    except Exception as e:
        print(f"Update failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = update_schema()
    sys.exit(0 if success else 1)
