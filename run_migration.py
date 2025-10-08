#!/usr/bin/env python3
"""Run database migration"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

from core.config import get_config


def run_migration(sql_file: str):
    """Run a SQL migration file"""
    config = get_config()
    engine = create_engine(config.database_url)

    # Read migration file
    migration_path = Path(sql_file)
    if not migration_path.exists():
        print(f"Error: Migration file not found: {sql_file}")
        sys.exit(1)

    sql_content = migration_path.read_text()

    # Execute migration
    print(f"Running migration: {migration_path.name}")
    try:
        with engine.connect() as conn:
            # Split by semicolons and execute each statement
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            for stmt in statements:
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        print("SUCCESS: Migration completed successfully")
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration("db/migrations/20251008_add_rai_analysis.sql")
