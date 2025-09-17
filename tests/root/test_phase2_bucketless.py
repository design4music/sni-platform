#!/usr/bin/env python3
"""
Phase 2 Bucketless Architecture Test
Tests direct title→EF processing without buckets
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

from apps.generate.database import get_gen1_database
from apps.generate.processor import get_gen1_processor
from core.database import check_database_connection


async def test_phase2_bucketless():
    """Test Phase 2 direct title→EF processing architecture"""
    
    logger.info("=== PHASE 2 BUCKETLESS ARCHITECTURE TEST ===")
    
    # Check database connection first
    logger.info("Checking database connection...")
    if not check_database_connection():
        logger.error("Database connection failed")
        return False
    logger.info("Database connection successful")
    
    # Get processor and database instances
    processor = get_gen1_processor()
    db = get_gen1_database()
    
    # Check current data status
    logger.info("Checking unassigned strategic titles...")
    titles = db.get_unassigned_strategic_titles(since_hours=72, limit=5)
    logger.info(f"Found {len(titles)} unassigned strategic titles for testing")
    
    if not titles:
        logger.warning("No unassigned strategic titles found - Phase 2 test cannot proceed")
        logger.info("Consider running CLUST-1 to generate strategic titles first")
        return True
    
    # Show sample titles
    logger.info("Sample unassigned titles:")
    for i, title in enumerate(titles[:3], 1):
        logger.info(f"  {i}. {title.get('title_display', 'N/A')[:60]}...")
        logger.info(f"     Publisher: {title.get('publisher_name', 'N/A')}")
        logger.info(f"     Date: {title.get('pubdate_utc', 'N/A')}")
    
    # Run Phase 2 processing with small batch
    logger.info("Starting Phase 2 direct title processing...")
    logger.info("Parameters: max_titles=10, batch_size=10, dry_run=False")
    
    result = await processor.process_strategic_titles(
        since_hours=72,
        max_titles=10,
        batch_size=10,
        dry_run=False
    )
    
    # Display results
    logger.info("=== PROCESSING RESULTS ===")
    logger.info(f"Titles processed: {result.titles_processed}")
    logger.info(f"Event Families created: {result.event_families_created}")
    logger.info(f"Framed Narratives created: {result.framed_narratives_created}")
    logger.info(f"Processing time: {result.processing_time:.2f}s")
    
    if result.errors:
        logger.error(f"Errors encountered: {len(result.errors)}")
        for error in result.errors[:3]:
            logger.error(f"  - {error}")
    
    # Validate success
    success = (
        result.event_families_created > 0 and
        result.framed_narratives_created > 0 and
        len(result.errors) == 0
    )
    
    if success:
        logger.success("✓ Phase 2 bucketless architecture working successfully!")
        logger.info("✓ Direct title→EF assignment functional")
        logger.info("✓ Event Families created without bucket dependency")
        logger.info("✓ Framed Narratives generated correctly")
        
        # Verify database updates
        updated_titles = db.get_unassigned_strategic_titles(since_hours=72, limit=5)
        logger.info(f"Remaining unassigned titles: {len(updated_titles)} (reduced by {len(titles) - len(updated_titles)})")
        
    else:
        logger.error("✗ Phase 2 test failed")
        if result.event_families_created == 0:
            logger.error("  No Event Families were created")
        if result.framed_narratives_created == 0:
            logger.error("  No Framed Narratives were created")
        if result.errors:
            logger.error(f"  {len(result.errors)} errors occurred")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(test_phase2_bucketless())
        
        if success:
            logger.success("Phase 2 bucketless architecture test PASSED")
            logger.info("Ready to proceed with bucket table cleanup")
        else:
            logger.error("Phase 2 bucketless architecture test FAILED")
            logger.warning("Do not proceed with bucket table cleanup until issues resolved")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.exception(f"Test script failed with exception: {e}")
        sys.exit(1)