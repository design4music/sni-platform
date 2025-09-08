"""
XML Sitemap Handler
Strategic Narrative Intelligence ETL Pipeline

Handler for XML sitemaps using the registry pattern.
Supports sitemap indexes, gzipped content, and robust parsing.
"""

from datetime import datetime
from typing import Optional, Tuple

import structlog

from .db_utils import save_article_from_sitemap
from .handlers import BaseFeedHandler, register
from .rss_handler import clean_source_name
from .sitemap_utils import fetch_sitemap_urls

logger = structlog.get_logger(__name__)


@register("xml_sitemap")
class XMLSitemapHandler(BaseFeedHandler):
    """
    Handler for XML sitemap feeds

    Features:
    - Sitemap index support
    - Gzipped content handling
    - URL normalization and deduplication
    - Timezone-aware processing
    - Error resilient parsing
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
        Ingest articles from XML sitemap

        Args:
            feed_id: Database feed ID
            feed_name: Human-readable feed name
            feed_url: Sitemap URL
            hours_lookback: Hours to look back for new content
            max_articles: Maximum articles to process

        Returns:
            Tuple of (new_articles, duplicates, errors)
        """
        logger.info(f"Processing XML sitemap: {feed_name} ({feed_url})")

        # Clean source name for database storage
        clean_name = clean_source_name(feed_name)

        try:
            # For now, convert last_fetched_at to hours for sitemap compatibility
            # TODO: Implement proper timestamp-based sitemap filtering
            hours_lookback = 24  # Default fallback
            if last_fetched_at:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                hours_since_last = (now - last_fetched_at).total_seconds() / 3600
                hours_lookback = max(int(hours_since_last), 1)
            
            # Fetch URLs from sitemap
            urls_with_dates = fetch_sitemap_urls(
                sitemap_url=feed_url,
                hours_lookback=hours_lookback,
                max_urls=max_articles,
            )

            if not urls_with_dates:
                logger.debug(f"No recent URLs found in sitemap: {feed_name}")
                return 0, 0, 0

            logger.info(f"Found {len(urls_with_dates)} recent URLs in {feed_name}")

            # Process each URL
            new_count = 0
            duplicate_count = 0
            error_count = 0

            for url, published_at in urls_with_dates:
                try:
                    result = save_article_from_sitemap(
                        feed_id=feed_id,
                        url=url,
                        published_at=published_at,
                        source_name=clean_name,
                    )

                    if result == "new":
                        new_count += 1
                    elif result == "duplicate":
                        duplicate_count += 1
                    else:  # error
                        error_count += 1

                except Exception as e:
                    logger.debug(f"Error processing URL {url}: {e}")
                    error_count += 1

            logger.info(
                f"XML sitemap {feed_name}: "
                f"{new_count} new, {duplicate_count} duplicates, {error_count} errors"
            )

            return new_count, duplicate_count, error_count

        except Exception as e:
            logger.error(f"Failed to process XML sitemap {feed_name}: {e}")
            return 0, 0, 1

    def get_handler_name(self) -> str:
        """Get human-readable handler name"""
        return "XML Sitemap Handler"
