#!/usr/bin/env python3
"""
Test Phase 1 Prompt Improvements
Compare fragmentation before/after the updated Event Family prompts
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

from apps.gen1.processor import get_gen1_processor


async def test_phase1_fragmentation_reduction():
    """Test Phase 1 prompt improvements for reduced fragmentation"""
    logger.info("=== TESTING PHASE 1: PROMPT IMPROVEMENTS ===")
    logger.info("Expected: Fewer, broader Event Families (2-3 instead of 7+)")
    
    processor = get_gen1_processor()
    
    # Use moderate settings to avoid timeouts while testing fragmentation
    result = await processor.process_event_families(
        since_hours=240,  # 10 days back (same as before)
        max_buckets=8,    # Smaller batch to avoid timeouts
        min_bucket_size=2,
        dry_run=False     # Save to database for comparison
    )
    
    logger.info("\n=== PHASE 1 TEST RESULTS ===")
    logger.info(f"Event Families Created: {len(result.event_families)}")
    logger.info("Expected Reduction: Should be 2-3 broad EFs instead of 7+ fragmented ones")
    logger.info(f"Framed Narratives: {len(result.framed_narratives)}")
    logger.info(f"Success Rate: {result.success_rate:.1%}")
    logger.info(f"Processing Time: {result.processing_time_seconds:.1f}s")
    
    if result.errors:
        logger.error(f"Errors: {result.errors}")
    if result.warnings:
        logger.warning(f"Warnings: {result.warnings}")
    
    # Analyze Event Family coherence
    logger.info("\n=== EVENT FAMILY COHERENCE ANALYSIS ===")
    
    for i, ef in enumerate(result.event_families, 1):
        logger.info(f"\n--- Event Family {i}: COHERENCE CHECK ---")
        logger.info(f"Title: {ef.title}")
        logger.info(f"Type: {ef.event_type}")
        logger.info(f"Key Actors: {', '.join(ef.key_actors)}")
        logger.info(f"Geography: {ef.geography}")
        logger.info(f"Confidence: {ef.confidence_score:.2f}")
        logger.info(f"Source Titles: {len(ef.source_title_ids)}")
        
        # Check for broader thematic coherence
        if len(ef.source_title_ids) >= 3:
            coherence_level = "GOOD - Multiple titles unified"
        elif len(ef.source_title_ids) == 2:
            coherence_level = "MODERATE - Pair unified"  
        else:
            coherence_level = "FRAGMENTED - Single title EF"
            
        logger.info(f"Coherence Assessment: {coherence_level}")
        logger.info(f"Summary: {ef.summary[:200]}...")
        logger.info(f"Coherence Reason: {ef.coherence_reason[:150]}...")
    
    # Overall fragmentation assessment
    logger.info("\n=== FRAGMENTATION ASSESSMENT ===")
    
    single_title_efs = len([ef for ef in result.event_families if len(ef.source_title_ids) == 1])
    multi_title_efs = len([ef for ef in result.event_families if len(ef.source_title_ids) > 1])
    avg_titles_per_ef = sum(len(ef.source_title_ids) for ef in result.event_families) / len(result.event_families) if result.event_families else 0
    
    logger.info(f"Total Event Families: {len(result.event_families)}")
    logger.info(f"Single-title EFs (fragmented): {single_title_efs}")
    logger.info(f"Multi-title EFs (coherent): {multi_title_efs}")
    logger.info(f"Average titles per EF: {avg_titles_per_ef:.1f}")
    
    # Assessment
    if len(result.event_families) <= 4 and multi_title_efs >= 2:
        assessment = "SUCCESS - Reduced fragmentation achieved"
    elif len(result.event_families) <= 6:
        assessment = "PARTIAL - Some improvement in fragmentation"
    else:
        assessment = "INSUFFICIENT - Still too fragmented"
        
    logger.info(f"Phase 1 Assessment: {assessment}")
    
    # Show thematic diversity
    logger.info("\n=== THEMATIC DIVERSITY CHECK ===")
    event_types = [ef.event_type for ef in result.event_families]
    geographies = [ef.geography for ef in result.event_families if ef.geography]
    
    logger.info(f"Event Types: {', '.join(set(event_types))}")
    logger.info(f"Geographic Spread: {', '.join(set(geographies))}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_phase1_fragmentation_reduction())