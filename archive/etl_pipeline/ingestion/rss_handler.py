"""
RSS Feed Handler
Strategic Narrative Intelligence ETL Pipeline

Handler for RSS and Google RSS feeds using the registry pattern.
"""

import asyncio
from datetime import datetime
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
    - "Reuters Sitemap Sitemap" → "Reuters"
    - "BBC World News" → "BBC World News" (unchanged)
    """

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


def clean_source_attribution(text: str, feed_name: str) -> str:
    """
    Dynamically clean source attributions from article content using feed name
    
    Removes source names and separators from the END of titles, summaries, and content.
    Works with all feed types (RSS, Google RSS, XML sitemap) and handles various 
    separator patterns (-, :, |, parentheses, etc.).
    
    Args:
        text: The text to clean (title, summary, or content)
        feed_name: The feed name from database (e.g., "DW", "zerohedge.com", "The Washington Post")
    
    Examples:
        - clean_source_attribution("Article title - DW", "DW") -> "Article title"
        - clean_source_attribution("News story: NPR", "NPR") -> "News story"
        - clean_source_attribution("Story zerohedge.com", "zerohedge.com") -> "Story"
        - clean_source_attribution("News - The Washington Post", "The Washington Post") -> "News"
    """
    if not text or not feed_name:
        return text
    
    import re
    
    clean_feed_name = clean_source_name(feed_name)
    
    # Create comprehensive patterns to remove source attributions at the end
    patterns_to_remove = []
    
    # 1. Website domains (e.g., "zerohedge.com", "afp.com") - always remove regardless of feed name
    patterns_to_remove.append(r'\s+[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$')
    
    # 2. Exact feed name with various separators (most common patterns first)
    separators = [
        r'\s*-\s*',      # " - DW", "News - CNN"  
        r'\s*:\s*',      # " : NPR", "Story: Reuters"
        r'\s*\|\s*',     # " | BBC", "Article | AP"
        r'\s*\(\s*',     # " (Reuters", "News (AP"
        r'\s*\[\s*',     # " [Source", "Story [BBC"
        r'\s*\u2013\s*', # en-dash
        r'\s*\u2014\s*', # em-dash
        r'\s+',          # Just space: "Article DW", "News NPR"
    ]
    
    for sep in separators:
        # With separator + feed name
        patterns_to_remove.append(sep + re.escape(clean_feed_name) + r'(\s*\))?(\s*\])?$')
        
        # Handle variations with "The" prefix - both ways
        if clean_feed_name.startswith('The '):
            # Feed is "The Washington Post", also match "Washington Post" 
            base_name = clean_feed_name[4:]  # Remove "The "
            patterns_to_remove.append(sep + re.escape(base_name) + r'(\s*\))?(\s*\])?$')
        else:
            # Feed is "Washington Post", also match "The Washington Post"
            patterns_to_remove.append(sep + r'The\s+' + re.escape(clean_feed_name) + r'(\s*\))?(\s*\])?$')
    
    # 3. Handle parenthetical attributions specifically
    patterns_to_remove.append(r'\s*\(\s*' + re.escape(clean_feed_name) + r'\s*\)$')
    patterns_to_remove.append(r'\s*\[\s*' + re.escape(clean_feed_name) + r'\s*\]$')
    
    cleaned_text = text.strip()
    original_text = cleaned_text
    
    # Apply patterns one by one
    for pattern in patterns_to_remove:
        try:
            new_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE).strip()
            # Safety check: only accept if it leaves substantial content
            if (len(new_text) >= len(original_text) * 0.4 and 
                len(new_text.split()) >= 2 and 
                new_text != cleaned_text):  # Ensure we made a change
                cleaned_text = new_text
                break  # Stop after first successful match
        except re.error:
            # Skip malformed patterns
            continue
    
    # Final cleanup: remove trailing punctuation that might be left behind
    # Include Unicode dashes and other punctuation
    cleaned_text = re.sub(r'[,\-\|\:\[\(\)\]\.\s\u2013\u2014]+$', '', cleaned_text).strip()
    
    # Additional cleanup for cases where punctuation was part of the separator
    # Try removing common trailing patterns that might be left
    trailing_patterns = [
        r'\s*-\s*$',      # trailing dash
        r'\s*:\s*$',      # trailing colon  
        r'\s*\|\s*$',     # trailing pipe
        r'\s*\[\s*$',     # trailing bracket
        r'\s*\(\s*$',     # trailing paren
        r'\s*\u2013\s*$', # trailing en-dash
        r'\s*\u2014\s*$', # trailing em-dash
    ]
    
    for pattern in trailing_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text).strip()
    
    # Return original if cleaning removed too much or left empty
    return cleaned_text if cleaned_text and len(cleaned_text) >= 3 else original_text


def filter_cgtn_cookie_content(content: str) -> str:
    """
    Filter out CGTN cookie consent paragraphs from article content
    
    Removes: "By continuing to browse our site you agree to our use of cookies, 
    revised Privacy Policy and Terms of Use. You can change your cookie settings through your browser."
    """
    if not content:
        return ""
    
    # CGTN cookie consent text patterns
    cookie_patterns = [
        r"By continuing to browse our site you agree to our use of cookies,?\s*revised Privacy Policy and Terms of Use\.\s*You can change your cookie settings through your browser\.",
        r"By continuing to browse our site you agree to our use of cookies[^.]*\.\s*You can change your cookie settings[^.]*\.",
        # More generic pattern for similar consent text
        r"By continuing to browse[^.]*cookies[^.]*browser\."
    ]
    
    import re
    
    filtered_content = content
    for pattern in cookie_patterns:
        filtered_content = re.sub(pattern, '', filtered_content, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up extra whitespace that might be left behind
    filtered_content = re.sub(r'\s+', ' ', filtered_content).strip()
    
    return filtered_content


def strip_html_content(html_content: str) -> str:
    """
    Strip HTML tags and clean up content for temporary storage

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

                # Clean source attributions from all fields (applies to all feed types)
                if article.title:
                    article.title = clean_source_attribution(article.title, feed_name)
                    
                if article.content:
                    # Filter CGTN cookie consent for all feeds
                    article.content = filter_cgtn_cookie_content(article.content)
                    article.content = clean_source_attribution(article.content, feed_name)
                    
                if article.summary:
                    article.summary = clean_source_attribution(article.summary, feed_name)

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


