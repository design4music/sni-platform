"""
RSS Feed Ingestion Implementation
"""

from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp
import feedparser
import structlog
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from .base import BaseIngestionSource, RawArticle

logger = structlog.get_logger(__name__)


class RSSIngestionSource(BaseIngestionSource):
    """RSS feed ingestion source"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.timeout = source_config.get("timeout", 30)
        self.max_articles = source_config.get("max_articles", 100)
        self.user_agent = source_config.get(
            "user_agent", "Strategic-Narrative-Intelligence/1.0"
        )

    async def validate_source(self) -> bool:
        """Validate RSS feed accessibility"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                headers = {"User-Agent": self.user_agent}

                async with session.get(self.url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(
                            "RSS feed validation failed",
                            source=self.name,
                            status=response.status,
                            url=self.url,
                        )
                        return False

                    # Try to parse the feed
                    content = await response.text()
                    feed = feedparser.parse(content)

                    if feed.bozo:
                        logger.warning(
                            "RSS feed has parsing issues",
                            source=self.name,
                            url=self.url,
                            bozo_exception=str(feed.bozo_exception),
                        )
                        # Still return True as some feeds work despite bozo flag

                    return len(feed.entries) > 0

        except Exception as e:
            logger.error(
                "RSS feed validation error",
                source=self.name,
                url=self.url,
                error=str(e),
            )
            return False

    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles from RSS feed"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                headers = {"User-Agent": self.user_agent}

                async with session.get(self.url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(
                            "Failed to fetch RSS feed",
                            source=self.name,
                            status=response.status,
                        )
                        return

                    content = await response.text()
                    feed = feedparser.parse(content)

                    logger.info(
                        "RSS feed fetched", source=self.name, entries=len(feed.entries)
                    )

                    processed = 0
                    for entry in feed.entries:
                        if processed >= self.max_articles:
                            break

                        try:
                            article = await self._parse_entry(entry)
                            if article:
                                yield article
                                processed += 1

                        except Exception as e:
                            logger.error(
                                "Failed to parse RSS entry",
                                source=self.name,
                                entry_title=getattr(entry, "title", "Unknown"),
                                error=str(e),
                            )
                            continue

                    logger.info(
                        "RSS processing completed",
                        source=self.name,
                        processed=processed,
                    )

        except Exception as e:
            logger.error("RSS fetch error", source=self.name, error=str(e))

    async def _parse_entry(self, entry) -> Optional[RawArticle]:
        """Parse individual RSS entry into RawArticle"""
        try:
            # Extract basic fields
            title = getattr(entry, "title", "").strip()
            if not title:
                return None

            url = getattr(entry, "link", "").strip()
            if not url:
                return None

            # Extract content
            content = self._extract_content(entry)
            summary = getattr(entry, "summary", "").strip()

            # Extract author
            author = self._extract_author(entry)

            # Extract published date
            published_at = self._extract_published_date(entry)

            # Create metadata
            metadata = {
                "source_type": "rss",
                "source_name": self.name,
                "feed_url": self.url,
                "raw_entry": {
                    "id": getattr(entry, "id", ""),
                    "guid": getattr(entry, "guid", ""),
                    "categories": [tag.term for tag in getattr(entry, "tags", [])],
                    "updated": getattr(entry, "updated", ""),
                },
            }

            return RawArticle(
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                language=self.language,
                summary=summary,
                metadata=metadata,
            )

        except Exception as e:
            logger.error("Entry parsing error", source=self.name, error=str(e))
            return None

    def _extract_content(self, entry) -> Optional[str]:
        """Extract content from RSS entry"""
        # Try different content fields in order of preference
        content_fields = ["content", "description", "summary", "summary_detail"]

        for field in content_fields:
            if hasattr(entry, field):
                value = getattr(entry, field)

                # Handle different content structures
                if isinstance(value, list) and value:
                    # Content is often a list of dicts
                    content_item = value[0]
                    if isinstance(content_item, dict):
                        return content_item.get("value", "").strip()
                    else:
                        return str(content_item).strip()

                elif isinstance(value, dict):
                    return value.get("value", "").strip()

                elif isinstance(value, str):
                    return value.strip()

        return None

    def _extract_author(self, entry) -> Optional[str]:
        """Extract author from RSS entry"""
        # Try different author fields
        author_fields = ["author", "author_detail", "dc_creator"]

        for field in author_fields:
            if hasattr(entry, field):
                value = getattr(entry, field)

                if isinstance(value, dict):
                    # Author detail structure
                    name = value.get("name", "").strip()
                    if name:
                        return name

                elif isinstance(value, str):
                    return value.strip()

        return None

    def _extract_published_date(self, entry) -> Optional[datetime]:
        """Extract published date from RSS entry"""
        # Try different date fields
        date_fields = [
            "published_parsed",
            "updated_parsed",
            "published",
            "updated",
            "pubDate",
        ]

        for field in date_fields:
            if hasattr(entry, field):
                value = getattr(entry, field)

                # Handle parsed time tuples
                if hasattr(value, "tm_year"):
                    try:
                        return datetime(*value[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        continue

                # Handle string dates
                elif isinstance(value, str) and value.strip():
                    try:
                        parsed_date = date_parser.parse(value.strip())
                        # Ensure timezone awareness
                        if parsed_date.tzinfo is None:
                            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                        return parsed_date
                    except (ValueError, TypeError):
                        continue

        # Default to current time if no date found
        return datetime.now(timezone.utc)


class EnhancedRSSIngestionSource(RSSIngestionSource):
    """Enhanced RSS ingestion with content extraction and cleanup"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.extract_full_content = source_config.get("extract_full_content", False)
        self.clean_html = source_config.get("clean_html", True)

    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles with enhanced content extraction"""
        async for article in super().fetch_articles():
            try:
                # Enhance content if requested
                if self.extract_full_content and article.url:
                    enhanced_content = await self._extract_full_content(article.url)
                    if enhanced_content:
                        article.content = enhanced_content

                # Clean HTML if requested
                if self.clean_html and article.content:
                    article.content = self._clean_html(article.content)

                # Extract additional metadata
                article.metadata.update(await self._extract_metadata(article))

                yield article

            except Exception as e:
                logger.error(
                    "Enhanced processing failed",
                    source=self.name,
                    url=article.url,
                    error=str(e),
                )
                # Still yield the original article
                yield article

    async def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full content from article URL"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                headers = {"User-Agent": self.user_agent}

                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return None

                    html_content = await response.text()

                    # Use newspaper3k or similar for content extraction
                    # For now, simple HTML parsing
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(html_content, "html.parser")

                    # Remove unwanted elements
                    for tag in soup(
                        ["script", "style", "nav", "header", "footer", "aside"]
                    ):
                        tag.decompose()

                    # Try to find article content
                    content_selectors = [
                        "article",
                        ".article-content",
                        ".content",
                        ".post-content",
                        "main",
                    ]

                    for selector in content_selectors:
                        content_element = soup.select_one(selector)
                        if content_element:
                            return content_element.get_text(strip=True)

                    # Fallback to body content
                    body = soup.find("body")
                    if body:
                        return body.get_text(strip=True)

                    return None

        except Exception as e:
            logger.error("Full content extraction failed", url=url, error=str(e))
            return None

    def _clean_html(self, content: str) -> str:
        """Clean HTML tags and normalize text"""
        try:
            import re

            from bs4 import BeautifulSoup

            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Extract text
            text = soup.get_text()

            # Normalize whitespace
            text = re.sub(r"\s+", " ", text)
            text = text.strip()

            return text

        except Exception as e:
            logger.error("HTML cleaning failed", error=str(e))
            return content

    async def _extract_metadata(self, article: RawArticle) -> Dict[str, Any]:
        """Extract additional metadata from article"""
        metadata = {}

        try:
            # Word count
            if article.content:
                metadata["word_count"] = len(article.content.split())

            # Title word count
            metadata["title_word_count"] = len(article.title.split())

            # Has summary
            metadata["has_summary"] = bool(article.summary)

            # URL domain
            from urllib.parse import urlparse

            parsed_url = urlparse(article.url)
            metadata["domain"] = parsed_url.netloc

            return metadata

        except Exception as e:
            logger.error("Metadata extraction failed", url=article.url, error=str(e))
            return metadata


class GoogleNewsRSSSource(RSSIngestionSource):
    """Google News RSS feed ingestion source with specialized parsing"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        # Google News specific rate limiting (10-15 seconds between requests)
        self.rate_limit_delay = source_config.get("rate_limit_delay", 12)

    async def _parse_entry(self, entry) -> Optional[RawArticle]:
        """Parse Google News RSS entry with specialized handling"""
        try:
            # Extract basic fields
            original_title = getattr(entry, "title", "").strip()
            if not original_title:
                return None

            # Extract Google News URL
            google_url = getattr(entry, "link", "").strip()
            if not google_url:
                return None

            # Extract anchor text from description as title (cleaner than original title)
            title = self._extract_anchor_text(entry) or original_title

            # Use Google URL directly - fetch_fulltext.py will resolve to original URL
            # This avoids consent pages and GDPR redirects during initial ingestion
            url = google_url

            # Extract content (usually minimal in Google News)
            content = self._extract_content(entry)
            summary = getattr(entry, "summary", "").strip()

            # Extract author if available
            author = self._extract_author(entry)

            # Extract published date
            published_at = self._extract_published_date(entry)

            # Create metadata
            metadata = {
                "source_name": self.name,
                "feed_url": self.url,
                "original_title": original_title,  # Keep original title with source suffix
                "raw_entry": {
                    "id": getattr(entry, "id", ""),
                    "guid": getattr(entry, "guid", ""),
                    "categories": [tag.term for tag in getattr(entry, "tags", [])],
                    "updated": getattr(entry, "updated", ""),
                },
            }

            return RawArticle(
                title=title,
                content=content,  # Will be empty initially, populated by fetch_fulltext.py
                url=url,
                author=author,
                published_at=published_at,
                language=self.language,
                summary=summary,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(
                "Google News entry parsing error", source=self.name, error=str(e)
            )
            return None

    def _extract_anchor_text(self, entry) -> Optional[str]:
        """Extract anchor text from Google News description"""
        try:
            description = getattr(entry, "description", "")
            if not description:
                return None

            # Parse HTML content to find the anchor tag
            soup = BeautifulSoup(description, "html.parser")

            # Find the first link (article title link)
            link = soup.find("a")
            if link:
                anchor_text = link.get_text(strip=True)
                if anchor_text:
                    return anchor_text

            return None

        except Exception as e:
            logger.debug(
                "Failed to extract anchor text", source=self.name, error=str(e)
            )
            return None

    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles with Google News rate limiting"""
        import asyncio

        # Add rate limiting delay before processing
        if hasattr(self, "_last_request_time"):
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

        # Use parent's fetch_articles method
        async for article in super().fetch_articles():
            yield article
