#!/usr/bin/env python3
"""
Generate 20 Event Families for detailed analysis
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

from apps.gen1.processor import get_gen1_processor


async def create_20_event_families():
    """Create 20 Event Families for analysis"""
    logger.info("=== Generating 20 Event Families for Analysis ===")
    
    processor = get_gen1_processor()
    
    # Process more buckets over a longer time period to get 20+ Event Families
    result = await processor.process_event_families(
        since_hours=240,  # 10 days back
        max_buckets=15,   # More buckets 
        min_bucket_size=2,
        dry_run=False     # Save to database for analysis
    )
    
    logger.info("\n=== GENERATION RESULTS ===")
    logger.info(f"Event Families Created: {len(result.event_families)}")
    logger.info(f"Framed Narratives: {len(result.framed_narratives)}")
    logger.info(f"Success Rate: {result.success_rate:.1%}")
    logger.info(f"Processing Time: {result.processing_time_seconds:.1f}s")
    
    if result.errors:
        logger.error(f"Errors: {result.errors}")
    if result.warnings:
        logger.warning(f"Warnings: {result.warnings}")
    
    # Display detailed analysis of Event Families
    logger.info("\n=== DETAILED EVENT FAMILY ANALYSIS ===")
    
    for i, ef in enumerate(result.event_families, 1):
        logger.info(f"\n--- Event Family {i} ---")
        logger.info(f"Title: {ef.title}")
        logger.info(f"Event Type: {ef.event_type}")
        logger.info(f"Geography: {ef.geography}")
        logger.info(f"Confidence: {ef.confidence_score:.2f}")
        logger.info(f"Key Actors: {', '.join(ef.key_actors)}")
        logger.info(f"Source Titles: {len(ef.source_title_ids)}")
        logger.info(f"Time Span: {ef.event_start} to {ef.event_end}")
        logger.info(f"Summary: {ef.summary[:150]}...")
        logger.info(f"Coherence Reason: {ef.coherence_reason[:100]}...")
    
    # Show statistics
    logger.info("\n=== EVENT FAMILY STATISTICS ===")
    
    # Event types distribution
    event_types = [ef.event_type for ef in result.event_families]
    type_counts = {}
    for et in event_types:
        type_counts[et] = type_counts.get(et, 0) + 1
    
    logger.info("Event Types:")
    for event_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {event_type}: {count}")
    
    # Geography distribution
    geographies = [ef.geography for ef in result.event_families if ef.geography]
    geo_counts = {}
    for geo in geographies:
        geo_counts[geo] = geo_counts.get(geo, 0) + 1
    
    logger.info("\nGeography Distribution:")
    for geography, count in sorted(geo_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {geography}: {count}")
    
    # Confidence distribution
    confidences = [ef.confidence_score for ef in result.event_families]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    high_confidence = len([c for c in confidences if c >= 0.8])
    medium_confidence = len([c for c in confidences if 0.6 <= c < 0.8])
    low_confidence = len([c for c in confidences if c < 0.6])
    
    logger.info("\nConfidence Analysis:")
    logger.info(f"  Average Confidence: {avg_confidence:.2f}")
    logger.info(f"  High (≥0.8): {high_confidence}")
    logger.info(f"  Medium (0.6-0.8): {medium_confidence}") 
    logger.info(f"  Low (<0.6): {low_confidence}")
    
    # Title count distribution
    title_counts = [len(ef.source_title_ids) for ef in result.event_families]
    avg_titles = sum(title_counts) / len(title_counts) if title_counts else 0
    single_title = len([c for c in title_counts if c == 1])
    multi_title = len([c for c in title_counts if c > 1])
    
    logger.info("\nTitle Count Analysis:")
    logger.info(f"  Average Titles per EF: {avg_titles:.1f}")
    logger.info(f"  Single-title EFs: {single_title}")
    logger.info(f"  Multi-title EFs: {multi_title}")
    logger.info(f"  Max titles in one EF: {max(title_counts) if title_counts else 0}")

if __name__ == "__main__":
    asyncio.run(create_20_event_families())