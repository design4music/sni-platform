"""Update titles_v3 to support multiple centroids per title"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def update_schema():
    """Change centroid_id to centroid_ids array"""
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
            print("Updating titles_v3 to support multiple centroids...")

            # Drop the foreign key constraint first
            print("1. Dropping foreign key constraint...")
            cur.execute(
                """
                ALTER TABLE titles_v3
                DROP CONSTRAINT IF EXISTS titles_v3_centroid_id_fkey
            """
            )

            # Change centroid_id (TEXT) to centroid_ids (TEXT[])
            print("2. Converting centroid_id to centroid_ids array...")
            cur.execute(
                """
                ALTER TABLE titles_v3
                RENAME COLUMN centroid_id TO centroid_ids
            """
            )

            cur.execute(
                """
                ALTER TABLE titles_v3
                ALTER COLUMN centroid_ids TYPE TEXT[]
                USING CASE
                    WHEN centroid_ids IS NULL THEN NULL
                    ELSE ARRAY[centroid_ids]
                END
            """
            )

            # Drop old index and create new one for array
            print("3. Updating indexes...")
            cur.execute(
                """
                DROP INDEX IF EXISTS idx_titles_v3_centroid
            """
            )

            cur.execute(
                """
                CREATE INDEX idx_titles_v3_centroid_ids
                ON titles_v3 USING GIN(centroid_ids)
            """
            )

            # Update composite index
            cur.execute(
                """
                DROP INDEX IF EXISTS idx_titles_v3_month_centroid_track
            """
            )

            cur.execute(
                """
                CREATE INDEX idx_titles_v3_month_centroids_track
                ON titles_v3 USING GIN(centroid_ids)
                WHERE centroid_ids IS NOT NULL AND track IS NOT NULL
            """
            )

            # Update column comment
            cur.execute(
                """
                COMMENT ON COLUMN titles_v3.centroid_ids IS
                'Array of centroid IDs this title belongs to. NULL = out of scope. Can belong to multiple centroids.'
            """
            )

            conn.commit()
            print("\nSuccessfully updated titles_v3!")
            print("- centroid_id → centroid_ids (TEXT[])")
            print("- Supports multiple centroids per title")
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
