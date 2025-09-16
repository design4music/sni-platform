#!/usr/bin/env python3
"""
Phase 1: EF Key Schema Migration
- Rename geography → primary_theater
- Add ef_key, status, merging fields
- Add enum constraints for event_type and primary_theater
- Create performance indexes
"""

import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session


def run_migration():
    """Execute Phase 1 schema migration"""
    logger.info("=== PHASE 1 MIGRATION: EF KEY SCHEMA ===")
    
    with get_db_session() as session:
        # Step 1: Rename geography to primary_theater
        logger.info("Step 1: Renaming geography → primary_theater")
        session.execute(text("""
            ALTER TABLE event_families 
            RENAME COLUMN geography TO primary_theater
        """))
        
        # Step 2: Add new columns for ef_key system
        logger.info("Step 2: Adding ef_key and merge tracking columns")
        session.execute(text("""
            ALTER TABLE event_families 
            ADD COLUMN ef_key VARCHAR(64) NULL,
            ADD COLUMN status VARCHAR(20) DEFAULT 'active',
            ADD COLUMN merged_into UUID NULL,
            ADD COLUMN merge_rationale TEXT NULL
        """))
        
        # Step 3: Add event_type enum constraint
        logger.info("Step 3: Adding event_type enum constraint")
        valid_event_types = [
            'Strategy/Tactics', 'Humanitarian', 'Alliances/Geopolitics',
            'Diplomacy/Negotiations', 'Sanctions/Economy', 'Domestic Politics',
            'Procurement/Force-gen', 'Tech/Cyber/OSINT', 'Legal/ICC',
            'Information/Media/Platforms', 'Energy/Infrastructure'
        ]
        event_type_constraint = "', '".join(valid_event_types)
        
        session.execute(text(f"""
            ALTER TABLE event_families 
            ADD CONSTRAINT chk_event_type 
            CHECK (event_type IN ('{event_type_constraint}'))
        """))
        
        # Step 4: Add primary_theater enum constraint (including new LATAM_REGIONAL)
        logger.info("Step 4: Adding primary_theater enum constraint")
        valid_theaters = [
            'UKRAINE', 'GAZA', 'TAIWAN_STRAIT', 'IRAN_NUCLEAR', 'EUROPE_SECURITY',
            'US_DOMESTIC', 'CHINA_TRADE', 'MEAST_REGIONAL', 'CYBER_GLOBAL',
            'CLIMATE_GLOBAL', 'AFRICA_SECURITY', 'KOREA_PENINSULA', 
            'LATAM_REGIONAL', 'ARCTIC', 'GLOBAL_SUMMIT'
        ]
        theater_constraint = "', '".join(valid_theaters)
        
        session.execute(text(f"""
            ALTER TABLE event_families 
            ADD CONSTRAINT chk_primary_theater 
            CHECK (primary_theater IN ('{theater_constraint}'))
        """))
        
        # Step 5: Create performance indexes
        logger.info("Step 5: Creating performance indexes")
        
        # Unique index for ef_key on active EFs only
        session.execute(text("""
            CREATE UNIQUE INDEX idx_ef_key_active 
            ON event_families(ef_key) 
            WHERE status = 'active'
        """))
        
        # Index for theater+type lookups (for Pass 2A merging)
        session.execute(text("""
            CREATE INDEX idx_theater_type_active 
            ON event_families(primary_theater, event_type) 
            WHERE status = 'active'
        """))
        
        # Index for status lookups
        session.execute(text("""
            CREATE INDEX idx_status 
            ON event_families(status)
        """))
        
        # Step 6: Set all existing EFs to active status
        logger.info("Step 6: Setting existing Event Families to active status")
        result = session.execute(text("""
            UPDATE event_families 
            SET status = 'active' 
            WHERE status IS NULL
        """))
        logger.info(f"Updated {result.rowcount} Event Families to active status")
        
        session.commit()
        logger.info("✅ Phase 1 migration completed successfully!")


def verify_migration():
    """Verify the migration was successful"""
    logger.info("=== VERIFYING MIGRATION ===")
    
    with get_db_session() as session:
        # Check column exists
        columns_result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'event_families' 
            AND column_name IN ('primary_theater', 'ef_key', 'status', 'merged_into', 'merge_rationale')
        """)).fetchall()
        
        columns_found = [row.column_name for row in columns_result]
        expected_columns = ['primary_theater', 'ef_key', 'status', 'merged_into', 'merge_rationale']
        
        logger.info(f"Columns found: {columns_found}")
        if all(col in columns_found for col in expected_columns):
            logger.info("✅ All expected columns present")
        else:
            missing = [col for col in expected_columns if col not in columns_found]
            logger.error(f"❌ Missing columns: {missing}")
        
        # Check indexes
        indexes_result = session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'event_families' 
            AND indexname IN ('idx_ef_key_active', 'idx_theater_type_active', 'idx_status')
        """)).fetchall()
        
        indexes_found = [row.indexname for row in indexes_result]
        expected_indexes = ['idx_ef_key_active', 'idx_theater_type_active', 'idx_status']
        
        logger.info(f"Indexes found: {indexes_found}")
        if all(idx in indexes_found for idx in expected_indexes):
            logger.info("✅ All expected indexes present")
        else:
            missing_idx = [idx for idx in expected_indexes if idx not in indexes_found]
            logger.error(f"❌ Missing indexes: {missing_idx}")
        
        # Check constraints
        constraints_result = session.execute(text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conname IN ('chk_event_type', 'chk_primary_theater')
        """)).fetchall()
        
        constraints_found = [row.conname for row in constraints_result]
        logger.info(f"Constraints found: {constraints_found}")
        
        # Check sample data
        sample_result = session.execute(text("""
            SELECT id, primary_theater, event_type, status, ef_key 
            FROM event_families 
            LIMIT 3
        """)).fetchall()
        
        logger.info("Sample Event Families after migration:")
        for row in sample_result:
            logger.info(f"  ID: {row.id}, Theater: {row.primary_theater}, Type: {row.event_type}, Status: {row.status}, EF_Key: {row.ef_key}")


def main():
    """Main entry point"""
    try:
        run_migration()
        verify_migration()
        logger.info("🎉 Phase 1 migration completed and verified!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()