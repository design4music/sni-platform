#!/usr/bin/env python3
"""
Test Phase 2: Direct title→EF assignment (bucketless architecture)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

from apps.generate.processor import Processor


async def test_phase2_processing():
    """Test new bucketless architecture with real strategic titles"""
    logger.info("=== TESTING PHASE 2: BUCKETLESS ARCHITECTURE ===")
    
    processor = Processor()
    
    # Test with small batch first
    logger.info("Testing with small batch (max 20 titles)...")
    result = await processor.process_strategic_titles(
        since_hours=72,
        max_titles=20,
        batch_size=20,
        dry_run=False
    )
    
    logger.info("Processing Result:")
    logger.info(f"  Titles processed: {result.titles_processed}")
    logger.info(f"  Event Families created: {result.event_families_created}")
    logger.info(f"  Framed Narratives created: {result.framed_narratives_created}")
    logger.info(f"  Processing time: {result.processing_time:.2f}s")
    
    if result.errors:
        logger.error(f"Errors encountered: {result.errors}")
        
    if result.event_families_created > 0:
        logger.info("SUCCESS: Phase 2 bucketless architecture working!")
        logger.info("Ready to process larger batches and remove bucket tables")
    else:
        logger.warning("No Event Families created - investigating...")
        
    return result

if __name__ == "__main__":
    asyncio.run(test_phase2_processing())