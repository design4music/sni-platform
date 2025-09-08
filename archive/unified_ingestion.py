#!/usr/bin/env python3
"""
Unified News Ingestion Runner
Strategic Narrative Intelligence ETL Pipeline

Orchestrates ingestion from multiple feed types using handler registry pattern.
Scalable design - adding new feed types requires only implementing a handler.
"""

import argparse
import logging
from typing import Dict

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.ingestion.db_utils import (add_sitemap_feed,
                                             get_pending_articles_count)
from etl_pipeline.ingestion.handlers import (get_handler,
                                             list_registered_handlers)
from etl_pipeline.ingestion.rss_handler import (  # noqa: F401
    GoogleRSSFeedHandler, RSSFeedHandler)
# Import handlers to register them
from etl_pipeline.ingestion.xml_sitemap_handler import \
    XMLSitemapHandler  # noqa: F401

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("unified_ingestion.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class UnifiedIngestionRunner:
    """
    Unified ingestion runner using handler registry pattern

    Supports any feed type with a registered handler.
    Easy to extend without modifying core logic.
    """

    def __init__(self):
        self.config = get_config()
        initialize_database(self.config.database)

    def run_all_feeds(
        self,
        hours_lookback: int = 24,
        only_type: str = None,
        limit_per_feed: int = 100,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """
        Run ingestion for all active feeds using their registered handlers

        Args:
            hours_lookback: Hours to look back for new content
            only_type: Only process feeds of this type (optional)
            limit_per_feed: Max articles per feed
            dry_run: Don't actually save articles

        Returns:
            Summary statistics by feed type
        """
        stats = {"total_new": 0, "total_duplicates": 0, "total_errors": 0}

        logger.info(
            f"Starting unified ingestion (lookback: {hours_lookback}h, limit: {limit_per_feed})"
        )

        if dry_run:
            logger.info("DRY RUN MODE - No articles will be saved")

        try:
            # Get all active feeds from database
            with get_db_session() as session:
                query = """
                    SELECT id, name, url, feed_type, priority, last_fetched_at
                    FROM news_feeds 
                    WHERE is_active = true
                """

                params = {}
                if only_type:
                    query += " AND feed_type = :feed_type"
                    params["feed_type"] = only_type

                query += " ORDER BY priority, name"

                result = session.execute(text(query), params)
                feeds = result.fetchall()

            if not feeds:
                logger.info("No active feeds found")
                return stats

            logger.info(f"Processing {len(feeds)} active feeds")

            # Process each feed using appropriate handler
            for feed_id, name, url, feed_type, priority, last_fetched_at in feeds:
                try:
                    # Get handler for feed type
                    handler = get_handler(feed_type)

                    logger.info(
                        f"Processing {feed_type} feed: {name} (priority: {priority})"
                    )

                    if not dry_run:
                        # Run ingestion
                        new, duplicates, errors = handler.ingest(
                            feed_id=str(feed_id),
                            feed_name=name,
                            feed_url=url,
                            last_fetched_at=last_fetched_at,
                            max_articles=limit_per_feed,
                        )
                    else:
                        # Dry run - just log what would be processed
                        logger.info(f"DRY RUN: Would process {feed_type} feed {name}")
                        new, duplicates, errors = 0, 0, 0

                    # Update statistics
                    key_prefix = feed_type.replace("_", "")  # xml_sitemap -> xmlsitemap
                    stats[f"{key_prefix}_new"] = stats.get(f"{key_prefix}_new", 0) + new
                    stats[f"{key_prefix}_duplicates"] = (
                        stats.get(f"{key_prefix}_duplicates", 0) + duplicates
                    )
                    stats[f"{key_prefix}_errors"] = (
                        stats.get(f"{key_prefix}_errors", 0) + errors
                    )

                    stats["total_new"] += new
                    stats["total_duplicates"] += duplicates
                    stats["total_errors"] += errors

                except ValueError as e:
                    if "No handler registered" in str(e):
                        logger.warning(
                            f"No handler for feed_type '{feed_type}', skipping {name}"
                        )
                        continue
                    else:
                        raise

                except Exception as e:
                    logger.error(f"Error processing feed {name}: {e}")
                    stats["total_errors"] += 1

            logger.info(f"Unified ingestion complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Unified ingestion failed: {e}")
            stats["total_errors"] += 1
            return stats

    def list_feeds(self) -> None:
        """List all feeds with their types and status"""
        try:
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                    SELECT name, url, feed_type, is_active, priority
                    FROM news_feeds
                    ORDER BY feed_type, priority, name
                """
                    )
                )

                feeds = result.fetchall()

                if not feeds:
                    print("No feeds found")
                    return

                print(f"Found {len(feeds)} feeds:")
                current_type = None

                for name, url, feed_type, is_active, priority in feeds:
                    if feed_type != current_type:
                        current_type = feed_type
                        print(f"\n{feed_type.upper()} feeds:")

                    status = "ACTIVE" if is_active else "INACTIVE"
                    print(f"  [{status}] {name} (Priority: {priority})")
                    print(f"    {url}")

        except Exception as e:
            logger.error(f"Error listing feeds: {e}")

    def add_xml_feed(self, name: str, sitemap_url: str, priority: int = 3) -> str:
        """Add XML sitemap feed to database"""
        try:
            feed_id = add_sitemap_feed(name, sitemap_url, priority)
            logger.info(f"Added XML sitemap feed: {name} (ID: {feed_id})")
            return feed_id
        except Exception as e:
            logger.error(f"Error adding XML feed: {e}")
            raise

    def show_status(self) -> None:
        """Show ingestion system status"""
        try:
            # Show registered handlers
            handlers = list_registered_handlers()
            print("Registered handlers:")
            for feed_type, handler_name in handlers.items():
                print(f"  {feed_type}: {handler_name}")

            # Show pending articles
            pending = get_pending_articles_count()
            print(f"\nPending enrichment: {pending} articles")

            # Show feed counts by type
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                    SELECT feed_type, COUNT(*) as count, 
                           COUNT(CASE WHEN is_active THEN 1 END) as active_count
                    FROM news_feeds
                    GROUP BY feed_type
                    ORDER BY feed_type
                """
                    )
                )

                feed_counts = result.fetchall()

                if feed_counts:
                    print("\nFeeds by type:")
                    for feed_type, total, active in feed_counts:
                        print(f"  {feed_type}: {active}/{total} active")

        except Exception as e:
            logger.error(f"Error showing status: {e}")


def main():
    """Command line interface for unified ingestion"""
    parser = argparse.ArgumentParser(description="Unified News Ingestion Runner")

    # Main operation flags
    parser.add_argument(
        "--run", action="store_true", help="Run ingestion for all feeds"
    )
    parser.add_argument("--list-feeds", action="store_true", help="List all feeds")
    parser.add_argument("--status", action="store_true", help="Show system status")

    # Ingestion options
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours to look back for new content"
    )
    parser.add_argument(
        "--only",
        help="Only process feeds of this type",
    )
    parser.add_argument(
        "--limit-per-feed", type=int, default=100, help="Max articles per feed"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without saving"
    )

    # Feed management
    parser.add_argument(
        "--add-xml-feed",
        nargs=3,
        metavar=("NAME", "URL", "PRIORITY"),
        help="Add XML sitemap feed (priority: 1-5)",
    )

    args = parser.parse_args()

    runner = UnifiedIngestionRunner()

    # Handle feed management commands
    if args.add_xml_feed:
        name, url, priority = args.add_xml_feed
        try:
            priority_int = int(priority)
            feed_id = runner.add_xml_feed(name, url, priority_int)
            print(f"Added XML feed: {name} (ID: {feed_id})")
        except ValueError:
            print("Priority must be an integer (1-5)")
        except Exception as e:
            print(f"Error adding feed: {e}")
        return

    # Handle info commands
    if args.list_feeds:
        runner.list_feeds()
        return

    if args.status:
        runner.show_status()
        return

    # Default action: run ingestion
    if not args.run and not any([args.list_feeds, args.status, args.add_xml_feed]):
        args.run = True

    if args.run:
        stats = runner.run_all_feeds(
            hours_lookback=args.hours,
            only_type=args.only,
            limit_per_feed=args.limit_per_feed,
            dry_run=args.dry_run,
        )

        print("\nIngestion Summary:")
        print(f"  New articles: {stats['total_new']}")
        print(f"  Duplicates: {stats['total_duplicates']}")
        print(f"  Errors: {stats['total_errors']}")

        # Show breakdown by feed type
        for key, value in stats.items():
            if key.endswith("_new") and value > 0:
                feed_type = key.replace("_new", "")
                print(f"  {feed_type.title()}: {value} new articles")


if __name__ == "__main__":
    main()
