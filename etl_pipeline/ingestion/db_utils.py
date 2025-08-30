"""
Database Utilities for Unified Ingestion
Strategic Narrative Intelligence ETL Pipeline

Provides UPSERT operations and article management for multiple feed types.
"""

import hashlib
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import text

from ..core.database import get_db_session
from .base import RawArticle
from .sitemap_utils import normalize_url

logger = structlog.get_logger(__name__)


def _now_utc() -> datetime:
    """Get current time in UTC with timezone info"""
    return datetime.now(timezone.utc)


def save_article_from_sitemap(
    feed_id: str, url: str, published_at: datetime, source_name: str
) -> str:
    """
    Save article from XML sitemap using UPSERT pattern

    Args:
        feed_id: UUID of the news feed
        url: Article URL (will be normalized)
        published_at: Publication datetime (UTC)
        source_name: Name of news source

    Returns:
        "new", "duplicate", or "error"
    """
    try:
        normalized_url = normalize_url(url)

        # Ensure published_at is UTC
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        else:
            published_at = published_at.astimezone(timezone.utc)

        with get_db_session() as session:
            # UPSERT: Insert if not exists, ignore if exists
            result = session.execute(
                text(
                    """
                INSERT INTO articles (
                    id, feed_id, title, content, summary, url, published_at,
                    language, word_count, content_hash, title_hash, 
                    source_name, created_at, processing_status
                )
                VALUES (
                    :id, :feed_id, :title, :content, :summary, :url, :published_at,
                    :language, :word_count, :content_hash, :title_hash,
                    :source_name, :created_at, :processing_status
                )
                ON CONFLICT (LOWER(url)) DO NOTHING
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "feed_id": feed_id,
                    "title": "[TITLE NEEDED]",  # Placeholder for enrichment
                    "content": None,  # Will be populated by enrichment
                    "summary": None,
                    "url": normalized_url,
                    "published_at": published_at,
                    "language": "EN",  # Default language for sitemap articles
                    "word_count": None,  # Will be calculated by enrichment
                    "content_hash": hashlib.sha256(
                        f"sitemap_content_{normalized_url}".encode()
                    ).hexdigest(),
                    "title_hash": hashlib.sha256(
                        f"sitemap_title_{normalized_url}".encode()
                    ).hexdigest(),
                    "source_name": source_name,
                    "created_at": _now_utc(),
                    "processing_status": "PENDING",  # Ready for enrichment
                },
            )

            # Check if row was inserted (rowcount > 0 means new insert)
            if result.rowcount > 0:
                logger.debug(f"Saved new article from sitemap: {normalized_url}")
                return "new"
            else:
                logger.debug(f"Article already exists: {normalized_url}")
                return "duplicate"

    except Exception as e:
        logger.error(f"Error saving article from sitemap {url}: {e}")
        return "error"


def get_or_create_sitemap_feed(
    session, source_name: str, sitemap_url: str, priority: int = 3
) -> str:
    """
    Get existing sitemap feed ID or create new one

    Args:
        session: Database session
        source_name: Human-readable source name
        sitemap_url: URL to XML sitemap
        priority: Feed priority (1=high, 5=low)

    Returns:
        Feed ID (UUID string)
    """
    # Check if feed exists
    result = session.execute(
        text("SELECT id FROM news_feeds WHERE url = :url"), {"url": sitemap_url}
    )
    existing = result.fetchone()

    if existing:
        return str(existing[0])

    # Create new sitemap feed
    feed_id = str(uuid.uuid4())

    session.execute(
        text(
            """
        INSERT INTO news_feeds (
            id, name, url, feed_type, language, is_active, 
            priority, created_at
        )
        VALUES (
            :id, :name, :url, :feed_type, :language, :is_active,
            :priority, :created_at
        )
    """
        ),
        {
            "id": feed_id,
            "name": f"{source_name} Sitemap",
            "url": sitemap_url,
            "feed_type": "xml_sitemap",
            "language": "EN",  # Default, can be enhanced later
            "is_active": True,
            "priority": priority,
            "created_at": _now_utc(),
        },
    )

    logger.info(f"Created new sitemap feed: {source_name} ({sitemap_url})")
    return feed_id


def get_active_feeds_by_type(feed_type: str) -> list:
    """
    Get all active feeds of specified type

    Args:
        feed_type: Type of feed ("rss", "xml_sitemap", etc.)

    Returns:
        List of (feed_id, name, url, priority) tuples
    """
    try:
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT id, name, url, priority 
                FROM news_feeds 
                WHERE feed_type = :feed_type 
                AND is_active = true
                ORDER BY priority, name
            """
                ),
                {"feed_type": feed_type},
            )

            return [
                (str(fid), name, url, priority)
                for fid, name, url, priority in result.fetchall()
            ]

    except Exception as e:
        logger.error(f"Error fetching {feed_type} feeds: {e}")
        return []


def add_sitemap_feed(name: str, sitemap_url: str, priority: int = 3) -> str:
    """
    Add a new XML sitemap feed to the database

    Args:
        name: Human-readable feed name
        sitemap_url: URL to the XML sitemap
        priority: Feed priority (1=high, 5=low)

    Returns:
        Feed ID of created feed

    Raises:
        ValueError: If feed already exists
    """
    try:
        with get_db_session() as session:
            feed_id = get_or_create_sitemap_feed(session, name, sitemap_url, priority)
            return feed_id

    except Exception as e:
        logger.error(f"Error adding XML sitemap feed: {e}")
        raise


def get_pending_articles_count() -> int:
    """
    Get count of articles pending enrichment

    Returns:
        Number of articles with processing_status = 'PENDING'
    """
    try:
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT COUNT(*) 
                FROM articles 
                WHERE processing_status = 'PENDING'
            """
                )
            )
            return result.fetchone()[0]

    except Exception as e:
        logger.error(f"Error counting pending articles: {e}")
        return 0


def save_article_from_rss(feed_id: str, article: RawArticle, source_name: str) -> str:
    """
    Save article from RSS feed using UPSERT pattern

    Args:
        feed_id: UUID of the news feed
        article: RawArticle object from RSS ingestion
        source_name: Name of news source

    Returns:
        "new", "duplicate", or "error"
    """
    try:
        # Normalize URL
        normalized_url = normalize_url(article.url)

        # Ensure published_at is UTC
        published_at = article.published_at
        if published_at:
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            else:
                published_at = published_at.astimezone(timezone.utc)
        else:
            published_at = _now_utc()  # Default to now if no date

        # Calculate hashes for deduplication
        content_for_hash = f"{article.title}{normalized_url}"
        content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
        title_hash = hashlib.sha256(article.title.encode()).hexdigest()

        # Calculate word count
        word_count = None
        if article.content:
            word_count = len(article.content.split())

        with get_db_session() as session:
            # UPSERT: Insert if not exists, ignore if exists
            result = session.execute(
                text(
                    """
                INSERT INTO articles (
                    id, feed_id, title, content, summary, url, published_at,
                    language, word_count, content_hash, title_hash, 
                    source_name, author, created_at, processing_status
                )
                VALUES (
                    :id, :feed_id, :title, :content, :summary, :url, :published_at,
                    :language, :word_count, :content_hash, :title_hash,
                    :source_name, :author, :created_at, :processing_status
                )
                ON CONFLICT (LOWER(url)) DO NOTHING
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "feed_id": feed_id,
                    "title": article.title,
                    "content": article.content,
                    "summary": article.summary,
                    "url": normalized_url,
                    "published_at": published_at,
                    "language": (
                        "EN" if article.language == "en" else "EN"
                    ),  # Convert to enum format
                    "word_count": word_count,
                    "content_hash": content_hash,
                    "title_hash": title_hash,
                    "source_name": source_name,
                    "author": article.author,
                    "created_at": _now_utc(),
                    "processing_status": "PENDING",  # Ready for enrichment
                },
            )

            # Check if row was inserted (rowcount > 0 means new insert)
            if result.rowcount > 0:
                logger.debug(f"Saved new RSS article: {article.title[:50]}...")
                return "new"
            else:
                logger.debug(f"RSS article already exists: {article.title[:50]}...")
                return "duplicate"

    except Exception as e:
        logger.error(f"Error saving RSS article {article.url}: {e}")
        return "error"
