#!/usr/bin/env python3
"""
Execute Migration 005: EF Context Enhancement
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session


def run_migration():
    """Execute the EF context enhancement migration"""

    migration_file = (
        project_root / "db" / "migrations" / "005_ef_context_enhancement.sql"
    )

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    # Read migration SQL
    with open(migration_file, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    logger.info("Starting EF context enhancement migration...")

    try:
        with get_db_session() as session:
            # Execute the migration
            session.execute(text(migration_sql))
            session.commit()

        logger.success("Migration 005 completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
