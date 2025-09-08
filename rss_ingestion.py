#!/usr/bin/env python3
"""
Production RSS Ingestion System
Strategic Narrative Intelligence Platform

Production-grade RSS ingestion with comprehensive error handling,
logging, retry logic, and configuration management.
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import feedparser
import requests
from dateutil import parser as date_parser
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.database.models import (Article, FeedType, LanguageCode,
                                               NewsFeed)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("rss_ingestion.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ProductionRSSIngestion:
    """Production-grade RSS ingestion system"""

    def __init__(self, config_file: Optional[str] = None):
        self.config = get_config()
        self.feeds_config = self._load_feeds_config(config_file)
        self.session_timeout = 30
        self.max_retries = 3
        self.retry_delay = 5

    def _load_feeds_config(self, config_file: Optional[str]) -> List[Dict]:
        """Load RSS feeds configuration from file or use defaults"""
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")

        # Default feeds configuration
        return [
            # Western mainstream sources
            {
                "name": "BBC World News",
                "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
                "priority": 1,
            },
            {
                "name": "BBC Politics",
                "url": "http://feeds.bbci.co.uk/news/politics/rss.xml",
                "priority": 2,
            },
            {
                "name": "Reuters Top News",
                "url": "https://feeds.reuters.com/reuters/topNews",
                "priority": 1,
            },
            {
                "name": "Reuters World News",
                "url": "https://feeds.reuters.com/Reuters/worldNews",
                "priority": 2,
            },
            {
                "name": "NPR World",
                "url": "https://feeds.npr.org/1004/rss.xml",
                "priority": 2,
            },
            {
                "name": "The Guardian World",
                "url": "https://www.theguardian.com/world/rss",
                "priority": 2,
            },
            {
                "name": "The Guardian Politics",
                "url": "https://www.theguardian.com/politics/rss",
                "priority": 3,
            },
            # Alternative/Independent Western sources
            {
                "name": "Al Jazeera English",
                "url": "https://www.aljazeera.com/xml/rss/all.xml",
                "priority": 2,
            },
            {
                "name": "France24 English",
                "url": "https://www.france24.com/en/rss",
                "priority": 3,
            },
            {
                "name": "DW English",
                "url": "https://rss.dw.com/xml/rss-en-all",
                "priority": 3,
            },
            {"name": "Euronews", "url": "https://www.euronews.com/rss", "priority": 3},
            # Russian sources (geographic filtering applied)
            {
                "name": "TASS English",
                "url": "http://tass.com/rss/v2.xml",
                "priority": 1,
            },
            {
                "name": "Kremlin News",
                "url": "http://en.kremlin.ru/events/president/news/feed",
                "priority": 1,
            },
            # Chinese sources
            {
                "name": "Xinhua English",
                "url": "http://www.xinhuanet.com/english/rss/englishnews.xml",
                "priority": 2,
            },
            {
                "name": "Global Times",
                "url": "https://www.globaltimes.cn/rss/outbrain.xml",
                "priority": 3,
            },
            {
                "name": "CGTN",
                "url": "https://www.cgtn.com/subscribe/rss/section/world.xml",
                "priority": 3,
            },
            # Middle Eastern sources
            {
                "name": "Press TV",
                "url": "https://www.presstv.ir/rss.xml",
                "priority": 3,
            },
            # Indian sources
            {
                "name": "Times of India",
                "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                "priority": 3,
            },
            {
                "name": "The Hindu",
                "url": "https://www.thehindu.com/news/international/feeder/default.rss",
                "priority": 3,
            },
            # Additional sources
            {
                "name": "Japan Times",
                "url": "https://www.japantimes.co.jp/feed/",
                "priority": 3,
            },
            {
                "name": "South China Morning Post",
                "url": "https://www.scmp.com/rss/91/feed",
                "priority": 3,
            },
        ]

    async def run_ingestion(self, limit_per_feed: int = 25) -> Dict[str, int]:
        """
        Run production RSS ingestion

        Args:
            limit_per_feed: Maximum articles per feed

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting production RSS ingestion")
        start_time = time.time()

        try:
            # Initialize database
            initialize_database(self.config.database)
            logger.info("Database initialized successfully")

            # Process feeds by priority
            feeds_by_priority = {}
            for feed in self.feeds_config:
                priority = feed.get("priority", 3)
                if priority not in feeds_by_priority:
                    feeds_by_priority[priority] = []
                feeds_by_priority[priority].append(feed)

            stats = {
                "total_feeds": len(self.feeds_config),
                "successful_feeds": 0,
                "failed_feeds": 0,
                "total_articles": 0,
                "new_articles": 0,
                "duplicate_articles": 0,
                "errors": [],
            }

            # Process by priority (1 = highest, 3 = lowest)
            for priority in sorted(feeds_by_priority.keys()):
                logger.info(
                    f"Processing priority {priority} feeds ({len(feeds_by_priority[priority])} feeds)"
                )

                for feed_data in feeds_by_priority[priority]:
                    try:
                        feed_stats = await self._process_single_feed(
                            feed_data, limit_per_feed
                        )
                        stats["successful_feeds"] += 1
                        stats["total_articles"] += feed_stats["total_articles"]
                        stats["new_articles"] += feed_stats["new_articles"]
                        stats["duplicate_articles"] += feed_stats["duplicate_articles"]

                        logger.info(
                            f"[OK] {feed_data['name']}: {feed_stats['new_articles']} new articles"
                        )

                    except Exception as e:
                        stats["failed_feeds"] += 1
                        error_msg = f"Failed to process {feed_data['name']}: {str(e)}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg, exc_info=True)

            duration = time.time() - start_time
            logger.info(f"Ingestion completed in {duration:.2f}s")
            logger.info(
                f"Summary: {stats['new_articles']} new articles from {stats['successful_feeds']}/{stats['total_feeds']} feeds"
            )

            return stats

        except Exception as e:
            logger.error(f"RSS ingestion failed: {e}", exc_info=True)
            raise

    async def _process_single_feed(self, feed_data: Dict, limit: int) -> Dict[str, int]:
        """Process a single RSS feed with retry logic"""
        feed_name = feed_data["name"]
        feed_url = feed_data["url"]

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Processing {feed_name} (attempt {attempt + 1})")

                # Parse RSS feed with timeout
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    logger.warning(f"No entries found in {feed_name}")
                    return {
                        "total_articles": 0,
                        "new_articles": 0,
                        "duplicate_articles": 0,
                    }

                # Create or get feed in database
                feed_id = await self._get_or_create_feed(feed_name, feed_url)

                # Process entries
                stats = {
                    "total_articles": 0,
                    "new_articles": 0,
                    "duplicate_articles": 0,
                }

                for entry in feed.entries[:limit]:
                    try:
                        stats["total_articles"] += 1
                        if await self._save_article(entry, feed_id, feed_name):
                            stats["new_articles"] += 1
                        else:
                            stats["duplicate_articles"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to save article from {feed_name}: {e}")

                return stats

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {feed_name}: {e}. Retrying in {self.retry_delay}s..."
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

        raise Exception(f"All {self.max_retries} attempts failed for {feed_name}")

    async def _get_or_create_feed(self, name: str, url: str) -> str:
        """Get existing feed or create new one"""
        try:
            with get_db_session() as session:
                # Check if feed exists
                result = session.execute(
                    text("SELECT id FROM news_feeds WHERE url = :url"), {"url": url}
                )
                existing = result.fetchone()
                if existing:
                    return existing[0]

                # Create new feed
                feed_id = str(uuid.uuid4())
                session.execute(
                    text(
                        """
                    INSERT INTO news_feeds (id, name, url, feed_type, language, is_active, priority, fetch_interval_minutes, created_at)
                    VALUES (:id, :name, :url, :feed_type, :language, :is_active, :priority, :fetch_interval_minutes, :created_at)
                """
                    ),
                    {
                        "id": feed_id,
                        "name": name,
                        "url": url,
                        "feed_type": "RSS",
                        "language": "EN",
                        "is_active": True,
                        "priority": 5,
                        "fetch_interval_minutes": 60,
                        "created_at": datetime.utcnow(),
                    },
                )
                session.commit()
                logger.debug(f"Created new feed: {name}")
                return feed_id

        except SQLAlchemyError as e:
            logger.error(f"Database error creating feed {name}: {e}")
            raise

    async def _save_article(self, entry, feed_id: str, source_name: str) -> bool:
        """Save single article to database with comprehensive error handling"""
        try:
            with get_db_session() as session:
                # Check if article already exists
                result = session.execute(
                    text("SELECT id FROM articles WHERE url = :url"),
                    {"url": entry.link},
                )
                if result.fetchone():
                    return False  # Skip duplicate

                # Parse published date with multiple fallbacks
                published_at = datetime.utcnow()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6])
                    except (TypeError, ValueError):
                        pass
                elif hasattr(entry, "published") and entry.published:
                    try:
                        published_at = date_parser.parse(entry.published).replace(
                            tzinfo=None
                        )
                    except (ValueError, TypeError):
                        pass

                # Prepare article data with validation
                title = getattr(entry, "title", "Untitled")[:500]  # Limit title length
                content = getattr(entry, "summary", "")[:10000]  # Limit content length
                url = getattr(entry, "link", "")[:500]  # Limit URL length

                if not url:
                    logger.warning(f"Skipping article without URL from {source_name}")
                    return False

                # Create article
                article_id = str(uuid.uuid4())
                session.execute(
                    text(
                        """
                    INSERT INTO articles (id, feed_id, title, content, summary, url, published_at, 
                                        language, word_count, content_hash, title_hash, source_name, created_at)
                    VALUES (:id, :feed_id, :title, :content, :summary, :url, :published_at,
                            :language, :word_count, :content_hash, :title_hash, :source_name, :created_at)
                """
                    ),
                    {
                        "id": article_id,
                        "feed_id": feed_id,
                        "title": title,
                        "content": content,
                        "summary": content[:500] if content else "",
                        "url": url,
                        "published_at": published_at,
                        "language": "EN",
                        "word_count": len(content.split()) if content else 0,
                        "content_hash": str(hash(content + title)),
                        "title_hash": str(hash(title)),
                        "source_name": source_name,
                        "created_at": datetime.utcnow(),
                    },
                )
                session.commit()
                return True

        except SQLAlchemyError as e:
            logger.error(f"Database error saving article from {source_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving article from {source_name}: {e}")
            return False


# Production CLI interface
async def main():
    """Main entry point for production RSS ingestion"""
    import argparse

    parser = argparse.ArgumentParser(description="Production RSS Ingestion System")
    parser.add_argument("--config", type=str, help="RSS feeds configuration file")
    parser.add_argument("--limit", type=int, default=25, help="Articles per feed limit")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        ingestion = ProductionRSSIngestion(args.config)
        stats = await ingestion.run_ingestion(args.limit)

        print(f"\n=== Production RSS Ingestion Complete ===")
        print(f"Feeds processed: {stats['successful_feeds']}/{stats['total_feeds']}")
        print(f"Articles processed: {stats['total_articles']}")
        print(f"New articles: {stats['new_articles']}")
        print(f"Duplicates skipped: {stats['duplicate_articles']}")

        if stats["errors"]:
            print(f"Errors: {len(stats['errors'])}")
            for error in stats["errors"]:
                print(f"  - {error}")

        return 0 if stats["successful_feeds"] > 0 else 1

    except Exception as e:
        logger.error(f"Production ingestion failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
