#!/usr/bin/env python3
"""
Simple SNI Migration Runner Script
Runs a specific migration file using SQLAlchemy directly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text

from core.database import (check_database_connection, get_db_session,
                           init_database)


def run_migration_sql(script_path: Path):
    """Run SQL migration script via SQLAlchemy"""
    try:
        with get_db_session() as session:
            sql_content = script_path.read_text()

            logger.info(f"Executing migration: {script_path.name}")

            # For migrations with BEGIN/COMMIT, we can execute the whole script
            # But let's be safe and split by statements if needed
            if "BEGIN;" in sql_content and "COMMIT;" in sql_content:
                # Execute as single transaction
                session.execute(text(sql_content))
            else:
                # Split by semicolon and execute each statement
                statements = [
                    stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
                ]

                for statement in statements:
                    if statement.strip():
                        session.execute(text(statement))

            logger.success(f"Migration completed successfully: {script_path.name}")
            return True

    except Exception as e:
        logger.error(f"Failed to execute migration: {e}")
        return False


def main():
    """Run migration"""
    if len(sys.argv) != 2:
        logger.error("Usage: python run_migration_simple.py <migration_file>")
        sys.exit(1)

    migration_file = Path(sys.argv[1])

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        sys.exit(1)

    logger.info(f"Running migration: {migration_file.name}")

    # Initialize database connection
    init_database()

    # Check connection
    if not check_database_connection():
        logger.error("Database connection failed")
        sys.exit(1)

    # Run migration
    if run_migration_sql(migration_file):
        logger.success("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
