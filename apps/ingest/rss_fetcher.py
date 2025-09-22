"""
RSS Feed Fetcher for SNI-v2
INGEST-001: Must-fixes implemented (NFKC, real publisher, UPSERT, watermark, ETag)
"""

import hashlib
import random
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
import requests
from langdetect import DetectorFactory, detect
from loguru import logger
from sqlalchemy import text

from core.config import get_config
from core.database import get_db_session

from .feeds_repo import FeedsRepo

# Set seed for consistent language detection
DetectorFactory.seed = 42


class RSSFetcher:
    """RSS feed fetcher with must-fixes: NFKC, real publisher, UPSERT, watermark, ETag"""

    def __init__(self):
        self.config = get_config()
        self.feeds_repo = FeedsRepo()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "SNI-v2 RSS Fetcher/1.0 (Headlines Analysis)"}
        )

    def normalize_title(
        self, title: str, publisher_name: str = None
    ) -> Tuple[str, str]:
        """
        A) Unicode & suffix normalization with NFKC
        """
        if not title:
            return "", ""

        # Unicode NFKC normalization first
        title = unicodedata.normalize("NFKC", title).strip()

        # Strip trailing publisher patterns only if exact match
        if publisher_name:
            patterns = [
                f" – {publisher_name}",
                f" — {publisher_name}",
                f" - {publisher_name}",
            ]
            for pattern in patterns:
                if title.endswith(pattern):
                    title = title[: -len(pattern)]
                    break

        # Collapse internal whitespace
        title_display = re.sub(r"\s+", " ", title).strip()

        # For matching: lowercase + remove non-informative symbols
        title_norm = title_display.lower()
        title_norm = re.sub(r"[^\w\s\-.,!?:;]", "", title_norm)
        title_norm = re.sub(r"\s+", " ", title_norm).strip()

        return title_display, title_norm

    def detect_language(self, text: str) -> Tuple[Optional[str], float]:
        """Detect language with graceful failure handling"""
        try:
            if not text or len(text.strip()) < 3:
                return None, 0.0

            lang = detect(text)
            confidence = min(0.95, 0.3 + len(text) / 200)
            return lang, confidence

        except Exception as e:
            logger.debug(f"Language detection failed for text: {text[:50]}... - {e}")
            return None, 0.0

    def extract_real_publisher(
        self, entry, feed
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        B) Real publisher extraction from Google News
        Prefer entry.source.title and domain from entry.source.href
        """
        publisher_name = None
        publisher_domain = None

        # Prefer entry.source (real publisher from Google News)
        if hasattr(entry, "source"):
            if hasattr(entry.source, "title") and entry.source.title:
                publisher_name = entry.source.title.strip()

            if hasattr(entry.source, "href") and entry.source.href:
                try:
                    parsed = urlparse(entry.source.href)
                    domain = parsed.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                    publisher_domain = domain
                except:
                    pass

        # Fallback to feed title only if entry.source missing
        if not publisher_name and hasattr(feed, "feed") and hasattr(feed.feed, "title"):
            publisher_name = feed.feed.title.strip()

        return publisher_name, publisher_domain

    def generate_content_hash(self, title_norm: str, publisher_domain: str) -> str:
        """Generate content hash for deduplication"""
        content = f"{title_norm}||{publisher_domain or ''}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def fetch_with_retries(
        self, feed_url: str, headers: Dict
    ) -> Optional[requests.Response]:
        """
        E) Conditional GET + retries with exponential backoff
        """
        for attempt in range(self.config.http_retries):
            try:
                response = self.session.get(
                    feed_url, headers=headers, timeout=self.config.http_timeout_sec
                )

                # 304 Not Modified - short circuit
                if response.status_code == 304:
                    logger.info(f"Feed not modified (304): {feed_url}")
                    return response

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                if attempt == self.config.http_retries - 1:
                    logger.error(
                        f"HTTP error after {self.config.http_retries} attempts for {feed_url}: {e}"
                    )
                    raise

                # Exponential backoff with jitter
                delay = (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    f"HTTP error attempt {attempt + 1}/{self.config.http_retries} for {feed_url}: {e}. Retrying in {delay:.1f}s"
                )
                time.sleep(delay)

        return None

    def fetch_feed(self, feed_id: str, feed_url: str) -> Tuple[List[Dict], Dict]:
        """
        Fetch and parse RSS feed with all must-fixes
        Returns (articles, stats)
        """
        start_time = time.time()
        stats = {
            "fetched": 0,
            "inserted": 0,
            "skipped": 0,
            "errors": 0,
            "duration_sec": 0,
        }

        try:
            # Get feed metadata for conditional GET
            feed_meta = self.feeds_repo.get(feed_url)

            # Prepare conditional headers
            headers = {}
            if feed_meta.get("etag"):
                headers["If-None-Match"] = feed_meta["etag"]
            if feed_meta.get("last_modified"):
                headers["If-Modified-Since"] = feed_meta["last_modified"]

            logger.info(f"Fetching RSS feed: {feed_url}")

            # Fetch with retries
            response = self.fetch_with_retries(feed_url, headers)
            if not response:
                return [], stats

            # Handle 304 Not Modified
            if response.status_code == 304:
                # Update last_run_at only
                self.feeds_repo.upsert(feed_url)
                stats["duration_sec"] = time.time() - start_time
                return [], stats

            # Parse RSS
            feed = feedparser.parse(response.content)

            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    f"Feed parsing warning for {feed_url}: {feed.bozo_exception}"
                )

            # Extract ETag and Last-Modified for next request
            etag = response.headers.get("ETag")
            last_modified = response.headers.get("Last-Modified")

            articles = []
            latest_pubdate = feed_meta.get("last_pubdate_utc")

            # D) Remove hard slice - iterate all entries with watermark
            watermark_date = None
            if feed_meta.get("last_pubdate_utc"):
                watermark_date = feed_meta["last_pubdate_utc"] - timedelta(
                    days=self.config.lookback_days
                )

            for entry in feed.entries:
                try:
                    # Extract basic fields
                    title_original = entry.get("title", "").strip()
                    if not title_original:
                        continue

                    # Extract publication date
                    pubdate_utc = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pubdate_utc = datetime(
                            *entry.published_parsed[:6], tzinfo=timezone.utc
                        )
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        pubdate_utc = datetime(
                            *entry.updated_parsed[:6], tzinfo=timezone.utc
                        )

                    # Skip if older than watermark
                    if watermark_date and pubdate_utc and pubdate_utc <= watermark_date:
                        continue

                    # Track latest pubdate
                    if pubdate_utc and (
                        not latest_pubdate or pubdate_utc > latest_pubdate
                    ):
                        latest_pubdate = pubdate_utc

                    # Get Google News URL
                    url_gnews = entry.get("link", entry.get("id", ""))
                    if not url_gnews:
                        continue

                    # B) Extract real publisher from entry.source
                    publisher_name, publisher_domain = self.extract_real_publisher(
                        entry, feed
                    )

                    # A) Normalize title with NFKC
                    title_display, title_norm = self.normalize_title(
                        title_original, publisher_name
                    )

                    # Language detection
                    detected_language, lang_confidence = self.detect_language(
                        title_display
                    )

                    # Generate content hash
                    content_hash = self.generate_content_hash(
                        title_norm, publisher_domain
                    )

                    article = {
                        "feed_id": feed_id,
                        "title_original": title_original,
                        "title_display": title_display,
                        "title_norm": title_norm,
                        "url_gnews": url_gnews,
                        "publisher_name": publisher_name,
                        "publisher_domain": publisher_domain,
                        "pubdate_utc": pubdate_utc,
                        "detected_language": detected_language,
                        "language_confidence": lang_confidence,
                        "content_hash": content_hash,
                    }

                    articles.append(article)
                    stats["fetched"] += 1

                    # Apply max items cap if configured
                    if (
                        self.config.max_items_per_feed
                        and len(articles) >= self.config.max_items_per_feed
                    ):
                        break

                except Exception as e:
                    logger.warning(f"Failed to process entry from {feed_url}: {e}")
                    stats["errors"] += 1
                    continue

            # C) Insert with UPSERT
            insert_stats = self.insert_articles(articles)
            stats.update(insert_stats)

            # Update feed metadata
            self.feeds_repo.upsert(
                feed_url,
                etag=etag,
                last_modified=last_modified,
                last_pubdate_utc=latest_pubdate,
            )

            stats["duration_sec"] = time.time() - start_time

            # F) Provenance/logging
            logger.info(
                f"Feed processing complete: {feed_url} - fetched: {stats['fetched']}, inserted: {stats['inserted']}, skipped: {stats['skipped']}, errors: {stats['errors']}, duration: {stats['duration_sec']:.2f}s"
            )

            return articles, stats

        except Exception as e:
            stats["duration_sec"] = time.time() - start_time
            logger.error(f"Error processing feed {feed_url}: {e}")
            return [], stats

    def insert_articles(self, articles: List[Dict]) -> Dict[str, int]:
        """
        C) Idempotent UPSERT with unique constraint
        """
        if not articles:
            return {"inserted": 0, "skipped": 0}

        stats = {"inserted": 0, "skipped": 0}

        try:
            with get_db_session() as session:
                for article in articles:
                    # C) INSERT ... ON CONFLICT DO NOTHING for idempotency
                    result = session.execute(
                        text(
                            """
                        INSERT INTO titles (
                            feed_id, title_original, title_display, title_norm, url_gnews,
                            publisher_name, publisher_domain, pubdate_utc,
                            detected_language, language_confidence, content_hash,
                            processing_status, ingested_at, created_at
                        ) VALUES (
                            :feed_id, :title_original, :title_display, :title_norm, :url_gnews,
                            :publisher_name, :publisher_domain, :pubdate_utc,
                            :detected_language, :language_confidence, :content_hash,
                            'pending', NOW(), NOW()
                        )
                        ON CONFLICT (content_hash, feed_id) DO NOTHING
                        RETURNING id
                    """
                        ),
                        {
                            "feed_id": article["feed_id"],
                            "title_original": article["title_original"],
                            "title_display": article["title_display"],
                            "title_norm": article["title_norm"],
                            "url_gnews": article["url_gnews"],
                            "publisher_name": article["publisher_name"],
                            "publisher_domain": article["publisher_domain"],
                            "pubdate_utc": article["pubdate_utc"],
                            "detected_language": article["detected_language"],
                            "language_confidence": article["language_confidence"],
                            "content_hash": article["content_hash"],
                        },
                    )

                    if result.fetchone():
                        stats["inserted"] += 1
                    else:
                        stats["skipped"] += 1

        except Exception as e:
            logger.error(f"Database error inserting articles: {e}")
            raise

        return stats
