#!/usr/bin/env python3
"""
GEN-1: Event Family Assembly Runner
CLI interface for running Event Family assembly and Framed Narrative generation
"""

import argparse
import asyncio
import sys
from datetime import datetime
from typing import Optional

from loguru import logger

from apps.gen1.processor import get_gen1_processor
from core.config import get_config
from core.database import check_database_connection


def setup_logging(verbose: bool = False):
    """Configure logging for GEN-1 runner"""
    log_level = "DEBUG" if verbose else "INFO"
    
    # Remove default logger
    logger.remove()
    
    # Add console logger with appropriate format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>GEN-1</cyan> | {message}",
        level=log_level,
        colorize=True,
    )
    
    # Add file logger for detailed tracking
    config = get_config()
    log_file = config.logs_dir / f"gen1_{datetime.now().strftime('%Y%m%d')}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | GEN-1 | {message}",
        level="DEBUG",
        rotation="1 day",
        retention="7 days",
    )


async def run_event_family_assembly(
    since_hours: int,
    min_bucket_size: int,
    max_buckets: Optional[int],
    dry_run: bool,
    summary_only: bool,
) -> bool:
    """
    Execute Event Family assembly pipeline
    
    Args:
        since_hours: How far back to look for buckets
        min_bucket_size: Minimum titles per bucket
        max_buckets: Maximum buckets to process
        dry_run: Don't save results to database
        summary_only: Show summary instead of processing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        processor = get_gen1_processor()
        
        if summary_only:
            logger.info("Generating GEN-1 processing summary...")
            summary = await processor.get_processing_summary(since_hours=24)
            
            print("\n" + "="*60)
            print("GEN-1 PROCESSING SUMMARY")
            print("="*60)
            
            # Core metrics
            print(f"Event Families (Total): {summary.get('event_families_total', 0)}")
            print(f"Event Families (24h): {summary.get('event_families_24h', 0)}")
            print(f"Framed Narratives (Total): {summary.get('framed_narratives_total', 0)}")
            print(f"Framed Narratives (24h): {summary.get('framed_narratives_24h', 0)}")
            print(f"Average Confidence Score: {summary.get('avg_confidence_score', 0):.3f}")
            
            # Configuration
            config_info = summary.get('config', {})
            print(f"\nConfiguration:")
            print(f"  Max buckets per batch: {config_info.get('max_buckets_per_batch', 'N/A')}")
            print(f"  Max Event Families per batch: {config_info.get('max_event_families_per_batch', 'N/A')}")
            print(f"  Max narratives per event: {config_info.get('max_narratives_per_event', 'N/A')}")
            
            print("\n" + "="*60)
            return True
        
        # Run full processing pipeline
        logger.info(
            f"Starting GEN-1 Event Family assembly",
            since_hours=since_hours,
            min_size=min_bucket_size,
            max_buckets=max_buckets,
            dry_run=dry_run,
        )
        
        result = await processor.process_event_families(
            since_hours=since_hours,
            min_bucket_size=min_bucket_size,
            max_buckets=max_buckets,
            dry_run=dry_run,
        )
        
        # Display results
        print("\n" + "="*60)
        print("GEN-1 PROCESSING RESULTS")
        print("="*60)
        print(f"Result: {result.summary}")
        print(f"Processing time: {result.processing_time_seconds:.1f} seconds")
        print(f"Success rate: {result.success_rate:.1%}")
        
        if result.event_families:
            print(f"\nEvent Families created:")
            for ef in result.event_families[:5]:  # Show first 5
                print(f"  - {ef.title} (confidence: {ef.confidence_score:.2f})")
            if len(result.event_families) > 5:
                print(f"  ... and {len(result.event_families) - 5} more")
        
        if result.framed_narratives:
            print(f"\nFramed Narratives generated:")
            for fn in result.framed_narratives[:5]:  # Show first 5
                print(f"  - {fn.frame_type}: {fn.frame_description[:60]}...")
            if len(result.framed_narratives) > 5:
                print(f"  ... and {len(result.framed_narratives) - 5} more")
        
        if result.errors:
            print(f"\nErrors encountered:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print(f"\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        print("\n" + "="*60)
        
        return len(result.errors) == 0
        
    except Exception as e:
        logger.error(f"GEN-1 processing failed: {e}")
        return False


async def check_system_readiness() -> bool:
    """
    Check if system is ready for GEN-1 processing
    
    Returns:
        True if system is ready, False otherwise
    """
    logger.info("Checking system readiness...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed")
        return False
    
    logger.info("Database connection: OK")
    
    # Check LLM configuration
    config = get_config()
    if not config.deepseek_api_key and not config.openai_api_key and not config.anthropic_api_key:
        logger.error("No LLM API keys configured")
        return False
    
    logger.info(f"LLM provider: {config.llm_provider}")
    
    # Check for required tables
    # This would check if CLUST-2 has created buckets and bucket_members tables
    logger.info("Required tables: OK (assumed)")
    
    logger.info("System readiness check passed")
    return True


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GEN-1: Event Family Assembly and Framed Narrative Generation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        default=72,
        help="How far back to look for buckets (hours)",
    )
    
    parser.add_argument(
        "--min-size",
        type=int,
        default=2,
        help="Minimum number of titles per bucket to process",
    )
    
    parser.add_argument(
        "--max-buckets",
        type=int,
        default=None,
        help="Maximum number of buckets to process (None for all)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process but don't save results to database",
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show processing summary instead of running pipeline",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check system readiness and exit",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logger.info("GEN-1: Event Family Assembly System")
    logger.info("=" * 40)
    
    async def main_async():
        try:
            # System readiness check
            if args.check:
                success = await check_system_readiness()
                return 0 if success else 1
            
            if not await check_system_readiness():
                logger.error("System readiness check failed")
                return 1
            
            # Run processing pipeline
            success = await run_event_family_assembly(
                since_hours=args.hours,
                min_bucket_size=args.min_size,
                max_buckets=args.max_buckets,
                dry_run=args.dry_run,
                summary_only=args.summary,
            )
            
            return 0 if success else 1
            
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return 1
    
    # Run async main
    exit_code = asyncio.run(main_async())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()