#!/usr/bin/env python3
"""
Apply database migration for parent/child narratives
"""
from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def apply_migration():
    """Apply the parent/child narratives migration"""
    try:
        # Initialize database first
        config = get_config()
        initialize_database(config.database)
        print("Database initialized successfully")

        # Read migration SQL
        with open("database_migrations/001_add_parent_id_to_narratives.sql", "r") as f:
            migration_sql = f.read()

        print("Applying parent/child narratives migration...")

        with get_db_session() as session:
            # Execute migration
            session.execute(text(migration_sql))
            session.commit()
            print("Migration applied successfully!")

        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    apply_migration()
