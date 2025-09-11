#!/usr/bin/env python3
"""
Phase 2 Migration: Add EF assignment columns to titles table
"""

import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402


def add_ef_assignment_columns():
    """Add Event Family assignment columns to titles table"""
    logger.info("=== PHASE 2 MIGRATION: Adding EF Assignment Columns ===")

    with get_db_session() as session:
        # Add new columns for direct EF assignment
        migration_sql = """
        -- Add EF assignment columns to titles table
        ALTER TABLE titles ADD COLUMN IF NOT EXISTS event_family_id uuid REFERENCES event_families(id);
        ALTER TABLE titles ADD COLUMN IF NOT EXISTS ef_assignment_confidence real;
        ALTER TABLE titles ADD COLUMN IF NOT EXISTS ef_assignment_reason text;
        ALTER TABLE titles ADD COLUMN IF NOT EXISTS ef_assignment_at timestamp;
        
        -- Create indexes for efficient querying
        CREATE INDEX IF NOT EXISTS idx_titles_event_family_id ON titles(event_family_id);
        CREATE INDEX IF NOT EXISTS idx_titles_unassigned ON titles(gate_keep, event_family_id) 
            WHERE gate_keep = true AND event_family_id IS NULL;
        """

        logger.info("Executing migration SQL...")
        session.execute(text(migration_sql))

        logger.info("Migration completed successfully!")

        # Verify the new columns exist
        columns_check = session.execute(
            text(
                """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'titles' 
            AND column_name IN ('event_family_id', 'ef_assignment_confidence', 'ef_assignment_reason', 'ef_assignment_at')
            ORDER BY column_name
        """
            )
        ).fetchall()

        logger.info(
            f"Verified new columns: {[col.column_name for col in columns_check]}"
        )

        # Check counts
        total_titles = session.execute(text("SELECT COUNT(*) FROM titles")).scalar()
        strategic_titles = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE gate_keep = true")
        ).scalar()
        unassigned_strategic = session.execute(
            text(
                "SELECT COUNT(*) FROM titles WHERE gate_keep = true AND event_family_id IS NULL"
            )
        ).scalar()

        logger.info("Current Data Status:")
        logger.info(f"   Total titles: {total_titles}")
        logger.info(f"   Strategic titles: {strategic_titles}")
        logger.info(f"   Unassigned strategic titles: {unassigned_strategic}")

        logger.info("Ready for direct title->EF assignment!")


if __name__ == "__main__":
    add_ef_assignment_columns()
