#!/usr/bin/env python3
"""
Strategic Feed Loader
Strategic Narrative Intelligence ETL Pipeline

Loads feeds from CSV configuration with regex filtering and validation.
Supports gradual rollout and quality control.
"""

import asyncio
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from etl_pipeline.core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StrategicFeedLoader:
    """Strategic feed loader with regex filtering and validation"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(
            project_root / "config" / "feeds" / "strategic_feeds.csv"
        )
        self.app_config = get_config()
        self.feeds = []
        self.stats = {
            "feeds_loaded": 0,
            "feeds_validated": 0,
            "feeds_failed": 0,
            "articles_processed": 0,
            "articles_allowed": 0,
            "articles_denied": 0,
        }

    def load_feed_config(self, limit: Optional[int] = None) -> List[Dict]:
        """Load feed configuration from CSV"""
        logger.info(f"Loading feed configuration from {self.config_path}")

        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Feed config file not found: {self.config_path}")

        feeds = []
        with open(self.config_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break

                # Clean and validate row
                feed_config = {
                    "source_name": row["source_name"].strip(),
                    "country": row["country"].strip(),
                    "language": row["language"].strip().lower(),
                    "section": row["section"].strip(),
                    "topic_tags": [tag.strip() for tag in row["topic_tags"].split("|")],
                    "rss_url": row["rss_url"].strip(),
                    "allow_regex": (
                        row["allow_regex"].strip()
                        if row["allow_regex"].strip() != "(.*)"
                        else None
                    ),
                    "deny_regex": (
                        row["deny_regex"].strip()
                        if row["deny_regex"].strip() != "(.*)"
                        else None
                    ),
                    "weight": float(row["weight"]),
                }

                feeds.append(feed_config)
                logger.debug(f"Loaded feed: {feed_config['source_name']}")

        self.feeds = feeds
        self.stats["feeds_loaded"] = len(feeds)
        logger.info(f"Loaded {len(feeds)} feed configurations")
        return feeds

    def validate_feed_url(self, feed_config: Dict) -> bool:
        """Validate RSS URL returns proper XML"""
        url = feed_config["rss_url"]
        source_name = feed_config["source_name"]

        try:
            logger.debug(f"Validating feed URL: {source_name}")

            # Check URL is reachable
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                logger.warning(
                    f"Feed URL returned {response.status_code}: {source_name}"
                )
                return False

            # Try to parse RSS
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {source_name}")
                return False

            # Check content type if available
            content_type = response.headers.get("content-type", "").lower()
            if content_type and "xml" not in content_type:
                logger.warning(
                    f"Content-Type is not XML: {source_name} ({content_type})"
                )
                # Don't fail on this - some feeds have incorrect content-type

            logger.debug(f"Feed validation successful: {source_name}")
            return True

        except Exception as e:
            logger.error(f"Feed validation failed for {source_name}: {e}")
            return False

    def apply_regex_filters(self, feed_config: Dict, entry) -> Tuple[bool, str]:
        """Apply allow/deny regex filters to entry"""
        source_name = feed_config["source_name"]
        allow_pattern = feed_config.get("allow_regex")
        deny_pattern = feed_config.get("deny_regex")

        # Get text to match against (title + link)
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        match_text = f"{title} {link}"

        # Apply deny filter first (exclusions)
        if deny_pattern:
            try:
                if re.search(deny_pattern, match_text, re.IGNORECASE):
                    return False, f"denied by pattern: {deny_pattern}"
            except re.error as e:
                logger.warning(
                    f"Invalid deny regex for {source_name}: {deny_pattern} ({e})"
                )

        # Apply allow filter (inclusions)
        if allow_pattern:
            try:
                if not re.search(allow_pattern, match_text, re.IGNORECASE):
                    return False, f"not matched by allow pattern: {allow_pattern}"
            except re.error as e:
                logger.warning(
                    f"Invalid allow regex for {source_name}: {allow_pattern} ({e})"
                )
                return False, f"invalid allow regex: {allow_pattern}"

        return True, "passed filters"

    async def validate_all_feeds(
        self, feeds: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Validate all feed URLs"""
        feeds_to_validate = feeds or self.feeds
        valid_feeds = []

        logger.info(f"Validating {len(feeds_to_validate)} feeds...")

        for feed_config in feeds_to_validate:
            if self.validate_feed_url(feed_config):
                valid_feeds.append(feed_config)
                self.stats["feeds_validated"] += 1
            else:
                self.stats["feeds_failed"] += 1
                logger.warning(f"Feed validation failed: {feed_config['source_name']}")

        logger.info(
            f"Feed validation complete: {len(valid_feeds)} valid, {self.stats['feeds_failed']} failed"
        )
        return valid_feeds

    async def process_feed_with_filters(
        self, feed_config: Dict, limit: int = 25
    ) -> Dict:
        """Process single feed with regex filtering"""
        source_name = feed_config["source_name"]
        url = feed_config["rss_url"]

        logger.info(f"Processing feed: {source_name}")

        try:
            # Parse RSS feed
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.warning(f"No entries in feed: {source_name}")
                return {"processed": 0, "allowed": 0, "denied": 0}

            processed = 0
            allowed = 0
            denied = 0

            for entry in feed.entries[:limit]:
                processed += 1
                self.stats["articles_processed"] += 1

                # Apply regex filters
                passes_filter, reason = self.apply_regex_filters(feed_config, entry)

                if passes_filter:
                    allowed += 1
                    self.stats["articles_allowed"] += 1
                    logger.debug(f"ALLOWED: {getattr(entry, 'title', '')[:60]}")
                else:
                    denied += 1
                    self.stats["articles_denied"] += 1
                    logger.debug(
                        f"DENIED ({reason}): {getattr(entry, 'title', '')[:60]}"
                    )

            feed_stats = {"processed": processed, "allowed": allowed, "denied": denied}
            logger.info(f"Feed stats for {source_name}: {feed_stats}")
            return feed_stats

        except Exception as e:
            logger.error(f"Error processing feed {source_name}: {e}")
            return {"processed": 0, "allowed": 0, "denied": 0}

    async def test_feeds(
        self, limit_feeds: Optional[int] = None, limit_articles: int = 10
    ) -> Dict:
        """Test feed loading and filtering (dry run)"""
        logger.info("=== STRATEGIC FEED LOADER TEST ===")

        # Load configuration
        feeds = self.load_feed_config(limit=limit_feeds)

        # Validate feeds
        valid_feeds = await self.validate_all_feeds(feeds)

        # Test processing with filters
        logger.info(f"Testing processing on {len(valid_feeds)} valid feeds...")

        for feed_config in valid_feeds:
            await self.process_feed_with_filters(feed_config, limit=limit_articles)

        # Generate report
        total_feeds = len(feeds)
        valid_count = len(valid_feeds)

        logger.info("=== TEST RESULTS ===")
        logger.info(f"Feeds loaded: {total_feeds}")
        logger.info(f"Feeds validated: {valid_count}")
        logger.info(f"Feeds failed: {total_feeds - valid_count}")
        logger.info(f"Articles processed: {self.stats['articles_processed']}")
        logger.info(f"Articles allowed: {self.stats['articles_allowed']}")
        logger.info(f"Articles denied: {self.stats['articles_denied']}")

        if self.stats["articles_processed"] > 0:
            allow_rate = (
                self.stats["articles_allowed"] / self.stats["articles_processed"]
            ) * 100
            logger.info(f"Filter pass rate: {allow_rate:.1f}%")

        return {
            "total_feeds": total_feeds,
            "valid_feeds": valid_count,
            "failed_feeds": total_feeds - valid_count,
            "articles_processed": self.stats["articles_processed"],
            "articles_allowed": self.stats["articles_allowed"],
            "articles_denied": self.stats["articles_denied"],
            "filter_pass_rate": (
                self.stats["articles_allowed"]
                / max(1, self.stats["articles_processed"])
            )
            * 100,
        }


async def main():
    """CLI interface for strategic feed loader"""
    import argparse

    parser = argparse.ArgumentParser(description="Strategic Feed Loader")
    parser.add_argument("--config", type=str, help="Path to feeds CSV file")
    parser.add_argument("--test", action="store_true", help="Test mode (dry run)")
    parser.add_argument(
        "--limit-feeds", type=int, help="Limit number of feeds to process"
    )
    parser.add_argument(
        "--limit-articles", type=int, default=10, help="Articles per feed (test mode)"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate feed URLs"
    )

    args = parser.parse_args()

    try:
        loader = StrategicFeedLoader(config_path=args.config)

        if args.validate_only:
            feeds = loader.load_feed_config(limit=args.limit_feeds)
            valid_feeds = await loader.validate_all_feeds(feeds)
            print(f"Validation complete: {len(valid_feeds)}/{len(feeds)} feeds valid")
            return 0

        if args.test:
            await loader.test_feeds(
                limit_feeds=args.limit_feeds, limit_articles=args.limit_articles
            )
            print("Test completed successfully")
            return 0

        print("Use --test for dry run or --validate-only for URL validation")
        return 1

    except Exception as e:
        logger.error(f"Strategic feed loader failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
