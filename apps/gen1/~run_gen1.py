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




async def run_direct_title_processing(
    max_titles: Optional[int],
    batch_size: int,
    dry_run: bool,
    summary_only: bool,
) -> bool:
    """
    Execute direct title→Event Family processing pipeline (Phase 2)
    Simplified: Process ALL unassigned strategic titles (corpus-wide)

    Args:
        max_titles: Maximum titles to process (None for all)
        batch_size: Number of titles per batch
        dry_run: Don't save results to database
        summary_only: Show summary instead of processing

    Returns:
        True if successful, False otherwise
    """
    try:
        processor = get_gen1_processor()

        if summary_only:
            logger.info("Generating GEN-1 Direct Processing summary...")
            summary = await processor.get_processing_summary(since_hours=24)

            print("\n" + "=" * 60)
            print("GEN-1 DIRECT PROCESSING SUMMARY (Phase 2)")
            print("=" * 60)

            # Show statistics specific to direct processing
            print(
                f"Strategic Titles Available: {summary.get('strategic_titles_available', 'N/A')}"
            )
            print(
                f"Unassigned Strategic Titles: {summary.get('unassigned_strategic_titles', 'N/A')}"
            )
            print(f"Event Families (Total): {summary.get('event_families_total', 0)}")
            print(f"Event Families (24h): {summary.get('event_families_24h', 0)}")
            print(
                f"Average Confidence Score: {summary.get('avg_confidence_score', 0):.3f}"
            )

            print("\n" + "=" * 60)
            return True

        # Run direct title processing pipeline
        logger.info(
            "Starting GEN-1 Corpus-Wide Processing (Phase 2)",
            max_titles=max_titles,
            batch_size=batch_size,
            dry_run=dry_run,
        )

        result = await processor.process_strategic_titles(
            max_titles=max_titles,
            batch_size=batch_size,
            dry_run=dry_run,
        )

        # Display results
        print("\n" + "=" * 60)
        print("GEN-1 DIRECT PROCESSING RESULTS (Phase 2)")
        print("=" * 60)
        print(f"Result: {result.summary}")
        print(f"Processing time: {result.processing_time_seconds:.1f} seconds")
        print(f"Success rate: {result.success_rate:.1%}")

        if hasattr(result, "titles_processed"):
            print(f"Strategic titles processed: {result.titles_processed}")

        if result.event_families:
            print("\nEvent Families created:")
            for ef in result.event_families[:5]:  # Show first 5
                print(f"  - {ef.title} (confidence: {ef.confidence_score:.2f})")
            if len(result.event_families) > 5:
                print(f"  ... and {len(result.event_families) - 5} more")

        if result.framed_narratives:
            print("\nFramed Narratives generated:")
            for fn in result.framed_narratives[:5]:  # Show first 5
                print(f"  - {fn.frame_type}: {fn.frame_description[:60]}...")
            if len(result.framed_narratives) > 5:
                print(f"  ... and {len(result.framed_narratives) - 5} more")

        if result.errors:
            print("\nErrors encountered:")
            for error in result.errors:
                print(f"  - {error}")

        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 60)

        return len(result.errors) == 0

    except Exception as e:
        logger.error(f"GEN-1 direct processing failed: {e}")
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
    if (
        not config.deepseek_api_key
        and not config.openai_api_key
        and not config.anthropic_api_key
    ):
        logger.error("No LLM API keys configured")
        return False

    logger.info(f"LLM provider: {config.llm_provider}")

    # Check for required tables
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


    parser.add_argument(
        "--max-titles",
        type=int,
        default=None,
        help="Maximum titles to process in direct mode (None for corpus-wide processing)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for direct title processing",
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

            # Run direct title processing (only mode available)
            success = await run_direct_title_processing(
                max_titles=args.max_titles,
                batch_size=args.batch_size,
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
