"""Fix centroids_v3 constraint"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def fix_constraint():
    """Drop and recreate the constraint correctly"""
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
            # Check current constraint
            cur.execute(
                """
                SELECT conname, pg_get_constraintdef(oid) as definition
                FROM pg_constraint
                WHERE conrelid = 'centroids_v3'::regclass
                AND contype = 'c'
            """
            )
            constraints = cur.fetchall()

            print("Current constraints:")
            for name, definition in constraints:
                print(f"  {name}: {definition}")

            # Drop the problematic constraint
            print("\nDropping centroids_v3_check constraint...")
            cur.execute(
                "ALTER TABLE centroids_v3 DROP CONSTRAINT IF EXISTS centroids_v3_check"
            )

            # Recreate it correctly - the issue is likely with NULL handling
            print("Creating new constraint...")
            cur.execute(
                """
                ALTER TABLE centroids_v3 ADD CONSTRAINT centroids_v3_theater_check
                CHECK (
                    (class = 'geo' AND primary_theater IS NOT NULL) OR
                    (class = 'systemic')
                )
            """
            )

            conn.commit()
            print("Constraint fixed successfully!")

        conn.close()
        return True

    except Exception as e:
        print(f"Fix failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = fix_constraint()
    sys.exit(0 if success else 1)
