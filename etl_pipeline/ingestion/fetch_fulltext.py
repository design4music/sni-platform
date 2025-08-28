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
import hashlib
import json
# Add project root to path
import os
import re
import sys
import time
import unicodedata
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
import structlog
import tldextract
import trafilatura
import yaml
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

        # Load cleaning configuration
        self.cleaning_config = self._load_cleaning_config()

        # Fetching configuration
        self.timeout = 30
        self.max_retries = 2
        self.user_agent = "Strategic-Narrative-Intelligence/2.0"

        # Processing stats
        self.stats = {
            "candidates_found": 0,
            "fetch_attempted": 0,
            "full_ok": 0,
            "full_empty": 0,
            "full_paywall": 0,
            "full_error": 0,
            "deleted_low_quality": 0,
            # New cleaning stats
            "amp_attempts": 0,
            "amp_success": 0,
            "raw_paragraphs": 0,
            "dropped_by_cookie": 0,
            "dropped_by_menu": 0,
            "dropped_by_promo": 0,
            "dropped_by_timestamp": 0,
            "dropped_by_link_density": 0,
            "dropped_by_uppercase": 0,
            "final_paragraphs": 0,
        }

    def _load_cleaning_config(self) -> dict:
        """Load cleaning configuration from YAML file"""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "ingestion",
                "cleaning.yml",
            )
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded cleaning config from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load cleaning config: {e}, using defaults")
            return self._get_default_cleaning_config()

    def _get_default_cleaning_config(self) -> dict:
        """Fallback cleaning configuration if YAML file not available"""
        return {
            "limits": {"max_content_chars": 50000, "extraction_timeout_seconds": 30},
            "post_filter": {"max_line_link_density": 0.5}
        }


    def _load_feed_profile(self, url: str) -> Optional[dict]:
        """Load learned extraction profile from feed database"""
        try:
            with get_db_session() as db:
                # Try to find profile by exact URL match first
                query = text("""
                    SELECT extraction_profile 
                    FROM news_feeds 
                    WHERE url = :url OR :url LIKE CONCAT('%', REPLACE(url, 'https://', ''), '%')
                    AND extraction_profile IS NOT NULL
                    LIMIT 1
                """)
                result = db.execute(query, {"url": url})
                row = result.fetchone()
                
                if not row:
                    # Try domain-scoped profile
                    domain = tldextract.extract(url).registered_domain
                    query = text("""
                        SELECT extraction_profile 
                        FROM news_feeds 
                        WHERE url LIKE :domain_pattern 
                        AND extraction_profile IS NOT NULL
                        AND extraction_profile->>'scope' = 'domain'
                        LIMIT 1
                    """)
                    result = db.execute(query, {"domain_pattern": f"%{domain}%"})
                    row = result.fetchone()
                
                if row and row[0]:
                    profile = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    logger.debug(f"Loaded learned profile for {url}")
                    return profile
                
                return None
        except Exception as e:
            logger.warning(f"Failed to load learned profile for {url}: {e}")
            return None

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
                  AND (
                    processing_status IS NULL 
                    OR CHAR_LENGTH(content) BETWEEN 50 AND 1500
                  )
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
                            extracted_text = await self._extract_article_content(
                                html_content, url
                            )

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

    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL with proper headers"""
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
                        return await response.text()
            return None
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return None

    def _apply_structural_post_filter(self, text: str) -> str:
        """Apply structural post-filtering to extracted content"""
        if not text:
            return text
            
        # Split into lines for processing
        lines = text.split('\n')
        filtered_lines = []
        seen_lines = set()
        
        # Get link density threshold from config
        max_link_density = self.cleaning_config.get("post_filter", {}).get("max_line_link_density", 0.5)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Normalize whitespace
            line = re.sub(r'\s+', ' ', line)
            
            # Compute link density for this line
            soup_line = BeautifulSoup(f"<p>{line}</p>", "html.parser")
            links = soup_line.find_all("a")
            if links:
                link_text_len = sum(len(link.get_text()) for link in links)
                total_text_len = len(line)
                link_density = link_text_len / total_text_len if total_text_len > 0 else 0
                
                # Drop high-link-density lines
                if link_density > max_link_density:
                    continue
            
            # Collapse repeated identical lines
            line_hash = hashlib.md5(line.lower().encode()).hexdigest()
            if line_hash in seen_lines:
                continue
            seen_lines.add(line_hash)
            
            filtered_lines.append(line)
        
        # Join with double newlines and final normalization
        result = '\n\n'.join(filtered_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)  # Limit paragraph breaks
        
        return result.strip()

    def _extract_with_trafilatura(self, html_content: str, url: str) -> Optional[str]:
        """Extract content using trafilatura with precision settings"""
        try:
            # Extract with trafilatura using precision-focused settings
            extracted = trafilatura.extract(
                html_content,
                url=url,
                favor_precision=True,
                include_links=False,
                include_images=False,
                output_format="txt"
            )
            
            if extracted and len(extracted.strip()) > 100:  # Minimum viable content
                logger.debug(f"Trafilatura extracted {len(extracted)} chars for {url}")
                return extracted
            return None
            
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed for {url}: {e}")
            return None


    def _extract_with_learned_profile(self, html_content: str, profile: dict) -> Optional[str]:
        """Extract content using learned extraction profile with full validation"""
        try:
            # Apply pre-clean regex
            cleaned_html = html_content
            for regex_rule in profile.get("pre_clean_regex", []):
                pattern = regex_rule.get("pattern", "")
                flags = regex_rule.get("flags", "")
                if pattern:
                    re_flags = 0
                    if 'i' in flags: re_flags |= re.IGNORECASE
                    if 'm' in flags: re_flags |= re.MULTILINE
                    if 's' in flags: re_flags |= re.DOTALL
                    cleaned_html = re.sub(pattern, '', cleaned_html, flags=re_flags)
            
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            # Select main content using learned selector
            main_selector = profile.get("main_selector", "")
            main_element = soup.select_one(main_selector)
            if not main_element:
                logger.debug("Learned profile: main selector not found")
                return None
            
            # Remove unwanted selectors
            for selector in profile.get("remove_selectors", []):
                for elem in main_element.select(selector):
                    elem.decompose()
            
            # Keep only allowed tags
            allowed_tags = set(profile.get("allow_tags", ["p", "h2", "h3", "ul", "li", "blockquote"]))
            for tag in main_element.find_all():
                if tag.name not in allowed_tags:
                    tag.unwrap()
            
            # Extract text
            text = main_element.get_text(" ", strip=True)
            
            # Apply post-clean regex
            for regex_rule in profile.get("post_clean_regex", []):
                pattern = regex_rule.get("pattern", "")
                flags = regex_rule.get("flags", "")
                if pattern:
                    re_flags = 0
                    if 'i' in flags: re_flags |= re.IGNORECASE
                    if 'm' in flags: re_flags |= re.MULTILINE
                    text = re.sub(pattern, '', text, flags=re_flags)
            
            # Remove junk phrases
            for phrase in profile.get("junk_phrases", []):
                text = text.replace(phrase, "")
            
            # Calculate metrics
            text_len = len(text)
            html_len = len(str(main_element))
            density = text_len / html_len if html_len > 0 else 0
            
            # Validate against thresholds
            min_length = profile.get("min_length", 150)
            density_threshold = profile.get("density_threshold", 0.12)
            
            if text_len >= min_length and density >= density_threshold:
                logger.debug(f"Learned profile extraction: {text_len} chars, {density:.3f} density")
                return text.strip()
            else:
                logger.debug(f"Learned profile failed validation: {text_len} chars, {density:.3f} density")
                return None
            
        except Exception as e:
            logger.debug(f"Learned profile extraction failed: {e}")
            return None

    async def _extract_article_content(
        self, html_content: str, url: str = None
    ) -> Optional[str]:
        """Extract article content using simplified two-tier architecture: Learned Profiles → Trafilatura"""
        try:
            if not html_content or not url:
                return None
            
            # TIER 1: Learned Profiles - Try LLM-generated extraction profiles first
            learned_profile = self._load_feed_profile(url)
            if learned_profile:
                logger.debug(f"Using learned profile for {url}")
                content = self._extract_with_learned_profile(html_content, learned_profile)
                if content:
                    logger.debug(f"Learned profile extraction: {len(content)} chars for {url}")
                    logger.info(f"Extraction successful", 
                              profile_used=True, extractor="learned_profile", 
                              length=len(content), url=url)
                    return content
            
            # TIER 2: Trafilatura - Universal content extraction fallback
            content = self._extract_with_trafilatura(html_content, url)
            if content:
                content = self._apply_structural_post_filter(content)
                if content and len(content) > 100:
                    logger.debug(f"Trafilatura extraction: {len(content)} chars for {url}")
                    logger.info(f"Extraction successful",
                              profile_used=False, extractor="trafilatura",
                              length=len(content), url=url)
                    return content
            
            # No extraction method succeeded
            logger.debug(f"No extraction method succeeded for {url}")
            logger.info(f"Extraction failed", 
                       profile_used=False, extractor="none", 
                       length=0, url=url)
            return None

        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

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
