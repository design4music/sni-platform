"""
RSS Feed Ingestion Tasks for Strategic Narrative Intelligence

This module implements the RSS feed ingestion tasks that populate the raw_articles table
with news content from configured feeds. Uses the news_feeds_config.json for source data.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
from langdetect import LangDetectError, detect
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ...ingestion.base import IngestionResult, RawArticle
from ...ingestion.rss_ingestion import GoogleNewsRSSSource, RSSIngestionSource
from ..database import get_db_session
from ..database.models import Article, NewsSource
from ..exceptions import RetryableError, TaskError
from .celery_app import celery_app

logger = structlog.get_logger(__name__)


class FeedIngestionManager:
    """Manages RSS feed ingestion with deduplication and error handling"""

    def __init__(self):
        self.config_path = (
            Path(__file__).parent.parent.parent.parent / "news_feeds_config.json"
        )
        self.feeds_config = self._load_feeds_config()
        self.session_timeout = aiohttp.ClientTimeout(total=30)

    def _load_feeds_config(self) -> Dict[str, Any]:
        """Load feed configuration from JSON file"""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            logger.info(
                "Feed configuration loaded",
                feeds_count=len(
                    config.get("strategic_news_feeds", {}).get("feeds", [])
                ),
            )
            return config
        except Exception as exc:
            logger.error(
                "Failed to load feed configuration",
                config_path=str(self.config_path),
                error=str(exc),
            )
            raise TaskError(f"Cannot load feed configuration: {exc}")

    async def ingest_single_feed(self, feed_config: Dict[str, Any]) -> IngestionResult:
        """Ingest articles from a single RSS feed"""
        start_time = datetime.now()

        try:
            # Initialize RSS source based on source type
            source_type = feed_config.get("source_type", "rss")
            if source_type == "google_rss":
                rss_source = GoogleNewsRSSSource(feed_config)
            else:
                rss_source = RSSIngestionSource(feed_config)

            # Fetch articles from RSS feed
            articles = []
            async for raw_article in rss_source.fetch_articles():
                # Process and validate article
                processed_article = await self._process_raw_article(
                    raw_article, feed_config
                )
                if processed_article:
                    articles.append(processed_article)

            # Store articles in database
            stored_count, failed_count, errors = await self._store_articles(
                articles, feed_config
            )

            duration = (datetime.now() - start_time).total_seconds()

            return IngestionResult(
                success=True,
                items_fetched=len(articles),
                items_processed=stored_count,
                items_failed=failed_count,
                errors=errors,
                duration_seconds=duration,
                metadata={
                    "feed_name": feed_config.get("name"),
                    "feed_url": feed_config.get("url"),
                    "category": feed_config.get("category"),
                },
            )

        except Exception as exc:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                "Feed ingestion failed",
                feed_name=feed_config.get("name"),
                feed_url=feed_config.get("url"),
                error=str(exc),
            )

            return IngestionResult(
                success=False,
                items_fetched=0,
                items_processed=0,
                items_failed=0,
                errors=[str(exc)],
                duration_seconds=duration,
                metadata={"feed_name": feed_config.get("name")},
            )

    async def _process_raw_article(
        self, raw_article: RawArticle, feed_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process and validate a raw article before storage"""
        try:
            # Generate content hash for deduplication
            content_for_hash = f"{raw_article.title}{raw_article.url}"
            content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()

            # Detect language if not provided
            language_code = raw_article.language or feed_config.get("language", "en")
            if not language_code or language_code == "auto":
                try:
                    detected_lang = detect(
                        raw_article.title + " " + (raw_article.content or "")
                    )
                    language_code = detected_lang[:2]  # Take first 2 chars
                except LangDetectError:
                    language_code = "en"  # Default fallback

            # Calculate word count
            word_count = 0
            if raw_article.content:
                word_count = len(raw_article.content.split())

            # Apply quality filters
            ingestion_config = self.feeds_config.get("ingestion_config", {})
            quality_filters = ingestion_config.get("quality_filtering", {})

            # Check minimum word count
            min_words = quality_filters.get("min_word_count", 50)
            if word_count < min_words:
                logger.debug(
                    "Article filtered out - too short",
                    title=raw_article.title[:100],
                    word_count=word_count,
                )
                return None

            # Check maximum word count
            max_words = quality_filters.get("max_word_count", 10000)
            if word_count > max_words:
                logger.debug(
                    "Article filtered out - too long",
                    title=raw_article.title[:100],
                    word_count=word_count,
                )
                return None

            # Check for excluded keywords
            exclude_keywords = quality_filters.get("exclude_keywords", [])
            title_lower = raw_article.title.lower()
            if any(keyword.lower() in title_lower for keyword in exclude_keywords):
                logger.debug(
                    "Article filtered out - excluded keyword",
                    title=raw_article.title[:100],
                )
                return None

            return {
                "title": raw_article.title,
                "content": raw_article.content,
                "summary": raw_article.summary,
                "url": raw_article.url,
                "author": raw_article.author,
                "published_at": raw_article.published_at or datetime.now(timezone.utc),
                "language_code": language_code,
                "word_count": word_count,
                "content_hash": content_hash,
                "title_hash": hashlib.sha256(raw_article.title.encode()).hexdigest(),
                "feed_config": feed_config,
            }

        except Exception as exc:
            logger.error(
                "Failed to process raw article",
                title=raw_article.title[:100],
                error=str(exc),
            )
            return None

    async def _store_articles(
        self, articles: List[Dict[str, Any]], feed_config: Dict[str, Any]
    ) -> tuple[int, int, List[str]]:
        """Store processed articles in the database"""
        stored_count = 0
        failed_count = 0
        errors = []

        async with get_db_session() as db:
            try:
                # Get or create news source
                source = await self._get_or_create_source(db, feed_config)

                for article_data in articles:
                    try:
                        # Check for duplicates
                        duplicate_exists = await db.scalar(
                            select(
                                exists().where(
                                    Article.content_hash == article_data["content_hash"]
                                )
                            )
                        )

                        if duplicate_exists:
                            logger.debug(
                                "Skipping duplicate article",
                                title=article_data["title"][:100],
                            )
                            continue

                        # Create article record
                        article = Article(
                            source_id=source.source_id,
                            title=article_data["title"],
                            content=article_data["content"],
                            summary=article_data["summary"],
                            author=article_data["author"],
                            published_at=article_data["published_at"],
                            url=article_data["url"],
                            language_code=article_data["language_code"],
                            word_count=article_data["word_count"],
                            content_hash=article_data["content_hash"],
                            title_hash=article_data["title_hash"],
                        )

                        db.add(article)
                        stored_count += 1

                    except IntegrityError as exc:
                        # Handle constraint violations (likely duplicates)
                        logger.debug(
                            "Article constraint violation (likely duplicate)",
                            title=article_data["title"][:100],
                            error=str(exc),
                        )
                        await db.rollback()
                        continue

                    except Exception as exc:
                        failed_count += 1
                        error_msg = f"Failed to store article '{article_data['title'][:100]}': {exc}"
                        errors.append(error_msg)
                        logger.error(
                            "Article storage failed",
                            title=article_data["title"][:100],
                            error=str(exc),
                        )
                        await db.rollback()
                        continue

                # Commit all successful inserts
                await db.commit()

                # Update source statistics
                await self._update_source_stats(db, source, stored_count)

            except SQLAlchemyError as exc:
                await db.rollback()
                error_msg = f"Database error during article storage: {exc}"
                errors.append(error_msg)
                logger.error("Database error in article storage", error=str(exc))
                raise RetryableError(error_msg, retry_delay=300)  # Retry in 5 minutes

        return stored_count, failed_count, errors

    async def _get_or_create_source(
        self, db, feed_config: Dict[str, Any]
    ) -> NewsSource:
        """Get existing news source or create a new one"""
        try:
            # Try to find existing source
            source = await db.scalar(
                select(NewsSource).where(NewsSource.source_url == feed_config["url"])
            )

            if source:
                return source

            # Create new source
            source_type = feed_config.get("source_type", "rss")
            source = NewsSource(
                source_name=feed_config["name"],
                source_url=feed_config["url"],
                source_type=source_type,
                language_code=feed_config["language"],
                country_code=(
                    feed_config.get("country", "")[:2]
                    if feed_config.get("country")
                    else None
                ),
                credibility_score={"high": 8.0, "medium": 6.0, "low": 4.0}.get(
                    feed_config.get("reliability", "medium"), 6.0
                ),
                update_frequency_minutes=feed_config.get("update_frequency", "30min")
                .replace("min", "")
                .replace("60", "60"),
                is_active=True,
            )

            db.add(source)
            await db.commit()
            await db.refresh(source)

            logger.info(
                "Created new news source",
                source_name=source.source_name,
                source_url=source.source_url,
            )

            return source

        except Exception as exc:
            await db.rollback()
            logger.error(
                "Failed to get or create news source",
                feed_name=feed_config.get("name"),
                error=str(exc),
            )
            raise

    async def _update_source_stats(self, db, source: NewsSource, articles_added: int):
        """Update source statistics after ingestion"""
        try:
            source.last_crawled_at = datetime.now(timezone.utc)
            # You could add more statistics here like article counts, etc.
            await db.commit()
        except Exception as exc:
            logger.error(
                "Failed to update source statistics",
                source_id=str(source.source_id),
                error=str(exc),
            )


# Celery Tasks
@celery_app.task(bind=True, name="etl.ingest_all_feeds")
def ingest_all_feeds(self):
    """
    Celery task to ingest articles from all configured RSS feeds
    Scheduled to run hourly via Celery Beat
    """
    logger.info("Starting ingestion of all RSS feeds")

    async def _async_ingest_all_feeds():
        manager = FeedIngestionManager()

        # Get feeds from configuration
        feeds = manager.feeds_config.get("strategic_news_feeds", {}).get("feeds", [])

        if not feeds:
            logger.warning("No feeds configured for ingestion")
            return {
                "success": False,
                "message": "No feeds configured",
                "feeds_processed": 0,
                "total_articles": 0,
            }

        # Process all feeds
        results = []
        total_articles = 0
        successful_feeds = 0

        # Process feeds concurrently (but with limit to avoid overwhelming sources)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent feed requests

        async def process_feed_with_semaphore(feed_config):
            async with semaphore:
                return await manager.ingest_single_feed(feed_config)

        # Execute ingestion for all feeds
        tasks = [process_feed_with_semaphore(feed) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Feed ingestion task failed",
                    feed_name=feeds[i].get("name"),
                    error=str(result),
                )
                continue

            if result.success:
                successful_feeds += 1
                total_articles += result.items_processed

                logger.info(
                    "Feed ingestion completed",
                    feed_name=result.metadata.get("feed_name"),
                    articles_processed=result.items_processed,
                    articles_failed=result.items_failed,
                    duration=result.duration_seconds,
                )
            else:
                logger.error(
                    "Feed ingestion failed",
                    feed_name=result.metadata.get("feed_name"),
                    errors=result.errors,
                )

        # Summary
        logger.info(
            "All feeds ingestion completed",
            total_feeds=len(feeds),
            successful_feeds=successful_feeds,
            total_articles_ingested=total_articles,
        )

        return {
            "success": True,
            "feeds_processed": successful_feeds,
            "total_feeds": len(feeds),
            "total_articles": total_articles,
            "results": [r for r in results if not isinstance(r, Exception)],
        }

    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_ingest_all_feeds())


@celery_app.task(bind=True, name="etl.ingest_single_feed")
def ingest_single_feed(self, feed_name: str):
    """
    Celery task to ingest articles from a single RSS feed
    Can be called directly for testing or manual ingestion
    """
    logger.info("Starting ingestion of single feed", feed_name=feed_name)

    async def _async_ingest_single_feed():
        manager = FeedIngestionManager()

        # Find the specified feed
        feeds = manager.feeds_config.get("strategic_news_feeds", {}).get("feeds", [])
        target_feed = None

        for feed in feeds:
            if feed.get("name") == feed_name:
                target_feed = feed
                break

        if not target_feed:
            error_msg = f"Feed '{feed_name}' not found in configuration"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

        # Process the single feed
        result = await manager.ingest_single_feed(target_feed)

        if result.success:
            logger.info(
                "Single feed ingestion completed",
                feed_name=feed_name,
                articles_processed=result.items_processed,
                duration=result.duration_seconds,
            )
        else:
            logger.error(
                "Single feed ingestion failed",
                feed_name=feed_name,
                errors=result.errors,
            )

        return {
            "success": result.success,
            "feed_name": feed_name,
            "articles_processed": result.items_processed,
            "articles_failed": result.items_failed,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
        }

    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_ingest_single_feed())


@celery_app.task(bind=True, name="etl.test_feed_connectivity")
def test_feed_connectivity(self):
    """
    Test connectivity to all configured RSS feeds
    Useful for health checks and feed validation
    """
    logger.info("Testing connectivity to all RSS feeds")

    async def _async_test_connectivity():
        manager = FeedIngestionManager()
        feeds = manager.feeds_config.get("strategic_news_feeds", {}).get("feeds", [])

        results = []

        async with aiohttp.ClientSession(timeout=manager.session_timeout) as session:
            for feed in feeds:
                feed_name = feed.get("name")
                feed_url = feed.get("url")

                try:
                    async with session.get(feed_url) as response:
                        status = response.status
                        accessible = status == 200

                        results.append(
                            {
                                "feed_name": feed_name,
                                "feed_url": feed_url,
                                "accessible": accessible,
                                "status_code": status,
                                "error": None,
                            }
                        )

                        logger.info(
                            "Feed connectivity test",
                            feed_name=feed_name,
                            accessible=accessible,
                            status_code=status,
                        )

                except Exception as exc:
                    results.append(
                        {
                            "feed_name": feed_name,
                            "feed_url": feed_url,
                            "accessible": False,
                            "status_code": None,
                            "error": str(exc),
                        }
                    )

                    logger.error(
                        "Feed connectivity test failed",
                        feed_name=feed_name,
                        error=str(exc),
                    )

        accessible_count = sum(1 for r in results if r["accessible"])

        return {
            "total_feeds": len(feeds),
            "accessible_feeds": accessible_count,
            "results": results,
        }

    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_async_test_connectivity())
