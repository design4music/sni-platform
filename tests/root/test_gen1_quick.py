#!/usr/bin/env python3
"""
Quick test of GEN-1 Event Family Assembly with fixed Framed Narrative generation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

from apps.gen1.processor import get_gen1_processor


async def test_gen1_quick():
    """Test GEN-1 processing with a small number of buckets"""
    logger.info("=== Quick GEN-1 Test (Fixed FN Generation) ===")
    
    processor = get_gen1_processor()
    
    # Process just 1 bucket with recent data to test FN generation
    result = await processor.process_event_families(
        since_hours=24,
        max_buckets=1, 
        min_bucket_size=2,
        dry_run=False  # Save to database to test full pipeline
    )
    
    logger.info("\n=== TEST RESULTS ===")
    logger.info(f"Event Families: {len(result.event_families)}")
    logger.info(f"Framed Narratives: {len(result.framed_narratives)}")
    logger.info(f"Success Rate: {result.success_rate:.1%}")
    logger.info(f"Processing Time: {result.processing_time_seconds:.1f}s")
    
    if result.errors:
        logger.error(f"Errors: {result.errors}")
    if result.warnings:
        logger.warning(f"Warnings: {result.warnings}")
    
    # Show Event Family details
    for i, ef in enumerate(result.event_families):
        logger.info(f"\nEvent Family {i+1}: {ef.title}")
        logger.info(f"  Confidence: {ef.confidence_score:.2f}")
        logger.info(f"  Source Titles: {len(ef.source_title_ids)}")
    
    # Show Framed Narrative details
    for i, fn in enumerate(result.framed_narratives):
        logger.info(f"\nFramed Narrative {i+1}: {fn.frame_type}")
        logger.info(f"  Stance: {fn.stance_summary}")
        logger.info(f"  Evidence Quality: {fn.evidence_quality:.2f}")
        logger.info(f"  Supporting Headlines: {len(fn.supporting_headlines)}")

if __name__ == "__main__":
    asyncio.run(test_gen1_quick())