#!/usr/bin/env python3
"""
SNI Migration Runner Script
Runs a specific migration file
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from core.database import (check_database_connection, init_database)
from scripts.setup_database import run_sql_script


def main():
    """Run migration"""
    if len(sys.argv) != 2:
        logger.error("Usage: python run_migration.py <migration_file>")
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
    if run_sql_script(migration_file):
        logger.success(f"Migration completed successfully: {migration_file.name}")
    else:
        logger.error(f"Migration failed: {migration_file.name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
