#!/usr/bin/env python3
"""
RSS Ingestion Driver for SNI-v2
Runs RSS ingestion across all active strategic feeds
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from apps.ingest.rss_fetcher import RSSFetcher
from core.checkpoint import get_checkpoint_manager
from core.config import get_config


class IngestionRunner:
    """RSS ingestion runner for all active feeds"""

    def __init__(self):
        self.config = get_config()
        self.engine = create_engine(self.config.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.fetcher = RSSFetcher()

        # Overall statistics
        self.stats = {
            "feeds_processed": 0,
            "feeds_success": 0,
            "feeds_errors": 0,
            "total_fetched": 0,
            "total_inserted": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "start_time": datetime.now(),
        }

    def get_active_feeds(self) -> List[Dict[str, Any]]:
        """Get all active feeds for ingestion"""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                SELECT id, url, name, source_domain, language_code
                FROM feeds 
                WHERE is_active = true
                ORDER BY priority DESC, name
            """
                )
            )

            return [
                {
                    "id": row.id,
                    "url": row.url,
                    "name": row.name,
                    "source_domain": row.source_domain,
                    "language_code": row.language_code,
                }
                for row in result.fetchall()
            ]

    def run_ingestion_batch(
        self, batch_size: int = None, resume: bool = False, max_feeds: int = None
    ) -> Dict[str, Any]:
        """
        Run RSS ingestion with batch processing and checkpoint support

        Args:
            batch_size: Number of feeds to process in this batch
            resume: Resume from last checkpoint
            max_feeds: Maximum feeds to process (for compatibility)

        Returns:
            Overall statistics
        """
        logger.info("Starting batch RSS ingestion with checkpoint support...")

        # Set up checkpoint manager
        checkpoint_manager = get_checkpoint_manager("p1_ingest")

        # Load checkpoint state
        checkpoint_state = checkpoint_manager.load_checkpoint() if resume else {}
        processed_count = checkpoint_state.get("processed_count", 0)
        last_feed_id = checkpoint_state.get("last_feed_id", None)

        if resume and checkpoint_state:
            logger.info(
                f"Resuming from checkpoint: {processed_count} feeds processed, last feed ID: {last_feed_id}"
            )

        # Get all active feeds
        feeds = self.get_active_feeds()

        # Filter feeds based on checkpoint if resuming
        if resume and last_feed_id:
            try:
                feed_ids = [feed["id"] for feed in feeds]
                last_index = feed_ids.index(last_feed_id)
                feeds_to_process = feeds[last_index + 1 :]
                logger.info(
                    f"Resuming after feed ID {last_feed_id}, {len(feeds_to_process)} feeds remaining"
                )
            except ValueError:
                feeds_to_process = feeds
                logger.warning(
                    f"Last processed feed ID {last_feed_id} not found, processing from start"
                )
        else:
            feeds_to_process = feeds

        # Apply batch limit
        batch_limit = batch_size or max_feeds
        if batch_limit and len(feeds_to_process) > batch_limit:
            feeds_to_process = feeds_to_process[:batch_limit]
            logger.info(
                f"Processing batch of {len(feeds_to_process)} feeds (batch size: {batch_limit})"
            )
        else:
            logger.info(f"Processing {len(feeds_to_process)} feeds")

        if not feeds_to_process:
            logger.info(
                "No feeds to process (all feeds already processed or empty batch)"
            )
            return self.stats

        # Process feeds one by one with checkpoint updates
        for i, feed in enumerate(feeds_to_process, 1):
            logger.info(
                f"Processing feed {i}/{len(feeds_to_process)}: {feed['name']} ({feed['source_domain']})"
            )

            try:
                # Run RSS fetch for this feed
                articles, feed_stats = self.fetcher.fetch_feed(feed["id"], feed["url"])

                # Update overall stats
                self.stats["feeds_processed"] += 1
                self.stats["feeds_success"] += 1
                self.stats["total_fetched"] += feed_stats.get("fetched", 0)
                self.stats["total_inserted"] += feed_stats.get("inserted", 0)
                self.stats["total_skipped"] += feed_stats.get("skipped", 0)
                self.stats["total_errors"] += feed_stats.get("errors", 0)

                logger.info(
                    f"Feed complete: {feed['name']} - "
                    f"fetched: {feed_stats.get('fetched', 0)}, "
                    f"inserted: {feed_stats.get('inserted', 0)}, "
                    f"skipped: {feed_stats.get('skipped', 0)}"
                )

                # Update checkpoint after each feed
                checkpoint_manager.update_progress(
                    processed_count=processed_count + self.stats["feeds_processed"],
                    last_feed_id=feed["id"],
                    total_success=self.stats["feeds_success"],
                    total_failed=self.stats["feeds_errors"],
                    total_inserted=self.stats["total_inserted"],
                )

            except Exception as e:
                logger.error(f"Feed processing failed: {feed['name']} - {e}")
                self.stats["feeds_processed"] += 1
                self.stats["feeds_errors"] += 1

                # Update checkpoint even on error
                checkpoint_manager.update_progress(
                    processed_count=processed_count + self.stats["feeds_processed"],
                    last_feed_id=feed["id"],
                    total_success=self.stats["feeds_success"],
                    total_failed=self.stats["feeds_errors"],
                    total_inserted=self.stats["total_inserted"],
                )
                continue

        # Clear checkpoint on successful completion (if not in batch mode)
        if batch_size is None:
            checkpoint_manager.clear_checkpoint()

        # Calculate final stats
        self.stats["end_time"] = datetime.now()
        self.stats["total_duration"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()

        self._log_summary()
        return self.stats

    def run_ingestion(self, max_feeds: int = None) -> Dict[str, Any]:
        """
        Run RSS ingestion across all active feeds

        Args:
            max_feeds: Maximum number of feeds to process (None for all)

        Returns:
            Overall statistics
        """
        logger.info("Starting RSS ingestion across all strategic feeds...")

        feeds = self.get_active_feeds()
        if max_feeds:
            feeds = feeds[:max_feeds]

        logger.info(f"Found {len(feeds)} active feeds to process")

        for i, feed in enumerate(feeds, 1):
            logger.info(
                f"Processing feed {i}/{len(feeds)}: {feed['name']} ({feed['source_domain']})"
            )

            try:
                # Run RSS fetch for this feed
                articles, feed_stats = self.fetcher.fetch_feed(feed["id"], feed["url"])

                # Update overall stats
                self.stats["feeds_processed"] += 1
                self.stats["feeds_success"] += 1
                self.stats["total_fetched"] += feed_stats.get("fetched", 0)
                self.stats["total_inserted"] += feed_stats.get("inserted", 0)
                self.stats["total_skipped"] += feed_stats.get("skipped", 0)
                self.stats["total_errors"] += feed_stats.get("errors", 0)

                logger.info(
                    f"Feed complete: {feed['name']} - "
                    f"fetched: {feed_stats.get('fetched', 0)}, "
                    f"inserted: {feed_stats.get('inserted', 0)}, "
                    f"skipped: {feed_stats.get('skipped', 0)}"
                )

            except Exception as e:
                logger.error(f"Feed processing failed: {feed['name']} - {e}")
                self.stats["feeds_processed"] += 1
                self.stats["feeds_errors"] += 1
                continue

        # Calculate final stats
        self.stats["end_time"] = datetime.now()
        self.stats["total_duration"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()

        self._log_summary()
        return self.stats

    def _log_summary(self):
        """Log ingestion summary statistics"""
        stats = self.stats
        logger.info("=== RSS INGESTION SUMMARY ===")
        logger.info(f"Feeds processed: {stats['feeds_processed']}")
        logger.info(f"Feeds success: {stats['feeds_success']}")
        logger.info(f"Feeds errors: {stats['feeds_errors']}")
        logger.info(f"Total articles fetched: {stats['total_fetched']}")
        logger.info(f"Total articles inserted: {stats['total_inserted']}")
        logger.info(f"Total articles skipped: {stats['total_skipped']}")
        logger.info(f"Total processing errors: {stats['total_errors']}")
        logger.info(f"Total duration: {stats['total_duration']:.1f}s")

        if stats["feeds_processed"] > 0:
            success_rate = (stats["feeds_success"] / stats["feeds_processed"]) * 100
            logger.info(f"Feed success rate: {success_rate:.1f}%")

        if stats["total_fetched"] > 0:
            insert_rate = (stats["total_inserted"] / stats["total_fetched"]) * 100
            logger.info(f"Article insert rate: {insert_rate:.1f}%")


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="RSS Ingestion Runner")
    parser.add_argument(
        "--max-feeds",
        type=int,
        default=None,
        help="Maximum feeds to process (default: all)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        help="Process feeds in batches of this size (resumable)",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show current database summary and exit"
    )

    args = parser.parse_args()

    runner = IngestionRunner()

    if args.summary:
        with runner.Session() as session:
            # Feed counts
            feed_result = session.execute(
                text(
                    """
                SELECT 
                    COUNT(*) as total_feeds,
                    COUNT(*) FILTER (WHERE is_active = true) as active_feeds
                FROM feeds
            """
                )
            )
            feed_row = feed_result.fetchone()

            # Title counts
            title_result = session.execute(
                text(
                    """
                SELECT 
                    COUNT(*) as total_titles,
                    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_titles,
                    COUNT(*) FILTER (WHERE processing_status = 'gated') as gated_titles
                FROM titles
            """
                )
            )
            title_row = title_result.fetchone()

            print("Database Summary:")
            print(f"  Feeds: {feed_row.active_feeds}/{feed_row.total_feeds} active")
            print(
                f"  Titles: {title_row.total_titles} total, {title_row.pending_titles} pending, {title_row.gated_titles} gated"
            )
        return

    # Run ingestion
    try:
        # Use batch processing if --batch or --resume flags are provided
        if args.batch is not None or args.resume:
            stats = runner.run_ingestion_batch(
                batch_size=args.batch, resume=args.resume, max_feeds=args.max_feeds
            )
        else:
            stats = runner.run_ingestion(max_feeds=args.max_feeds)

        # Print automation-friendly summary
        print(
            f"INGESTION_RESULT: {stats['feeds_success']}/{stats['feeds_processed']} feeds success, "
            f"{stats['total_inserted']} articles inserted, {stats['total_skipped']} skipped"
        )

        # Exit with appropriate code
        sys.exit(0 if stats["feeds_errors"] == 0 else 1)

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
