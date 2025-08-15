#!/usr/bin/env python3
"""
Progressive Full-Text Fetch System
Strategic Narrative Intelligence ETL Pipeline

Fetches full article content for likely snippets using existing schema:
- language (not language_code)
- word_count
- ingestion_status
"""

import argparse
import asyncio
# Add project root to path
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp
import structlog
from bs4 import BeautifulSoup
from sqlalchemy import text

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database

logger = structlog.get_logger(__name__)


class ProgressiveFullTextFetcher:
    """Progressive full-text fetcher for likely snippets"""

    def __init__(self):
        self.config = get_config()
        initialize_database(self.config.database)

        # Fetching configuration
        self.timeout = 30
        self.max_retries = 2
        self.user_agent = "Strategic-Narrative-Intelligence/1.0"

        # Processing stats
        self.stats = {
            "candidates_found": 0,
            "fetch_attempted": 0,
            "full_ok": 0,
            "full_empty": 0,
            "full_paywall": 0,
            "full_error": 0,
            "deleted_low_quality": 0,
        }

    async def fetch_progressive_fulltext(self, window_hours: int = 72) -> dict:
        """
        Main progressive fetch workflow

        Args:
            window_hours: Time window to process articles

        Returns:
            Processing statistics
        """
        logger.info(f"Starting progressive full-text fetch for {window_hours}h window")
        start_time = time.time()

        # Get candidate articles for full-text fetch
        candidates = self._get_fetch_candidates(window_hours)
        self.stats["candidates_found"] = len(candidates)

        if not candidates:
            logger.info("No articles need full-text fetching")
            return self.stats

        logger.info(f"Found {len(candidates)} articles needing full-text fetch")

        # Process articles in batches
        batch_size = 10
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i : i + batch_size]
            logger.info(
                f"Processing batch {i//batch_size + 1}/{(len(candidates) + batch_size - 1)//batch_size}"
            )

            # Process batch concurrently
            tasks = [
                self._fetch_single_article(article_id, url) for article_id, url in batch
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Brief pause between batches
            await asyncio.sleep(1)

        # Backfill word_count if needed
        self._backfill_word_counts(window_hours)

        # Clean up low-quality articles that can't be salvaged
        self._cleanup_low_quality_articles(window_hours)

        duration = time.time() - start_time
        logger.info(f"Progressive fetch completed in {duration:.2f}s", **self.stats)

        return self.stats

    def _get_fetch_candidates(self, window_hours: int) -> List[Tuple[str, str]]:
        """Get articles needing full-text fetch"""

        with get_db_session() as session:
            # For progressive fetch, we can be more targeted and get articles
            # that actually need fetching (regardless of window if window_hours is 0)
            if window_hours > 0:
                time_filter = (
                    f"AND published_at >= now() - interval '{window_hours} hours'"
                )
            else:
                time_filter = ""  # Process all articles that need fetching

            result = session.execute(
                text(
                    f"""
                SELECT id, url
                FROM articles
                WHERE language = 'EN'
                  {time_filter}
                  AND (word_count IS NULL OR word_count < 50)
                  AND (ingestion_status IS NULL OR ingestion_status = 'PENDING')
                  AND url IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1000
            """
                )
            )

            return [(str(row[0]), row[1]) for row in result.fetchall()]

    async def _fetch_single_article(self, article_id: str, url: str) -> None:
        """Fetch full text for a single article"""

        self.stats["fetch_attempted"] += 1

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:

                    headers = {
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate",
                        "Connection": "keep-alive",
                    }

                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            extracted_text = self._extract_article_content(html_content)

                            if extracted_text:
                                status = self._classify_extraction_result(
                                    extracted_text
                                )
                                word_count = self._calculate_word_count(extracted_text)

                                # Update database with proper enum values
                                self._update_article_content(
                                    article_id, extracted_text, word_count, status
                                )

                                # Map status to stats tracking (use original logic for stats)
                                if status == "COMPLETED":
                                    self.stats["full_ok"] += 1
                                else:
                                    self.stats["full_empty"] += 1
                                logger.debug(
                                    f"Fetched {article_id}: {status} ({word_count} words)"
                                )
                                return
                            else:
                                self._update_article_status(article_id, "FAILED")
                                self.stats["full_empty"] += 1
                                return

                        elif response.status == 403 or response.status == 402:
                            self._update_article_status(article_id, "FAILED")
                            self.stats["full_paywall"] += 1
                            return
                        else:
                            if attempt == self.max_retries - 1:
                                self._update_article_status(article_id, "FAILED")
                                self.stats["full_error"] += 1
                                return

            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url}: {e}")
                    self._update_article_status(article_id, "FAILED")
                    self.stats["full_error"] += 1
                    return

                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _extract_article_content(self, html_content: str) -> Optional[str]:
        """Extract article content from HTML"""

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove unwanted elements
            for tag in soup(
                ["script", "style", "nav", "header", "footer", "aside", "advertisement"]
            ):
                tag.decompose()

            # Try multiple content extraction strategies
            content_selectors = [
                "article",
                '[role="main"]',
                ".article-content",
                ".post-content",
                ".entry-content",
                ".content",
                ".story-body",
                ".article-body",
                "main",
            ]

            # Strategy 1: Try semantic selectors
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    text = content_element.get_text(separator=" ", strip=True)
                    if len(text.split()) >= 100:  # Minimum viable article length
                        return self._clean_extracted_text(text)

            # Strategy 2: Fallback to body with paragraph filtering
            paragraphs = soup.find_all("p")
            if paragraphs:
                paragraph_texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 30:  # Filter very short paragraphs
                        paragraph_texts.append(text)

                if paragraph_texts:
                    full_text = " ".join(paragraph_texts)
                    if len(full_text.split()) >= 50:
                        return self._clean_extracted_text(full_text)

            # Strategy 3: Final fallback to body text
            body = soup.find("body")
            if body:
                text = body.get_text(separator=" ", strip=True)
                if len(text.split()) >= 50:
                    return self._clean_extracted_text(text)

            return None

        except Exception as e:
            logger.error(f"HTML extraction failed: {e}")
            return None

    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text"""

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common boilerplate patterns
        boilerplate_patterns = [
            r"Subscribe to our newsletter.*?$",
            r"Sign up for.*?$",
            r"Follow us on.*?$",
            r"Copyright.*?$",
            r"All rights reserved.*?$",
            r"Click here.*?$",
            r"Read more.*?$",
            r"Advertisement\s*$",
        ]

        for pattern in boilerplate_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

        # Clean and normalize
        text = text.strip()

        return text

    def _classify_extraction_result(self, text: str) -> str:
        """Classify extraction result quality - map to actual enum values"""

        word_count = len(text.split())

        # Check for paywall indicators
        paywall_indicators = [
            "subscribe to continue",
            "premium subscriber",
            "paywall",
            "sign in to read",
            "become a subscriber",
        ]

        text_lower = text.lower()
        if any(indicator in text_lower for indicator in paywall_indicators):
            return "FAILED"  # Paywall = failed fetch

        # Check content quality
        if word_count < 30:
            return "FAILED"  # Empty/insufficient content = failed
        elif word_count >= 50:
            return "COMPLETED"  # Good content = completed successfully
        else:
            return "FAILED"  # Marginal content = failed

    def _calculate_word_count(self, text: str) -> int:
        """Calculate word count from text"""
        return len(text.split())

    def _update_article_content_only(
        self, article_id: str, content: str, word_count: int
    ):
        """Update article with extracted content (skip status due to enum constraints)"""

        with get_db_session() as session:
            session.execute(
                text(
                    """
                UPDATE articles 
                SET content = :content,
                    word_count = :word_count
                WHERE id = :article_id
            """
                ),
                {
                    "content": content,
                    "word_count": word_count,
                    "article_id": article_id,
                },
            )
            session.commit()

    def _update_article_content(
        self, article_id: str, content: str, word_count: int, status: str
    ):
        """Update article with extracted content"""

        with get_db_session() as session:
            session.execute(
                text(
                    """
                UPDATE articles 
                SET content = :content,
                    word_count = :word_count,
                    ingestion_status = :status
                WHERE id = :article_id
            """
                ),
                {
                    "content": content,
                    "word_count": word_count,
                    "status": status,
                    "article_id": article_id,
                },
            )
            session.commit()

    def _update_article_status(self, article_id: str, status: str):
        """Update article ingestion status only"""

        with get_db_session() as session:
            session.execute(
                text(
                    """
                UPDATE articles 
                SET ingestion_status = :status
                WHERE id = :article_id
            """
                ),
                {"status": status, "article_id": article_id},
            )
            session.commit()

    def _backfill_word_counts(self, window_hours: int):
        """Backfill word_count for articles with content but missing word_count"""

        with get_db_session() as session:
            result = session.execute(
                text(
                    f"""
                UPDATE articles
                SET word_count = COALESCE(
                    word_count, 
                    CASE 
                        WHEN content IS NOT NULL AND length(content) > 0 THEN
                            array_length(string_to_array(regexp_replace(content, '\\s+', ' ', 'g'), ' '), 1)
                        ELSE 0
                    END
                )
                WHERE language = 'EN' 
                  AND published_at >= now() - interval '{window_hours} hours'
                  AND content IS NOT NULL 
                  AND word_count IS NULL
            """
                )
            )

            updated_count = result.rowcount
            session.commit()

            if updated_count > 0:
                logger.info(f"Backfilled word_count for {updated_count} articles")

    def _cleanup_low_quality_articles(self, window_hours: int):
        """Delete articles that are unsalvageable low quality"""

        with get_db_session() as session:
            # Delete articles that meet deletion criteria:
            # 1. word_count < 50 AND summary too short (< 50 words)
            # 2. ingestion_status indicates unusable content
            # 3. Empty content after fetch attempts

            result = session.execute(
                text(
                    f"""
                DELETE FROM articles 
                WHERE language = 'EN'
                  AND published_at >= now() - interval '{window_hours} hours'
                  AND (
                    -- Case 1: Short content with inadequate summary
                    (COALESCE(word_count, 0) < 50 AND 
                     (summary IS NULL OR array_length(string_to_array(summary, ' '), 1) < 50))
                    OR
                    -- Case 2: Failed fetch attempts - no viable content
                    ingestion_status = 'FAILED'
                    OR
                    -- Case 3: Empty content after processing
                    (COALESCE(content, '') = '' AND COALESCE(summary, '') = '')
                  )
                  -- Safety: Don't delete if it has extracted keywords (already processed)
                  AND id NOT IN (SELECT DISTINCT article_id FROM article_keywords WHERE article_id IS NOT NULL)
            """
                )
            )

            deleted_count = result.rowcount
            session.commit()

            self.stats["deleted_low_quality"] = deleted_count

            if deleted_count > 0:
                logger.info(
                    f"Deleted {deleted_count} low-quality articles to maintain KPI accuracy"
                )


async def main():
    """CLI interface for progressive full-text fetching"""

    parser = argparse.ArgumentParser(description="Progressive Full-Text Fetch")
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )

    args = parser.parse_args()

    fetcher = ProgressiveFullTextFetcher()

    try:
        stats = await fetcher.fetch_progressive_fulltext(args.window)

        print("\n=== Progressive Full-Text Fetch Results ===")
        print(f"Candidates found: {stats['candidates_found']}")
        print(f"Fetch attempted: {stats['fetch_attempted']}")
        print(f"Success (full_ok): {stats['full_ok']}")
        print(f"Empty content: {stats['full_empty']}")
        print(f"Paywalled: {stats['full_paywall']}")
        print(f"Errors: {stats['full_error']}")
        print(f"Deleted low-quality: {stats['deleted_low_quality']}")

        success_rate = (
            (stats["full_ok"] / stats["fetch_attempted"] * 100)
            if stats["fetch_attempted"] > 0
            else 0
        )
        print(f"Success rate: {success_rate:.1f}%")

        return 0 if stats["full_ok"] > 0 else 1

    except Exception as e:
        logger.error(f"Progressive fetch failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
