#!/usr/bin/env python3
"""
Check table schema script
Inspects the current structure of event_families table
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


def check_table_schema():
    """Check current event_families table schema"""
    try:
        with get_db_session() as session:
            # Get table columns
            result = session.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'event_families'
                ORDER BY ordinal_position;
            """
                )
            )

            columns = result.fetchall()

            logger.info("Current event_families table schema:")
            for col in columns:
                logger.info(
                    f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})"
                )

            # Check if centroids table exists
            result = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_name = 'centroids';
            """
                )
            )

            centroids_exists = result.scalar() > 0
            logger.info(f"Centroids table exists: {centroids_exists}")

            if centroids_exists:
                result = session.execute(text("SELECT COUNT(*) FROM centroids"))
                count = result.scalar()
                logger.info(f"Centroids table row count: {count}")

    except Exception as e:
        logger.error(f"Error checking schema: {e}")


def main():
    """Main function"""
    # Initialize database connection
    init_database()

    # Check connection
    if not check_database_connection():
        logger.error("Database connection failed")
        sys.exit(1)

    check_table_schema()


if __name__ == "__main__":
    main()
