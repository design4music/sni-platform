"""
Feed Ingestion Framework for Strategic Narrative Intelligence ETL Pipeline

This module handles ingestion from multiple news sources including RSS feeds,
REST APIs, and web scrapers with comprehensive error handling and retry logic.
"""

import asyncio
import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiofiles
import aiohttp
import feedparser
import structlog
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from ..config import IngestionConfig
from ..database import get_db_session
from ..database.models import (Article, FeedMetrics, FeedType, NewsFeed,
                               ProcessingStatus)
from ..exceptions import ContentError, FeedError, IngestionError
from ..monitoring import MetricsCollector

logger = structlog.get_logger(__name__)


@dataclass
class IngestionResult:
    """Result of feed ingestion operation"""

    feed_id: str
    success: bool
    articles_count: int
    new_articles_count: int
    duplicate_articles_count: int
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0
    total_articles_processed: int = 0


@dataclass
class ArticleData:
    """Structured article data from ingestion"""

    title: str
    content: Optional[str]
    url: str
    published_at: datetime
    author: Optional[str] = None
    summary: Optional[str] = None
    source_name: Optional[str] = None
    language: str = "en"
    content_hash: Optional[str] = None
    title_hash: Optional[str] = None


class FeedIngestor:
    """
    Handles ingestion from various news feed sources with error handling,
    deduplication, and quality validation.
    """

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.metrics_collector = MetricsCollector(config.monitoring)

        # HTTP client configuration
        self.timeout = aiohttp.ClientTimeout(
            total=config.request_timeout_seconds, connect=config.connect_timeout_seconds
        )

        # Content parsing patterns
        self.date_patterns = [
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
            r"\d{2}/\d{2}/\d{4}",
            r"\d{2}-\d{2}-\d{4}",
        ]

        # Quality filters
        self.min_title_length = 10
        self.min_content_length = 100
        self.max_content_length = 50000

        # Deduplication cache
        self.content_hashes = set()

    async def ingest_feed(self, feed_config: Dict[str, Any]) -> IngestionResult:
        """
        Ingest articles from a single news feed.

        Args:
            feed_config: Feed configuration dictionary

        Returns:
            IngestionResult with ingestion statistics
        """
        start_time = datetime.utcnow()
        feed_id = feed_config.get("id")

        self.logger.info(
            "Starting feed ingestion",
            feed_id=feed_id,
            feed_type=feed_config.get("type"),
        )

        try:
            # Get feed from database
            with get_db_session() as db:
                feed = db.query(NewsFeed).filter(NewsFeed.id == feed_id).first()
                if not feed or not feed.is_active:
                    raise FeedError(f"Feed {feed_id} not found or inactive")

            # Determine ingestion method based on feed type
            if feed.feed_type == FeedType.RSS:
                articles = await self._ingest_rss_feed(feed)
            elif feed.feed_type == FeedType.API:
                articles = await self._ingest_api_feed(feed)
            elif feed.feed_type == FeedType.SCRAPER:
                articles = await self._ingest_scraper_feed(feed)
            else:
                raise FeedError(f"Unsupported feed type: {feed.feed_type}")

            # Process and store articles
            result = await self._process_and_store_articles(feed, articles)

            # Update feed metrics
            await self._update_feed_metrics(feed, result, success=True)

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time_seconds = processing_time

            self.logger.info(
                "Feed ingestion completed successfully",
                feed_id=feed_id,
                articles_count=result.articles_count,
                new_articles=result.new_articles_count,
                processing_time=processing_time,
            )

            return result

        except Exception as exc:
            # Update feed metrics for failure
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            with get_db_session() as db:
                feed = db.query(NewsFeed).filter(NewsFeed.id == feed_id).first()
                if feed:
                    await self._update_feed_metrics(
                        feed, None, success=False, error=str(exc)
                    )

            error_result = IngestionResult(
                feed_id=feed_id,
                success=False,
                articles_count=0,
                new_articles_count=0,
                duplicate_articles_count=0,
                error_message=str(exc),
                processing_time_seconds=processing_time,
            )

            self.logger.error(
                "Feed ingestion failed",
                feed_id=feed_id,
                error=str(exc),
                processing_time=processing_time,
                exc_info=True,
            )

            raise IngestionError(
                f"Failed to ingest feed {feed_id}: {str(exc)}"
            ) from exc

    async def _ingest_rss_feed(self, feed: NewsFeed) -> List[ArticleData]:
        """Ingest articles from RSS feed"""
        articles = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                headers = self._get_request_headers(feed)

                async with session.get(feed.url, headers=headers) as response:
                    if response.status != 200:
                        raise FeedError(f"RSS feed returned status {response.status}")

                    content = await response.text()

                # Parse RSS content
                rss_data = feedparser.parse(content)

                if rss_data.bozo and rss_data.bozo_exception:
                    self.logger.warning(
                        "RSS feed has parsing issues",
                        feed_id=str(feed.id),
                        error=str(rss_data.bozo_exception),
                    )

                # Extract articles from RSS entries
                for entry in rss_data.entries:
                    try:
                        article_data = await self._parse_rss_entry(entry, feed)
                        if article_data and self._is_quality_content(article_data):
                            articles.append(article_data)
                    except Exception as exc:
                        self.logger.warning(
                            "Failed to parse RSS entry",
                            feed_id=str(feed.id),
                            entry_title=getattr(entry, "title", "Unknown"),
                            error=str(exc),
                        )
                        continue

            except aiohttp.ClientError as exc:
                raise FeedError(f"HTTP error fetching RSS feed: {str(exc)}") from exc
            except Exception as exc:
                raise FeedError(f"Error parsing RSS feed: {str(exc)}") from exc

        return articles

    async def _ingest_api_feed(self, feed: NewsFeed) -> List[ArticleData]:
        """Ingest articles from REST API"""
        articles = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                headers = self._get_request_headers(feed)
                params = feed.api_params or {}

                # Add API key if required
                if feed.api_key_required and self.config.api_keys.get(str(feed.id)):
                    api_key = self.config.api_keys[str(feed.id)]
                    if "api_key" in params:
                        params["api_key"] = api_key
                    elif "apikey" in params:
                        params["apikey"] = api_key
                    else:
                        headers["Authorization"] = f"Bearer {api_key}"

                async with session.get(
                    feed.url, headers=headers, params=params
                ) as response:
                    if response.status == 429:  # Rate limited
                        raise FeedError("API rate limit exceeded")
                    elif response.status == 401:
                        raise FeedError("API authentication failed")
                    elif response.status != 200:
                        raise FeedError(f"API returned status {response.status}")

                    data = await response.json()

                # Parse API response based on common patterns
                articles_data = self._extract_articles_from_api_response(data)

                for article_json in articles_data:
                    try:
                        article_data = await self._parse_api_article(article_json, feed)
                        if article_data and self._is_quality_content(article_data):
                            articles.append(article_data)
                    except Exception as exc:
                        self.logger.warning(
                            "Failed to parse API article",
                            feed_id=str(feed.id),
                            error=str(exc),
                        )
                        continue

            except aiohttp.ClientError as exc:
                raise FeedError(f"HTTP error fetching API feed: {str(exc)}") from exc
            except Exception as exc:
                raise FeedError(f"Error parsing API feed: {str(exc)}") from exc

        return articles

    async def _ingest_scraper_feed(self, feed: NewsFeed) -> List[ArticleData]:
        """Ingest articles using web scraping"""
        articles = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            try:
                headers = self._get_request_headers(feed)

                async with session.get(feed.url, headers=headers) as response:
                    if response.status != 200:
                        raise FeedError(
                            f"Scraper target returned status {response.status}"
                        )

                    html_content = await response.text()

                # Parse HTML content
                soup = BeautifulSoup(html_content, "html.parser")

                # Extract articles using configured XPath/CSS selectors
                article_elements = self._extract_article_elements(soup, feed)

                for element in article_elements:
                    try:
                        article_data = await self._parse_scraped_article(element, feed)
                        if article_data and self._is_quality_content(article_data):
                            articles.append(article_data)
                    except Exception as exc:
                        self.logger.warning(
                            "Failed to parse scraped article",
                            feed_id=str(feed.id),
                            error=str(exc),
                        )
                        continue

            except aiohttp.ClientError as exc:
                raise FeedError(f"HTTP error scraping feed: {str(exc)}") from exc
            except Exception as exc:
                raise FeedError(f"Error scraping feed: {str(exc)}") from exc

        return articles

    async def _parse_rss_entry(self, entry, feed: NewsFeed) -> Optional[ArticleData]:
        """Parse RSS entry into ArticleData"""
        try:
            # Extract title
            title = getattr(entry, "title", "").strip()
            if not title:
                return None

            # Extract content
            content = None
            if hasattr(entry, "content") and entry.content:
                content = (
                    entry.content[0].get("value", "")
                    if isinstance(entry.content, list)
                    else entry.content
                )
            elif hasattr(entry, "description"):
                content = entry.description
            elif hasattr(entry, "summary"):
                content = entry.summary

            # Clean HTML from content
            if content:
                content = self._clean_html_content(content)

            # Extract URL
            url = getattr(entry, "link", "").strip()
            if not url:
                return None

            # Make URL absolute if relative
            if url.startswith("/"):
                base_url = f"{urlparse(feed.url).scheme}://{urlparse(feed.url).netloc}"
                url = urljoin(base_url, url)

            # Extract publication date
            published_at = self._parse_date(
                getattr(entry, "published", "")
                or getattr(entry, "updated", "")
                or getattr(entry, "created", "")
            )

            if not published_at:
                published_at = datetime.utcnow()

            # Extract author
            author = getattr(entry, "author", None)
            if isinstance(author, dict):
                author = author.get("name", None)

            # Extract summary
            summary = getattr(entry, "summary", None)
            if summary:
                summary = self._clean_html_content(summary)

            # Create hashes for deduplication
            content_hash = self._create_content_hash(content or title)
            title_hash = self._create_content_hash(title)

            return ArticleData(
                title=title,
                content=content,
                url=url,
                published_at=published_at,
                author=author,
                summary=summary,
                source_name=feed.name,
                language=feed.language.value,
                content_hash=content_hash,
                title_hash=title_hash,
            )

        except Exception as exc:
            self.logger.error("Error parsing RSS entry", error=str(exc))
            return None

    async def _parse_api_article(
        self, article_json: Dict[str, Any], feed: NewsFeed
    ) -> Optional[ArticleData]:
        """Parse API article JSON into ArticleData"""
        try:
            # Handle different API response formats
            title = (
                article_json.get("title")
                or article_json.get("headline")
                or article_json.get("name", "")
            ).strip()

            if not title:
                return None

            content = (
                article_json.get("content")
                or article_json.get("body")
                or article_json.get("text")
                or article_json.get("description", "")
            )

            if content:
                content = self._clean_html_content(content)

            url = (
                article_json.get("url")
                or article_json.get("link")
                or article_json.get("permalink", "")
            ).strip()

            if not url:
                return None

            # Parse publication date
            date_field = (
                article_json.get("publishedAt")
                or article_json.get("published_at")
                or article_json.get("pub_date")
                or article_json.get("date")
                or article_json.get("created_at")
            )

            published_at = (
                self._parse_date(date_field) if date_field else datetime.utcnow()
            )

            author = article_json.get("author", {})
            if isinstance(author, dict):
                author = author.get("name") or author.get("display_name")

            summary = article_json.get("summary") or article_json.get("excerpt")
            if summary:
                summary = self._clean_html_content(summary)

            # Create hashes
            content_hash = self._create_content_hash(content or title)
            title_hash = self._create_content_hash(title)

            return ArticleData(
                title=title,
                content=content,
                url=url,
                published_at=published_at,
                author=author,
                summary=summary,
                source_name=feed.name,
                language=feed.language.value,
                content_hash=content_hash,
                title_hash=title_hash,
            )

        except Exception as exc:
            self.logger.error("Error parsing API article", error=str(exc))
            return None

    async def _parse_scraped_article(
        self, element, feed: NewsFeed
    ) -> Optional[ArticleData]:
        """Parse scraped HTML element into ArticleData"""
        try:
            # Extract title using configured selector
            title_element = (
                element.select_one(feed.title_xpath)
                if feed.title_xpath
                else element.find("h1") or element.find("h2")
            )
            title = title_element.get_text().strip() if title_element else ""

            if not title:
                return None

            # Extract content
            content_element = (
                element.select_one(feed.content_xpath)
                if feed.content_xpath
                else element.find("div", class_="content") or element.find("article")
            )
            content = content_element.get_text().strip() if content_element else ""

            # Extract URL
            url_element = element.find("a", href=True)
            url = url_element["href"] if url_element else ""

            if url and url.startswith("/"):
                base_url = f"{urlparse(feed.url).scheme}://{urlparse(feed.url).netloc}"
                url = urljoin(base_url, url)

            if not url:
                return None

            # Extract date
            date_element = (
                element.select_one(feed.date_xpath)
                if feed.date_xpath
                else element.find("time")
            )
            date_text = ""
            if date_element:
                date_text = date_element.get("datetime") or date_element.get_text()

            published_at = (
                self._parse_date(date_text) if date_text else datetime.utcnow()
            )

            # Create hashes
            content_hash = self._create_content_hash(content or title)
            title_hash = self._create_content_hash(title)

            return ArticleData(
                title=title,
                content=content,
                url=url,
                published_at=published_at,
                source_name=feed.name,
                language=feed.language.value,
                content_hash=content_hash,
                title_hash=title_hash,
            )

        except Exception as exc:
            self.logger.error("Error parsing scraped article", error=str(exc))
            return None

    def _get_request_headers(self, feed: NewsFeed) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json, application/xml, text/xml, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        # Add custom headers from feed configuration
        if feed.api_headers:
            headers.update(feed.api_headers)

        return headers

    def _extract_articles_from_api_response(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract articles array from API response"""
        # Handle common API response patterns
        if isinstance(data, list):
            return data
        elif "articles" in data:
            return data["articles"]
        elif "items" in data:
            return data["items"]
        elif "data" in data:
            if isinstance(data["data"], list):
                return data["data"]
            elif "articles" in data["data"]:
                return data["data"]["articles"]
        elif "results" in data:
            return data["results"]
        else:
            # If no standard pattern, try to find array field
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    return value

        return []

    def _extract_article_elements(self, soup: BeautifulSoup, feed: NewsFeed) -> List:
        """Extract article elements from HTML using CSS selectors"""
        # Try common article selectors
        selectors = [
            "article",
            ".article",
            ".post",
            ".news-item",
            ".story",
            '[class*="article"]',
            '[class*="post"]',
            ".entry",
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements

        # Fallback to div elements with text content
        return soup.find_all("div", string=True)[:20]  # Limit to prevent overprocessing

    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content and extract text"""
        if not html_content:
            return ""

        # Parse HTML and extract text
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text and clean whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_string:
            return None

        try:
            # Try dateutil parser first
            return date_parser.parse(date_string, fuzzy=True)
        except:
            # Try regex patterns
            for pattern in self.date_patterns:
                match = re.search(pattern, date_string)
                if match:
                    try:
                        return datetime.strptime(match.group(), "%Y-%m-%d %H:%M:%S")
                    except:
                        continue

        return None

    def _create_content_hash(self, content: str) -> str:
        """Create SHA-256 hash of content for deduplication"""
        if not content:
            return ""

        # Normalize content for hashing
        normalized = re.sub(r"\s+", " ", content.strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _is_quality_content(self, article: ArticleData) -> bool:
        """Check if article meets quality standards"""
        if not article.title or len(article.title) < self.min_title_length:
            return False

        if article.content:
            if len(article.content) < self.min_content_length:
                return False
            if len(article.content) > self.max_content_length:
                return False

        # Check for spam indicators
        spam_patterns = [
            r"click here",
            r"buy now",
            r"limited time",
            r"act now",
            r"free trial",
        ]

        content_to_check = (article.title + " " + (article.content or "")).lower()
        for pattern in spam_patterns:
            if re.search(pattern, content_to_check):
                return False

        return True

    async def _process_and_store_articles(
        self, feed: NewsFeed, articles: List[ArticleData]
    ) -> IngestionResult:
        """Process and store articles in database"""
        new_articles_count = 0
        duplicate_articles_count = 0
        total_articles = len(articles)

        with get_db_session() as db:
            # Get existing content hashes to check for duplicates
            existing_hashes = set()
            existing_articles = (
                db.query(Article.content_hash)
                .filter(
                    Article.feed_id == feed.id,
                    Article.published_at >= datetime.utcnow() - timedelta(days=30),
                )
                .all()
            )

            for article_hash in existing_articles:
                if article_hash.content_hash:
                    existing_hashes.add(article_hash.content_hash)

            # Process each article
            for article_data in articles:
                try:
                    # Check for duplicates
                    if article_data.content_hash in existing_hashes:
                        duplicate_articles_count += 1
                        continue

                    # Create new article record
                    article = Article(
                        feed_id=feed.id,
                        title=article_data.title,
                        content=article_data.content,
                        summary=article_data.summary,
                        url=article_data.url,
                        author=article_data.author,
                        published_at=article_data.published_at,
                        language=article_data.language,
                        source_name=article_data.source_name,
                        content_hash=article_data.content_hash,
                        title_hash=article_data.title_hash,
                        processing_status=ProcessingStatus.PENDING,
                        ingestion_status=ProcessingStatus.COMPLETED,
                        word_count=(
                            len(article_data.content.split())
                            if article_data.content
                            else 0
                        ),
                        reading_time_minutes=(
                            len(article_data.content.split()) / 200.0
                            if article_data.content
                            else 0.0
                        ),
                    )

                    db.add(article)
                    new_articles_count += 1

                    # Add to existing hashes to prevent duplicates in same batch
                    existing_hashes.add(article_data.content_hash)

                except Exception as exc:
                    self.logger.error(
                        "Error storing article",
                        feed_id=str(feed.id),
                        article_title=article_data.title,
                        error=str(exc),
                    )
                    continue

            # Update feed last fetched timestamp
            feed.last_fetched_at = datetime.utcnow()
            if new_articles_count > 0:
                feed.last_successful_fetch_at = datetime.utcnow()

            db.commit()

        return IngestionResult(
            feed_id=str(feed.id),
            success=True,
            articles_count=total_articles,
            new_articles_count=new_articles_count,
            duplicate_articles_count=duplicate_articles_count,
            total_articles_processed=total_articles,
        )

    async def _update_feed_metrics(
        self,
        feed: NewsFeed,
        result: Optional[IngestionResult],
        success: bool,
        error: Optional[str] = None,
    ):
        """Update feed metrics in database"""
        today = datetime.utcnow().date()

        with get_db_session() as db:
            # Get or create today's metrics record
            metrics = (
                db.query(FeedMetrics)
                .filter(FeedMetrics.feed_id == feed.id, FeedMetrics.date == today)
                .first()
            )

            if not metrics:
                metrics = FeedMetrics(feed_id=feed.id, date=today)
                db.add(metrics)

            # Update metrics
            metrics.fetch_attempts += 1

            if success and result:
                metrics.fetch_successes += 1
                metrics.articles_fetched += result.articles_count
                metrics.articles_new += result.new_articles_count
                metrics.articles_duplicate += result.duplicate_articles_count

                if result.processing_time_seconds > 0:
                    if metrics.avg_processing_time_seconds:
                        metrics.avg_processing_time_seconds = (
                            metrics.avg_processing_time_seconds
                            + result.processing_time_seconds
                        ) / 2
                    else:
                        metrics.avg_processing_time_seconds = (
                            result.processing_time_seconds
                        )
            else:
                metrics.fetch_failures += 1
                metrics.error_count += 1
                if error:
                    metrics.last_error_message = error[:1000]  # Truncate long errors

            db.commit()
