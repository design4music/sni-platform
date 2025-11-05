"""Rename centroids_v3.is_superpower to is_macro"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def rename_column():
    """Rename is_superpower to is_macro"""
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
            print("Renaming centroids_v3.is_superpower to is_macro...")

            # Rename the column
            cur.execute(
                """
                ALTER TABLE centroids_v3
                RENAME COLUMN is_superpower TO is_macro
            """
            )

            # Drop old index and create new one with updated name
            cur.execute(
                """
                DROP INDEX IF EXISTS idx_centroids_v3_superpower
            """
            )

            cur.execute(
                """
                CREATE INDEX idx_centroids_v3_macro
                ON centroids_v3(is_macro)
                WHERE is_macro = true
            """
            )

            # Update column comment
            cur.execute(
                """
                COMMENT ON COLUMN centroids_v3.is_macro IS
                'Flag for US/EU/CN/RU macro centroids used in Pass 3'
            """
            )

            conn.commit()
            print("Successfully renamed is_superpower to is_macro")

        conn.close()
        return True

    except Exception as e:
        print(f"Rename failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = rename_column()
    sys.exit(0 if success else 1)
