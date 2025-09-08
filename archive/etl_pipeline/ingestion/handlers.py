"""
Feed Handler Registry
Strategic Narrative Intelligence ETL Pipeline

Extensible registry pattern for different feed types.
Makes adding new ingestion methods (Google News, APIs, etc.) a single-file change.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Global handler registry
REGISTRY: Dict[str, "BaseFeedHandler"] = {}


def register(feed_type: str):
    """
    Decorator to register feed handlers

    Usage:
        @register("xml_sitemap")
        class SitemapHandler(BaseFeedHandler):
            ...
    """

    def decorator(cls):
        handler_instance = cls()
        REGISTRY[feed_type] = handler_instance
        logger.info(f"Registered handler for feed_type: {feed_type}")
        return cls

    return decorator


class BaseFeedHandler(ABC):
    """
    Base class for feed handlers

    Each feed type (RSS, XML sitemap, API, etc.) implements this interface
    """

    @abstractmethod
    def ingest(
        self,
        feed_id: str,
        feed_name: str,
        feed_url: str,
        last_fetched_at: Optional[datetime] = None,
        max_articles: int = 100,
    ) -> Tuple[int, int, int]:
        """
        Ingest content from feed using incremental approach

        Args:
            feed_id: Database feed ID
            feed_name: Human-readable feed name
            feed_url: Feed URL
            last_fetched_at: Timestamp of last successful fetch (None for new feeds)
            max_articles: Maximum articles to process

        Returns:
            Tuple of (new_articles, duplicates, errors)
        """
        pass

    @abstractmethod
    def get_handler_name(self) -> str:
        """Get human-readable handler name"""
        pass


def get_handler(feed_type: str) -> BaseFeedHandler:
    """
    Get handler for feed type

    Args:
        feed_type: Type of feed (from database)

    Returns:
        Handler instance

    Raises:
        ValueError: If no handler registered for feed type
    """
    if feed_type not in REGISTRY:
        raise ValueError(f"No handler registered for feed_type: {feed_type}")

    return REGISTRY[feed_type]


def list_registered_handlers() -> Dict[str, str]:
    """
    List all registered handlers

    Returns:
        Dict mapping feed_type -> handler_name
    """
    return {
        feed_type: handler.get_handler_name() for feed_type, handler in REGISTRY.items()
    }
