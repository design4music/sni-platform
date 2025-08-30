"""
RSS Feed Handler
Strategic Narrative Intelligence ETL Pipeline

Handler for RSS and Google RSS feeds using the registry pattern.
Supports both traditional RSS and Google News RSS feeds with specialized parsing.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Tuple

import structlog
from bs4 import BeautifulSoup

from .db_utils import save_article_from_rss
from .handlers import BaseFeedHandler, register
from .rss_ingestion import GoogleNewsRSSSource, RSSIngestionSource

logger = structlog.get_logger(__name__)


def clean_source_name(feed_name: str) -> str:
    """
    Clean source name by removing technical suffixes

    Examples:
    - "Associated Press (Google News)" → "Associated Press"
    - "Reuters Sitemap Sitemap" → "Reuters"
    - "BBC World News" → "BBC World News" (unchanged)
    """
    # Remove Google News suffix
    if feed_name.endswith("(Google News)"):
        return feed_name.replace("(Google News)", "").strip()

    # Remove Sitemap suffixes
    if "Sitemap" in feed_name:
        # Handle cases like "Reuters Sitemap Sitemap"
        cleaned = feed_name.replace("Sitemap", "").strip()
        # Remove extra spaces and trailing words
        parts = cleaned.split()
        if parts:
            # Take first meaningful part (usually the agency name)
            return parts[0]

    return feed_name


def strip_html_content(html_content: str) -> str:
    """
    Strip HTML tags and clean up content for temporary storage

    Used for Google News content that contains HTML which will be
    replaced by full-text extraction later.
    """
    if not html_content:
        return ""

    try:
        # Parse HTML and extract clean text
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements completely
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content and clean up whitespace
        text = soup.get_text()

        # Normalize whitespace
        import re

        text = re.sub(r"\s+", " ", text).strip()

        return text

    except Exception as e:
        logger.debug(f"HTML stripping failed: {e}")
        # Return original content if stripping fails
        return html_content


@register("RSS")
class RSSFeedHandler(BaseFeedHandler):
    """
    Handler for traditional RSS feeds

    Features:
    - Standard RSS 2.0/Atom parsing
    - Content extraction and cleanup
    - Author and metadata extraction
    - Language detection
    - Error resilient processing
    - Incremental ingestion using timestamps
    """

    def ingest(
        self,
        feed_id: str,
        feed_name: str,
        feed_url: str,
        last_fetched_at: Optional[datetime] = None,
        max_articles: int = 100,
    ) -> Tuple[int, int, int]:
        """
        Ingest articles from RSS feed using incremental approach

        Args:
            feed_id: Database feed ID
            feed_name: Human-readable feed name
            feed_url: RSS feed URL
            last_fetched_at: Timestamp of last successful fetch (None for new feeds)
            max_articles: Maximum articles to process

        Returns:
            Tuple of (new_articles, duplicates, errors)
        """
        logger.info(f"Processing RSS feed: {feed_name} ({feed_url})")

        try:
            # Configure RSS source
            source_config = {
                "name": feed_name,
                "url": feed_url,
                "language": "en",  # Default, will be auto-detected
                "max_articles": max_articles,
                "timeout": 30,
            }

            # Create RSS source
            rss_source = RSSIngestionSource(source_config)

            # Clean source name for database storage
            clean_name = clean_source_name(feed_name)

            # Run async ingestion
            return asyncio.run(
                self._async_ingest(rss_source, feed_id, clean_name, last_fetched_at)
            )

        except Exception as e:
            logger.error(f"Failed to process RSS feed {feed_name}: {e}")
            return 0, 0, 1

    async def _async_ingest(
        self,
        rss_source: RSSIngestionSource,
        feed_id: str,
        feed_name: str,
        last_fetched_at: Optional[datetime],
    ) -> Tuple[int, int, int]:
        """Async ingestion logic using incremental timestamps"""

        # Validate source
        if not await rss_source.validate_source():
            logger.error(f"RSS source validation failed: {feed_name}")
            return 0, 0, 1

        new_count = 0
        duplicate_count = 0
        error_count = 0

        # Fetch articles
        async for article in rss_source.fetch_articles():
            try:
                # Filter by last fetch timestamp (incremental ingestion)
                if last_fetched_at and article.published_at:
                    # Skip articles published before the last successful fetch
                    if article.published_at <= last_fetched_at:
                        logger.debug(
                            f"Article already processed, skipping: {article.title}"
                        )
                        continue

                # Save article
                result = save_article_from_rss(
                    feed_id=feed_id,
                    article=article,
                    source_name=feed_name,
                )

                if result == "new":
                    new_count += 1
                elif result == "duplicate":
                    duplicate_count += 1
                else:  # error
                    error_count += 1

            except Exception as e:
                logger.debug(f"Error processing article {article.url}: {e}")
                error_count += 1

        logger.info(
            f"RSS feed {feed_name}: "
            f"{new_count} new, {duplicate_count} duplicates, {error_count} errors"
        )

        return new_count, duplicate_count, error_count

    def get_handler_name(self) -> str:
        """Get human-readable handler name"""
        return "RSS Feed Handler"


@register("google_rss")
class GoogleRSSFeedHandler(BaseFeedHandler):
    """
    Handler for Google News RSS feeds

    Features:
    - Google News RSS parsing
    - Anchor text extraction for clean titles
    - Google URL handling
    - Rate limiting (12-second delays)
    - Source attribution metadata
    """

    def ingest(
        self,
        feed_id: str,
        feed_name: str,
        feed_url: str,
        last_fetched_at: Optional[datetime] = None,
        max_articles: int = 100,
    ) -> Tuple[int, int, int]:
        """
        Ingest articles from Google News RSS feed

        Args:
            feed_id: Database feed ID
            feed_name: Human-readable feed name
            feed_url: Google News RSS URL
            hours_lookback: Hours to look back for new content
            max_articles: Maximum articles to process

        Returns:
            Tuple of (new_articles, duplicates, errors)
        """
        logger.info(f"Processing Google RSS feed: {feed_name} ({feed_url})")

        try:
            # Configure Google RSS source
            source_config = {
                "name": feed_name,
                "url": feed_url,
                "language": "en",  # Google News feeds are typically English
                "max_articles": max_articles,
                "timeout": 30,
                "rate_limit_delay": 12,  # Conservative rate limiting
            }

            # Create Google RSS source
            rss_source = GoogleNewsRSSSource(source_config)

            # Clean source name for database storage
            clean_name = clean_source_name(feed_name)

            # Run async ingestion
            return asyncio.run(
                self._async_ingest(rss_source, feed_id, clean_name, last_fetched_at)
            )

        except Exception as e:
            logger.error(f"Failed to process Google RSS feed {feed_name}: {e}")
            return 0, 0, 1

    async def _async_ingest(
        self,
        rss_source: GoogleNewsRSSSource,
        feed_id: str,
        feed_name: str,
        last_fetched_at: Optional[datetime],
    ) -> Tuple[int, int, int]:
        """Async ingestion logic for Google RSS feeds"""

        # Validate source
        if not await rss_source.validate_source():
            logger.error(f"Google RSS source validation failed: {feed_name}")
            return 0, 0, 1

        new_count = 0
        duplicate_count = 0
        error_count = 0

        # Fetch articles
        async for article in rss_source.fetch_articles():
            try:
                # Filter by last fetch timestamp (incremental ingestion)
                if last_fetched_at and article.published_at:
                    # Skip articles published before the last successful fetch
                    if article.published_at <= last_fetched_at:
                        logger.debug(
                            f"Article already processed, skipping: {article.title}"
                        )
                        continue

                # Strip HTML from content and summary for Google News
                if article.content:
                    article.content = strip_html_content(article.content)
                if article.summary:
                    article.summary = strip_html_content(article.summary)

                # Save article
                result = save_article_from_rss(
                    feed_id=feed_id,
                    article=article,
                    source_name=feed_name,
                )

                if result == "new":
                    new_count += 1
                elif result == "duplicate":
                    duplicate_count += 1
                else:  # error
                    error_count += 1

            except Exception as e:
                logger.debug(f"Error processing article {article.url}: {e}")
                error_count += 1

        logger.info(
            f"Google RSS feed {feed_name}: "
            f"{new_count} new, {duplicate_count} duplicates, {error_count} errors"
        )

        return new_count, duplicate_count, error_count

    def get_handler_name(self) -> str:
        """Get human-readable handler name"""
        return "Google RSS Feed Handler"
