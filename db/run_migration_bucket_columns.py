"""
Run migration to add bucket columns to events_v3
"""

import os
import sys
from pathlib import Path

import psycopg2

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from core.config import config  # noqa: E402


def main():
    print("=" * 60)
    print("MIGRATION: Add bucket columns to events_v3")
    print("=" * 60)

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Step 1: Check current columns
            print("\nStep 1: Check current events_v3 columns")
            print("-" * 60)

            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'events_v3'
                ORDER BY ordinal_position
            """
            )

            for name, dtype in cur.fetchall():
                print(f"  {name}: {dtype}")

            # Step 2: Apply migration
            print("\nStep 2: Applying migration")
            print("-" * 60)

            migration_file = (
                Path(__file__).parent
                / "migrations"
                / "20260118_add_bucket_columns_to_events_v3.sql"
            )

            with open(migration_file, "r", encoding="utf-8") as f:
                migration_sql = f.read()

            cur.execute(migration_sql)
            conn.commit()
            print("Migration applied successfully")

            # Step 3: Verify new columns
            print("\nStep 3: Verify new columns")
            print("-" * 60)

            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'events_v3'
                ORDER BY ordinal_position
            """
            )

            for name, dtype in cur.fetchall():
                marker = " <-- NEW" if name in ("event_type", "bucket_key") else ""
                print(f"  {name}: {dtype}{marker}")

            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE")
            print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
