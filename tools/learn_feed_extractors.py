#!/usr/bin/env python3
"""
LLM-powered extractor profile learner for news feeds

Creates/updates news_feeds.extraction_profile by sampling recent articles
and using LLM to infer optimal extraction selectors and rules.
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
import asyncio
import structlog
from bs4 import BeautifulSoup
from sqlalchemy import text

sys.path.append('.')

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database

logger = structlog.get_logger(__name__)


class FeedExtractorLearner:
    """Learn extraction profiles for feeds using LLM analysis"""
    
    def __init__(self):
        self.config = get_config()
        self.session = None
        initialize_database(self.config.database)
    
    def get_profile_schema(self) -> Dict:
        """Return the exact JSON schema for extraction profiles"""
        return {
            "version": 1,
            "scope": "feed",  # "feed" or "domain"
            "main_selector": "",
            "title_selector": "h1",
            "date_selector": "time, .pub-date",
            "author_selector": ".byline",
            "remove_selectors": [],
            "allow_tags": ["p", "h2", "h3", "ul", "li", "blockquote"],
            "junk_phrases": [],
            "pre_clean_regex": [],
            "post_clean_regex": [],
            "min_length": 150,
            "density_threshold": 0.12,
            "last_validated_at": datetime.utcnow().isoformat() + "Z",
            "source": "llm",
            "notes": ""
        }
    
    def get_recent_articles(self, feed_id: Optional[str] = None, domain: Optional[str] = None, 
                          days: int = 14, limit: int = 50) -> List[Dict]:
        """Get recent articles for feed or domain"""
        with get_db_session() as db:
            if feed_id:
                query = text("""
                    SELECT url, title, content, created_at
                    FROM articles 
                    WHERE feed_id = :feed_id 
                    AND url IS NOT NULL
                    AND created_at >= :since
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                params = {"feed_id": feed_id, "since": datetime.utcnow() - timedelta(days=days), "limit": limit}
            elif domain:
                query = text("""
                    SELECT url, title, content, created_at
                    FROM articles 
                    WHERE url LIKE :domain_pattern
                    AND url IS NOT NULL
                    AND created_at >= :since
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                params = {"domain_pattern": f"%{domain}%", "since": datetime.utcnow() - timedelta(days=days), "limit": limit}
            else:
                raise ValueError("Either feed_id or domain must be provided")
            
            result = db.execute(query, params)
            return [dict(row._mapping) for row in result.fetchall()]
    
    async def fetch_html(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    def analyze_html_structure(self, html: str, url: str) -> Dict:
        """Analyze HTML structure and return compact summary for LLM"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Tag histogram
            tag_counts = {}
            for tag in soup.find_all():
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
            
            # Class name frequency
            class_counts = {}
            for tag in soup.find_all(class_=True):
                for cls in tag.get('class', []):
                    class_counts[cls] = class_counts.get(cls, 0) + 1
            
            # Find text-dense containers (potential article content)
            candidates = []
            for tag in soup.find_all(['div', 'article', 'section', 'main']):
                text = tag.get_text(strip=True)
                if len(text) > 200:  # Substantial text
                    tag_html = str(tag)[:500] if tag else ""
                    classes = ' '.join(tag.get('class', []))
                    candidates.append({
                        "tag": tag.name,
                        "classes": classes,
                        "id": tag.get('id', ''),
                        "text_length": len(text),
                        "text_preview": text[:500],
                        "html_preview": tag_html
                    })
            
            # Sort candidates by text length (descending)
            candidates = sorted(candidates, key=lambda x: x['text_length'], reverse=True)[:5]
            
            # Title candidates
            title_candidates = []
            for tag in soup.find_all(['h1', 'h2', 'title']):
                text = tag.get_text(strip=True)
                if len(text) > 10 and len(text) < 200:
                    title_candidates.append({
                        "tag": tag.name,
                        "classes": ' '.join(tag.get('class', [])),
                        "id": tag.get('id', ''),
                        "text": text
                    })
            
            return {
                "url": url,
                "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_classes": dict(sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "content_candidates": candidates,
                "title_candidates": title_candidates[:3]
            }
        except Exception as e:
            logger.warning(f"HTML analysis failed for {url}: {e}")
            return {"url": url, "error": str(e)}
    
    async def get_llm_profile(self, structure_summaries: List[Dict], domain: str) -> Optional[Dict]:
        """Generate extraction profile from structure analysis"""
        try:
            logger.info(f"Analyzing structure for {domain}")
            
            # Analyze content candidates to find the best selectors
            all_candidates = []
            for summary in structure_summaries:
                candidates = summary.get("content_candidates", [])
                all_candidates.extend(candidates)
            
            if not all_candidates:
                logger.error("No content candidates found in summaries")
                return None
            
            # Find the most promising content selector based on text length and frequency
            class_scores = {}
            id_scores = {}
            tag_scores = {}
            
            for candidate in all_candidates:
                # Score by text length (longer is better)
                text_len = candidate.get("text_length", 0)
                if text_len > 200:  # Only consider substantial content
                    # Score classes
                    classes = candidate.get("classes", "").split()
                    for cls in classes:
                        if cls and len(cls) > 2:  # Avoid short/generic class names
                            class_scores[cls] = class_scores.get(cls, 0) + text_len
                    
                    # Score IDs
                    elem_id = candidate.get("id", "")
                    if elem_id and len(elem_id) > 2:
                        id_scores[elem_id] = id_scores.get(elem_id, 0) + text_len
                    
                    # Score tags
                    tag = candidate.get("tag", "")
                    if tag:
                        tag_scores[tag] = tag_scores.get(tag, 0) + text_len
            
            # Build main selector from best scoring elements
            main_selectors = []
            
            # Add best classes
            if class_scores:
                best_classes = sorted(class_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                for cls, score in best_classes:
                    if score > 1000:  # Only high-scoring classes
                        main_selectors.append(f".{cls}")
            
            # Add best IDs
            if id_scores:
                best_ids = sorted(id_scores.items(), key=lambda x: x[1], reverse=True)[:2]
                for elem_id, score in best_ids:
                    if score > 1000:
                        main_selectors.append(f"#{elem_id}")
            
            # Add semantic selectors as fallback
            semantic_selectors = ["article", "[role='main']", ".content", ".article-content", 
                                ".story", ".post-content", ".entry-content"]
            main_selectors.extend(semantic_selectors)
            
            if not main_selectors:
                main_selectors = ["article", ".content", "main"]
            
            # Analyze common junk patterns
            junk_phrases = ["Subscribe", "Privacy Policy", "Cookie Policy", "Related Articles"]
            
            # Domain-specific customizations
            if "presstv" in domain.lower():
                main_selectors.insert(0, ".story")
                main_selectors.insert(0, "#story")
                junk_phrases.extend(["Press TV", "Follow Press TV"])
            elif "japantimes" in domain.lower():
                main_selectors.insert(0, ".article-body")
                main_selectors.insert(0, ".entry-content")
            elif "scmp" in domain.lower():
                main_selectors.insert(0, ".article-content")
                main_selectors.insert(0, ".story-content")
            elif "france24" in domain.lower():
                main_selectors.insert(0, ".article-content")
                main_selectors.insert(0, ".content-body")
            
            # Build profile
            profile = self.get_profile_schema()
            profile.update({
                "main_selector": ", ".join(main_selectors[:5]),  # Top 5 selectors
                "remove_selectors": [
                    ".advertisement", ".ad", ".ads", ".social-share", ".share-buttons",
                    ".related-articles", ".sidebar", ".newsletter", ".subscription",
                    "nav", "header", "footer", ".navigation", ".menu",
                    ".comments", ".comment-form"
                ],
                "junk_phrases": junk_phrases,
                "pre_clean_regex": [
                    {"pattern": r"^Share\s+.*", "flags": "m"},
                    {"pattern": r"^Follow us.*", "flags": "m"}
                ],
                "post_clean_regex": [
                    {"pattern": r"(?i)^(Subscribe|Related|Sponsored).*$", "flags": "m"}
                ],
                "min_length": 200,  # Slightly higher for news content
                "density_threshold": 0.08,  # Lower threshold for news sites
                "notes": f"Learned from {len(structure_summaries)} pages for {domain}",
                "scope": "domain" if len(structure_summaries) >= 6 else "feed"
            })
            
            logger.info(f"Generated profile with main selector: {profile['main_selector']}")
            return profile
            
        except Exception as e:
            logger.error(f"Profile generation failed: {e}")
            return None
    
    def validate_profile(self, profile: Dict, html_samples: List[Tuple[str, str]]) -> Tuple[bool, Dict]:
        """Validate profile against HTML samples"""
        results = []
        
        for url, html in html_samples:
            try:
                # Apply profile extraction
                soup = BeautifulSoup(html, 'html.parser')
                
                # Pre-clean regex
                cleaned_html = html
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
                
                # Select main content
                main_selector = profile.get("main_selector", "")
                main_element = soup.select_one(main_selector)
                if not main_element:
                    results.append({"url": url, "success": False, "error": "Main selector not found"})
                    continue
                
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
                
                # Post-clean regex
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
                
                # Check thresholds
                min_length = profile.get("min_length", 150)
                density_threshold = profile.get("density_threshold", 0.12)
                
                success = text_len >= min_length and density >= density_threshold
                
                results.append({
                    "url": url,
                    "success": success,
                    "length": text_len,
                    "density": density,
                    "text_preview": text[:200]
                })
                
            except Exception as e:
                results.append({"url": url, "success": False, "error": str(e)})
        
        # Calculate overall success rate
        success_count = sum(1 for r in results if r.get("success", False))
        success_rate = success_count / len(results) if results else 0
        
        # Profile passes if >= 80% success rate
        passes = success_rate >= 0.8
        
        return passes, {
            "success_rate": success_rate,
            "results": results,
            "total_samples": len(results)
        }
    
    def save_profile(self, profile: Dict, feed_id: Optional[str] = None, domain: Optional[str] = None):
        """Save profile to database"""
        with get_db_session() as db:
            if feed_id:
                query = text("UPDATE news_feeds SET extraction_profile = :profile WHERE id = :feed_id")
                db.execute(query, {"profile": json.dumps(profile), "feed_id": feed_id})
            elif domain and profile.get("scope") == "domain":
                # Update all feeds for this domain
                query = text("""
                    UPDATE news_feeds 
                    SET extraction_profile = :profile 
                    WHERE url LIKE :domain_pattern
                """)
                db.execute(query, {"profile": json.dumps(profile), "domain_pattern": f"%{domain}%"})
            
            db.commit()
    
    async def learn_profile(self, feed_id: Optional[str] = None, domain: Optional[str] = None,
                          sample_size: int = 8, dry_run: bool = False) -> bool:
        """Main learning workflow"""
        logger.info(f"Learning extraction profile for {'feed ' + feed_id if feed_id else 'domain ' + domain}")
        
        # Get recent articles
        articles = self.get_recent_articles(feed_id, domain, days=14, limit=sample_size * 3)
        if len(articles) < sample_size:
            logger.error(f"Not enough articles found: {len(articles)} < {sample_size}")
            return False
        
        # Sample URLs and fetch HTML
        sample_urls = [article["url"] for article in articles[:sample_size]]
        html_samples = []
        structure_summaries = []
        
        logger.info(f"Fetching {len(sample_urls)} sample pages...")
        for url in sample_urls:
            html = await self.fetch_html(url)
            if html:
                html_samples.append((url, html))
                structure_summaries.append(self.analyze_html_structure(html, url))
        
        if len(html_samples) < sample_size * 0.6:  # Need at least 60% successful fetches
            logger.error(f"Too few pages fetched successfully: {len(html_samples)}")
            return False
        
        # Get LLM profile
        target_domain = domain or urlparse(sample_urls[0]).netloc
        profile = await self.get_llm_profile(structure_summaries, target_domain)
        if not profile:
            logger.error("Failed to generate profile from LLM")
            return False
        
        # Validate profile
        passes, validation_results = self.validate_profile(profile, html_samples)
        
        # Print results
        print(f"\nValidation Results for {target_domain}:")
        print(f"Success Rate: {validation_results['success_rate']:.1%}")
        print(f"Total Samples: {validation_results['total_samples']}")
        print("\nPer-URL Results:")
        for result in validation_results['results']:
            status = "PASS" if result.get('success') else "FAIL"
            length = result.get('length', 0)
            density = result.get('density', 0)
            error = result.get('error', '')
            print(f"  {status:4} | {length:4d} chars | {density:.3f} density | {result['url'][:60]}")
            if error:
                print(f"       | Error: {error}")
        
        if dry_run:
            print(f"\nGenerated Profile (DRY RUN):")
            print(json.dumps(profile, indent=2))
            return True
        
        if passes:
            self.save_profile(profile, feed_id, domain)
            logger.info(f"Profile saved successfully for {'feed ' + feed_id if feed_id else 'domain ' + domain}")
            return True
        else:
            logger.error(f"Profile validation failed (success rate: {validation_results['success_rate']:.1%})")
            print("\nGenerated Profile (NOT SAVED due to validation failure):")
            print(json.dumps(profile, indent=2))
            return False


async def main():
    parser = argparse.ArgumentParser(description="Learn extraction profiles for news feeds")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--feed-id", help="Feed UUID to learn profile for")
    group.add_argument("--domain", help="Domain to learn profile for")
    parser.add_argument("--sample", type=int, default=8, help="Number of pages to sample (5-10)")
    parser.add_argument("--llm", default="deepseek", help="LLM to use for learning")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed JSON but don't save")
    
    args = parser.parse_args()
    
    if args.sample < 5 or args.sample > 10:
        print("Sample size must be between 5 and 10")
        sys.exit(1)
    
    learner = FeedExtractorLearner()
    success = await learner.learn_profile(
        feed_id=args.feed_id,
        domain=args.domain,
        sample_size=args.sample,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())