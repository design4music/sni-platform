"""Run database migration script"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def run_migration(migration_file: str):
    """Run a SQL migration file"""
    migration_path = Path(__file__).parent / "migrations" / migration_file

    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}")
        return False

    print(f"Running migration: {migration_file}")

    # Read migration SQL
    with open(migration_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Connect and execute
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
            cur.execute(sql)
            conn.commit()

        print("Migration completed successfully!")

        # Verify tables created
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name IN ('centroids_v3', 'taxonomy_v3', 'ctm', 'titles_v3')
                ORDER BY table_name
            """
            )
            tables = cur.fetchall()

            print("\nTables created:")
            for table in tables:
                print(f"  - {table[0]}")

        conn.close()
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_migration("20251103_create_sni_v3_tables.sql")
    sys.exit(0 if success else 1)
