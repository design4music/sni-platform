"""
RSS Feed Fetcher for SNI v3

Simplified ingestion adapted for titles_v3 schema:
- NFKC normalization
- Real publisher extraction from Google News
- UPSERT with content-based deduplication
- Conditional GET with ETag/Last-Modified
- Watermark-based incremental fetching
"""

import hashlib
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser
import psycopg2
import requests
from langdetect import DetectorFactory, detect

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.publisher_filter import clean_title_display, load_title_cleaning_patterns

from .feeds_repo import FeedsRepo

# Set seed for consistent language detection
DetectorFactory.seed = 42


class RSSFetcher:
    """RSS feed fetcher for v3 pipeline"""

    def __init__(self):
        self.config = config
        self.feeds_repo = FeedsRepo()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "SNI-v3 RSS Fetcher/1.0 (Headlines Analysis)"}
        )
        # Load publisher patterns for title cleaning (lazy load on first use)
        self._title_cleaning_patterns = None

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )

    def get_title_cleaning_patterns(self) -> set:
        """Load title cleaning patterns (lazy, cached)"""
        if self._title_cleaning_patterns is None:
            conn = self.get_connection()
            try:
                self._title_cleaning_patterns = load_title_cleaning_patterns(conn)
                print(
                    f"Loaded {len(self._title_cleaning_patterns)} title cleaning patterns"
                )
            finally:
                conn.close()
        return self._title_cleaning_patterns

    def normalize_title(
        self, title: str, publisher_name: str = None
    ) -> Tuple[str, str]:
        """
        Unicode & suffix normalization with NFKC.

        Returns:
            (title_display, content_hash_base)
        """
        if not title:
            return "", ""

        # Unicode NFKC normalization
        title = unicodedata.normalize("NFKC", title).strip()

        # Strip trailing publisher patterns
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

        # For deduplication: lowercase + remove non-informative symbols
        hash_base = title_display.lower()
        hash_base = re.sub(r"[^\w\s\-.,!?:;]", "", hash_base)
        hash_base = re.sub(r"\s+", " ", hash_base).strip()

        return title_display, hash_base

    def detect_language(self, text: str) -> Optional[str]:
        """Detect language with graceful failure handling"""
        try:
            if not text or len(text.strip()) < 3:
                return None
            return detect(text)
        except Exception:
            return None

    def extract_real_publisher(
        self, entry, feed
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract real publisher from Google News entry.

        Returns:
            (publisher_name, publisher_domain)
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
                except Exception:
                    pass

        # Fallback to feed title if entry.source missing
        if not publisher_name and hasattr(feed, "feed") and hasattr(feed.feed, "title"):
            publisher_name = feed.feed.title.strip()

        return publisher_name, publisher_domain

    def generate_content_hash(self, hash_base: str, publisher_domain: str) -> str:
        """Generate content hash for deduplication"""
        content = f"{hash_base}||{publisher_domain or ''}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def fetch_with_retries(
        self, feed_url: str, headers: Dict
    ) -> Optional[requests.Response]:
        """Fetch with exponential backoff retries"""
        for attempt in range(self.config.http_retries):
            try:
                response = self.session.get(
                    feed_url, headers=headers, timeout=self.config.http_timeout_sec
                )

                # 304 Not Modified - short circuit
                if response.status_code == 304:
                    print(f"Feed not modified (304): {feed_url}")
                    return response

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                if attempt == self.config.http_retries - 1:
                    print(
                        f"HTTP error after {self.config.http_retries} attempts for {feed_url}: {e}"
                    )
                    raise

                # Exponential backoff with jitter
                delay = (2**attempt) + random.uniform(0, 1)
                print(
                    f"HTTP error attempt {attempt + 1}/{self.config.http_retries} for {feed_url}: {e}. Retrying in {delay:.1f}s"
                )
                time.sleep(delay)

        return None

    def fetch_feed(self, feed_id: str, feed_url: str) -> Tuple[List[Dict], Dict]:
        """
        Fetch and parse RSS feed.

        Returns:
            (articles, stats)
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

            print(f"Fetching RSS feed: {feed_url}")

            # Fetch with retries
            response = self.fetch_with_retries(feed_url, headers)
            if not response:
                return [], stats

            # Handle 304 Not Modified
            if response.status_code == 304:
                self.feeds_repo.upsert(feed_url)
                stats["duration_sec"] = time.time() - start_time
                return [], stats

            # Parse RSS
            feed = feedparser.parse(response.content)

            if feed.bozo and feed.bozo_exception:
                print(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")

            # Extract ETag and Last-Modified for next request
            etag = response.headers.get("ETag")
            last_modified = response.headers.get("Last-Modified")

            articles = []
            latest_pubdate = feed_meta.get("last_pubdate_utc")

            # Watermark for incremental fetching
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

                    # Extract real publisher from entry.source
                    publisher_name, publisher_domain = self.extract_real_publisher(
                        entry, feed
                    )

                    # Normalize title with NFKC
                    title_display, hash_base = self.normalize_title(
                        title_original, publisher_name
                    )

                    # Clean publisher artifacts from title
                    patterns = self.get_title_cleaning_patterns()
                    title_display = clean_title_display(title_display, patterns)

                    # Language detection
                    detected_language = self.detect_language(title_display)

                    # Generate content hash for deduplication
                    content_hash = self.generate_content_hash(
                        hash_base, publisher_domain
                    )

                    article = {
                        "title_display": title_display,
                        "url_gnews": url_gnews,
                        "publisher_name": publisher_name,
                        "pubdate_utc": pubdate_utc,
                        "detected_language": detected_language,
                        "content_hash": content_hash,
                        "feed_id": feed_id,
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
                    print(f"Failed to process entry from {feed_url}: {e}")
                    stats["errors"] += 1
                    continue

            # Insert articles
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

            print(
                f"Feed complete: {feed_url} - fetched: {stats['fetched']}, inserted: {stats['inserted']}, skipped: {stats['skipped']}, errors: {stats['errors']}, duration: {stats['duration_sec']:.2f}s"
            )

            return articles, stats

        except Exception as e:
            stats["duration_sec"] = time.time() - start_time
            print(f"Error processing feed {feed_url}: {e}")
            return [], stats

    def insert_articles(self, articles: List[Dict]) -> Dict[str, int]:
        """
        Insert articles into titles_v3 with idempotent UPSERT.

        Uses content_hash for deduplication across the entire database.
        """
        if not articles:
            return {"inserted": 0, "skipped": 0}

        stats = {"inserted": 0, "skipped": 0}

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                for article in articles:
                    # UPSERT: Insert only if exact title doesn't exist
                    # Strict dedup: same title_display = duplicate (regardless of publisher)
                    # Also check tombstone table to prevent re-ingesting purged titles
                    cur.execute(
                        """
                        INSERT INTO titles_v3 (
                            title_display, url_gnews, publisher_name, pubdate_utc,
                            detected_language, feed_id, processing_status,
                            created_at, updated_at
                        )
                        SELECT %s, %s, %s, %s, %s, %s, 'pending', NOW(), NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM titles_v3
                            WHERE title_display = %s
                        )
                        AND NOT EXISTS (
                            SELECT 1 FROM titles_purged
                            WHERE url_hash = md5(%s)
                        )
                        RETURNING id
                    """,
                        (
                            article["title_display"],
                            article["url_gnews"],
                            article["publisher_name"],
                            article["pubdate_utc"],
                            article["detected_language"],
                            article.get("feed_id"),
                            # Strict deduplication: same title = duplicate
                            article["title_display"],
                            # Tombstone check
                            article["url_gnews"],
                        ),
                    )

                    row = cur.fetchone()
                    if row:
                        stats["inserted"] += 1
                    else:
                        stats["skipped"] += 1

            conn.commit()

        except Exception as e:
            print(f"Database error inserting articles: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

        return stats
