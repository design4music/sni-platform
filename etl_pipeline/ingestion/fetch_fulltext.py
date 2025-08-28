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
            "amp_first_hints": [
                "indiatimes.com",
                "newsus.cgtn.com",
                "dw.com",
                "presstv.ir",
            ],
            "min_par_chars": 25,
            "max_link_density": 0.4,
            "max_upper_ratio": 0.7,
            "menu_upper_ratio": 0.6,
            "menu_min_tokens": 8,
            "min_contiguous_run_chars": 600,
            "stop_phrases": [
                "privacy policy",
                "cookie policy",
                "terms of use",
                "subscribe",
            ],
            "menu_keywords": ["world", "politics", "economy", "business", "sports"],
            "regexes": {
                "timestamp_line": r"^(updated|last\s+updated|published)\s*[-–—:]?.*$",
                "first_line_url": r"^\s*https?://\S+\s*$",
                "also_read": r"^(also\s+read|read\s+more)\b.*",
            },
            "limits": {"max_content_chars": 50000, "max_paragraphs": 100},
        }

    def _load_domain_profile(self, domain: str) -> Optional[dict]:
        """Load domain-specific extraction profile if available"""
        try:
            profile_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "ingestion", 
                "profiles",
                f"{domain}.json"
            )
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile = yaml.safe_load(f)
                logger.debug(f"Loaded domain profile for {domain}")
                return profile
            return None
        except Exception as e:
            logger.warning(f"Failed to load domain profile for {domain}: {e}")
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

    async def _find_amp_url(self, html_content: str, base_url: str) -> Optional[str]:
        """Find AMP version URL if available"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            amp_link = soup.find("link", rel="amphtml")
            if amp_link and amp_link.get("href"):
                amp_url = urljoin(base_url, amp_link["href"])
                logger.debug(f"Found AMP URL: {amp_url}")
                return amp_url
            return None
        except Exception as e:
            logger.debug(f"AMP URL detection failed: {e}")
            return None

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

    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Extract all paragraph-like content from HTML"""
        if not soup:
            return []

        # Remove unwanted elements completely
        for tag in soup(
            ["script", "style", "nav", "header", "footer", "aside", "form"]
        ):
            tag.decompose()

        # Collect text from paragraph-like elements
        paragraphs = []

        # Try structured content first
        for selector in [
            "article",
            '[role="main"]',
            "main",
            ".content",
            ".article-content",
        ]:
            container = soup.select_one(selector)
            if container:
                # Get paragraphs from this container
                for p in container.find_all(["p", "h1", "h2", "h3", "div"]):
                    text = p.get_text(" ", strip=True)
                    if text and len(text) > 10:  # Basic length filter
                        paragraphs.append(text)
                if paragraphs:
                    break

        # Fallback: get all paragraphs from body
        if not paragraphs:
            for p in soup.find_all(["p", "h1", "h2", "h3"]):
                text = p.get_text(" ", strip=True)
                if text and len(text) > 10:
                    paragraphs.append(text)

        return paragraphs[
            : self.cleaning_config.get("limits", {}).get("max_paragraphs", 100)
        ]

    def _clean_paragraphs(
        self, paragraphs: List[str], page_title: str = "", url: str = ""
    ) -> List[str]:
        """Apply generic paragraph-level cleaning filters"""
        if not paragraphs:
            return []

        config = self.cleaning_config
        cleaned_paragraphs = []
        initial_count = len(paragraphs)
        self.stats["raw_paragraphs"] = initial_count

        # Compile regexes once
        timestamp_regex = re.compile(config["regexes"]["timestamp_line"], re.IGNORECASE)
        first_url_regex = re.compile(config["regexes"]["first_line_url"])
        also_read_regex = re.compile(config["regexes"]["also_read"], re.IGNORECASE)

        for i, para in enumerate(paragraphs):
            if not para or not para.strip():
                continue

            para = para.strip()
            original_para = para

            # Apply regex cleaners
            if i == 0 and first_url_regex.match(para):  # First paragraph URL
                continue

            if timestamp_regex.match(para):  # Timestamp lines
                self.stats["dropped_by_timestamp"] += 1
                continue

            if also_read_regex.match(para):  # Also read lines
                continue

            # Unicode normalization
            para = unicodedata.normalize("NFKC", para)

            # Basic length filter
            if len(para) < config["min_par_chars"]:
                continue

            # Stop phrases filter (case-insensitive)
            lower_para = para.lower()
            if any(phrase in lower_para for phrase in config["stop_phrases"]):
                self.stats["dropped_by_cookie"] += 1
                continue

            # Link density filter
            soup_para = BeautifulSoup(f"<p>{original_para}</p>", "html.parser")
            links = soup_para.find_all("a")
            link_text_len = sum(len(link.get_text()) for link in links)
            total_text_len = len(para)
            link_density = link_text_len / total_text_len if total_text_len > 0 else 0

            if link_density > config["max_link_density"]:
                self.stats["dropped_by_link_density"] += 1
                continue

            # Uppercase filter (for non-headings)
            if len(para) > config.get("min_heading_chars", 3):
                upper_count = sum(1 for c in para if c.isupper())
                alpha_count = sum(1 for c in para if c.isalpha())
                if alpha_count > 0:
                    upper_ratio = upper_count / alpha_count

                    # Menu detection (lots of uppercase + menu keywords)
                    if upper_ratio > config["menu_upper_ratio"]:
                        tokens = re.findall(r"[A-Za-z]+", para)
                        if (
                            len(tokens) >= config["menu_min_tokens"]
                            and sum(
                                1
                                for token in tokens
                                if token.lower() in config["menu_keywords"]
                            )
                            >= 3
                        ):
                            self.stats["dropped_by_menu"] += 1
                            continue

                    # General uppercase filter
                    if upper_ratio > config["max_upper_ratio"]:
                        self.stats["dropped_by_uppercase"] += 1
                        continue

            # Whitespace normalization
            para = re.sub(r"\s+", " ", para).strip()

            if para:
                cleaned_paragraphs.append(para)

        # Deduplicate paragraphs
        seen_hashes = set()
        deduped_paragraphs = []
        for para in cleaned_paragraphs:
            para_hash = hashlib.md5(para.lower().encode()).hexdigest()
            if para_hash not in seen_hashes:
                seen_hashes.add(para_hash)
                deduped_paragraphs.append(para)

        self.stats["final_paragraphs"] = len(deduped_paragraphs)
        logger.debug(
            f"Paragraph cleaning: {initial_count} -> {len(deduped_paragraphs)} paragraphs"
        )

        return deduped_paragraphs

    def _score_paragraph(self, para: str, page_title: str = "") -> float:
        """Score paragraph for content quality"""
        if not para:
            return 0.0

        base_score = len(para)

        # Apply link density penalty
        soup_para = BeautifulSoup(f"<p>{para}</p>", "html.parser")
        links = soup_para.find_all("a")
        link_text_len = sum(len(link.get_text()) for link in links)
        total_text_len = len(para)
        link_density = link_text_len / total_text_len if total_text_len > 0 else 0

        score = base_score * (
            1 - link_density * self.cleaning_config.get("link_density_penalty", 1.0)
        )

        # Title keyword bonus
        if page_title:
            title_words = set(re.findall(r"\w+", page_title.lower()))
            para_words = set(re.findall(r"\w+", para.lower()))
            if title_words & para_words:  # Has common words with title
                score *= self.cleaning_config.get("title_keyword_bonus", 1.5)

        return score

    def _select_best_content_run(
        self, paragraphs: List[str], page_title: str = ""
    ) -> List[str]:
        """Select the best contiguous run of content paragraphs"""
        if not paragraphs:
            return []

        if len(paragraphs) <= 5:
            return paragraphs  # Too few to analyze, return all

        # Score each paragraph
        scores = [self._score_paragraph(para, page_title) for para in paragraphs]

        # Find best contiguous run
        min_run_chars = self.cleaning_config.get("min_contiguous_run_chars", 600)
        best_run = []
        best_score = 0

        # Try different run lengths
        for start in range(len(paragraphs)):
            current_run = []
            current_chars = 0
            current_score = 0

            for end in range(start, len(paragraphs)):
                current_run.append(paragraphs[end])
                current_chars += len(paragraphs[end])
                current_score += scores[end]

                if current_chars >= min_run_chars:
                    avg_score = current_score / len(current_run)
                    if avg_score > best_score:
                        best_score = avg_score
                        best_run = current_run.copy()

        # Fallback: if no good run found, take top 5 scored paragraphs in order
        if not best_run:
            indexed_scores = [(scores[i], i) for i in range(len(scores))]
            indexed_scores.sort(reverse=True)
            top_indices = sorted([idx for _, idx in indexed_scores[:5]])
            best_run = [paragraphs[i] for i in top_indices]

        return best_run

    def _apply_structural_post_filter(self, text: str) -> str:
        """Apply structural post-filtering to extracted content"""
        if not text:
            return text
            
        # Split into lines for processing
        lines = text.split('\n')
        filtered_lines = []
        seen_lines = set()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Normalize whitespace
            line = re.sub(r'\s+', ' ', line)
            
            # Compute link density for this line (paragraph)
            soup_line = BeautifulSoup(f"<p>{line}</p>", "html.parser")
            links = soup_line.find_all("a")
            if links:
                link_text_len = sum(len(link.get_text()) for link in links)
                total_text_len = len(line)
                link_density = link_text_len / total_text_len if total_text_len > 0 else 0
                
                # Drop high-link-density blocks
                if link_density > 0.5:  # More aggressive than paragraph cleaning
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

    def _extract_with_profile(self, html_content: str, profile: dict) -> Optional[str]:
        """Extract content using domain-specific profile selectors"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove unwanted selectors first
            for selector in profile.get("remove_selectors", []):
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract main content
            main_selector = profile.get("main_selector")
            if main_selector:
                main_element = soup.select_one(main_selector)
                if main_element:
                    content = main_element.get_text(" ", strip=True)
                    if content and len(content) > 100:
                        logger.debug(f"Profile extraction got {len(content)} chars")
                        return content
            
            return None
            
        except Exception as e:
            logger.debug(f"Profile extraction failed: {e}")
            return None

    async def _extract_article_content(
        self, html_content: str, url: str = None
    ) -> Optional[str]:
        """Extract article content using trafilatura-first hierarchy with fallbacks"""
        try:
            if not html_content or not url:
                return None

            # Get domain for profile lookup
            domain = tldextract.extract(url).domain + "." + tldextract.extract(url).suffix
            
            # STEP 1: Check for domain-specific profile
            profile = self._load_domain_profile(domain)
            if profile:
                logger.debug(f"Using domain profile for {domain}")
                extracted = self._extract_with_profile(html_content, profile)
                if extracted:
                    # Apply structural post-filter
                    content = self._apply_structural_post_filter(extracted)
                    if content and len(content) > 100:
                        logger.debug(f"Profile extraction: {len(content)} chars for {url}")
                        return content
            
            # STEP 2: Try Trafilatura first
            extracted = self._extract_with_trafilatura(html_content, url)
            if extracted:
                # Apply structural post-filter
                content = self._apply_structural_post_filter(extracted)
                if content and len(content) > 100:
                    logger.debug(f"Trafilatura extraction: {len(content)} chars for {url}")
                    return content
            
            # STEP 3: Fallback to existing domain-agnostic method
            logger.debug(f"Falling back to custom extraction for {url}")
            
            # Try AMP version if domain is in hints
            final_html = html_content
            final_url = url
            
            try_amp_first = domain in self.cleaning_config.get("amp_first_hints", [])
            if try_amp_first and self.cleaning_config.get("amp", {}).get("enabled", True):
                self.stats["amp_attempts"] += 1
                amp_url = await self._find_amp_url(html_content, url)
                if amp_url:
                    amp_html = await self._fetch_url(amp_url)
                    if amp_html:
                        final_html = amp_html
                        final_url = amp_url
                        self.stats["amp_success"] += 1
                        logger.debug(f"Using AMP version: {amp_url}")

            # Extract using existing paragraph-based method
            soup = BeautifulSoup(final_html, "html.parser")
            title_tag = soup.find("title")
            page_title = title_tag.get_text().strip() if title_tag else ""
            
            raw_paragraphs = self._extract_paragraphs(soup)
            if not raw_paragraphs:
                logger.debug(f"No paragraphs extracted from {final_url}")
                return None

            cleaned_paragraphs = self._clean_paragraphs(raw_paragraphs, page_title, final_url)
            if not cleaned_paragraphs:
                logger.debug(f"No paragraphs survived cleaning for {final_url}")
                return None

            final_paragraphs = self._select_best_content_run(cleaned_paragraphs, page_title)
            if not final_paragraphs:
                logger.debug(f"No content run selected for {final_url}")
                return None

            # Join and apply structural post-filter
            raw_content = "\n\n".join(final_paragraphs)
            content = self._apply_structural_post_filter(raw_content)
            
            # Apply final limits
            max_chars = self.cleaning_config.get("limits", {}).get("max_content_chars", 50000)
            if len(content) > max_chars:
                content = content[:max_chars]

            logger.debug(f"Fallback extraction: {len(content)} chars for {url}")
            return content if content and len(content) > 100 else None

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
