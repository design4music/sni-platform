#!/usr/bin/env python3
"""
Unified Keyword Extraction Pipeline
Strategic Narrative Intelligence ETL Pipeline

Combines short-text and full-text extraction into a single unified pipeline:
- Short mode (≤500 chars): NER + title bigrams, cap 4
- Full mode (>500 chars): NER + YAKE + KeyBERT, cap 8
- Auto mode: Automatically chooses based on content length
- Idempotent: Skip articles already at cap, top-up if below cap
"""

import argparse
import logging
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from multiprocessing import cpu_count
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import spacy
from psycopg2.extras import execute_values

# Add project root to path for centralized config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import centralized database connection
from etl_pipeline.core.config import get_db_connection

# Import components
sys.path.append(str(Path(__file__).parent))
from canonicalizer import get_canonicalizer

# Import full extractor components
sys.path.append(str(Path(__file__).parent.parent / "extraction"))
from dynamic_keyword_extractor import get_singleton_extractor

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnifiedKeywordExtractor:
    """Unified keyword extractor with chunked processing and time budgets"""

    def __init__(self, batch_size: int = 200, time_budget_seconds: int = 600, 
                 max_workers: int = 1, cap_per_article: int = 8, only_new: bool = True):
        # Chunked worker parameters
        self.batch_size = batch_size
        self.time_budget_seconds = time_budget_seconds
        self.max_workers = max_workers
        self.cap_per_article = cap_per_article
        self.only_new = only_new
        
        self.canonicalizer = get_canonicalizer()

        # Load spaCy model for short mode
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded for short-text extraction")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm"
            )
            raise

        # Initialize full extractor (lazy loaded)
        self.full_extractor = None

        # Strategic scores for different entity types
        self.strategic_scores = {
            "PERSON": 0.9,
            "ORG": 1.0,
            "GPE": 1.0,  # Geopolitical entities
            "bigram": 0.6,
        }

        logger.info(f"Unified keyword extractor initialized: batch_size={self.batch_size}, "
                   f"time_budget={self.time_budget_seconds}s, max_workers={self.max_workers}, "
                   f"cap_per_article={self.cap_per_article}")

    def get_db_connection(self):
        """Get database connection using centralized configuration"""
        return get_db_connection()

    def get_full_extractor(self):
        """Lazy load the full extractor"""
        if self.full_extractor is None:
            self.full_extractor = get_singleton_extractor()
            logger.info("Full keyword extractor loaded")
        return self.full_extractor

    def determine_mode(self, content: str, mode: str) -> str:
        """Determine extraction mode based on content and user preference"""
        if mode in ["short", "full"]:
            return mode

        # Auto mode: decide based on content length
        content_len = len(content or "")
        if content_len <= 500:
            return "short"
        else:
            return "full"

    def check_article_keyword_status(self, conn, article_id: str) -> Tuple[int, int]:
        """Check current keyword count and determine caps"""
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*) 
                FROM article_keywords ak
                WHERE ak.article_id = %s
            """,
                (article_id,),
            )

            current_count = cur.fetchone()[0]
            return current_count, 8  # Max cap is 8 for any article

        finally:
            cur.close()

    def extract_short_keywords(
        self, article_data: Tuple, frequent_bigrams: Set[str]
    ) -> List[Tuple[str, str, float]]:
        """Extract keywords using short-text method (NER + bigrams)"""
        article_id, title, summary, content = article_data

        # Combine available text (title + summary if available)
        text_parts = [title or ""]
        if summary:
            text_parts.append(summary)

        combined_text = " ".join(text_parts).strip()

        if not combined_text:
            return []

        keywords = []

        # 1. Extract named entities
        entities = self.extract_entities(combined_text)
        for entity_text, entity_type in entities:
            # Canonicalize entity
            canonical = self.canonicalizer.normalize_token(entity_text)
            if canonical and canonical != entity_text:
                keywords.append(
                    (canonical, "entity", self.strategic_scores[entity_type])
                )
            else:
                keywords.append(
                    (entity_text, "entity", self.strategic_scores[entity_type])
                )

        # 2. Extract frequent bigrams from title
        title_bigrams = self.extract_bigrams(title or "")
        for bigram in title_bigrams:
            if bigram in frequent_bigrams:
                # Canonicalize bigram
                canonical = self.canonicalizer.normalize_token(bigram)
                if canonical and canonical != bigram:
                    keywords.append(
                        (canonical, "phrase", self.strategic_scores["bigram"])
                    )
                else:
                    keywords.append((bigram, "phrase", self.strategic_scores["bigram"]))

        # Remove duplicates and cap at 4 for short mode
        unique_keywords = []
        seen = set()
        for keyword, kw_type, score in keywords:
            if keyword not in seen and len(keyword.strip()) >= 2:
                unique_keywords.append((keyword.strip(), kw_type, score))
                seen.add(keyword)
                if len(unique_keywords) >= 4:
                    break

        return unique_keywords

    def extract_full_keywords(
        self, article_data: Tuple
    ) -> List[Tuple[str, str, float]]:
        """Extract keywords using full-text method (NER + YAKE + KeyBERT)"""
        article_id, title, summary, content = article_data

        full_extractor = self.get_full_extractor()
        result = full_extractor.extract_keywords(
            str(article_id), title or "", content or "", summary, "en"
        )

        # Convert to our format, cap at 8
        keywords = []
        for keyword in result.keywords[:8]:
            # Map extraction method to keyword_type
            if keyword.keyword_type == "entity":
                kw_type = "entity"
            elif keyword.keyword_type == "phrase":
                kw_type = "phrase"
            elif keyword.keyword_type == "keyphrase":
                kw_type = "keyphrase"
            else:
                kw_type = "full"

            keywords.append(
                (keyword.text.strip(), kw_type, float(keyword.strategic_score))
            )

        return keywords

    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract named entities using spaCy"""
        entities = []
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE"]:
                    clean_text = ent.text.strip()
                    if len(clean_text) >= 2:
                        entities.append((clean_text, ent.label_))
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")

        return entities

    def extract_bigrams(self, text: str) -> List[str]:
        """Extract bigrams from text"""
        if not text or len(text.strip()) < 4:
            return []

        # Tokenize and clean
        tokens = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
        if len(tokens) < 2:
            return []

        # Create bigrams
        bigrams = []
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            if len(bigram) <= 30:  # Reasonable length limit
                bigrams.append(bigram)

        return bigrams

    def build_frequent_bigrams(self, conn, hours_back: int = 300) -> Set[str]:
        """Build set of frequent bigrams from recent articles"""
        cur = conn.cursor()
        try:
            window_start = datetime.now() - timedelta(hours=hours_back)
            cur.execute(
                """
                SELECT title, summary 
                FROM articles 
                WHERE language = 'EN' 
                AND created_at >= %s
                AND (LENGTH(COALESCE(content, '')) <= 500 OR content IS NULL)
                AND title IS NOT NULL
            """,
                (window_start,),
            )

            # Extract all bigrams from titles
            all_bigrams = []
            for title, summary in cur.fetchall():
                text_parts = [title or ""]
                if summary:
                    text_parts.append(summary)
                combined_text = " ".join(text_parts)
                all_bigrams.extend(self.extract_bigrams(combined_text))

            # Keep bigrams with frequency >= 2
            bigram_counts = Counter(all_bigrams)
            frequent_bigrams = {
                bigram for bigram, count in bigram_counts.items() if count >= 2
            }

            logger.info(
                f"Found {len(frequent_bigrams)} frequent bigrams (≥2 occurrences) in corpus"
            )
            return frequent_bigrams

        finally:
            cur.close()

    def get_articles_batch(self, conn, hours_back: int) -> List[Tuple[int, str, str, str, int]]:
        """Get a batch of articles that need keyword extraction (idempotent query)"""
        cur = conn.cursor()
        try:
            window_start = datetime.now() - timedelta(hours=hours_back)

            # Chunked idempotent query - get articles below cap (simplified for batching)
            query = """
                SELECT a.id, a.title, a.summary, a.content,
                       COALESCE(ak_count.cnt, 0) as current_keywords
                FROM articles a
                LEFT JOIN (
                    SELECT article_id, COUNT(*) as cnt 
                    FROM article_keywords 
                    GROUP BY article_id
                ) ak_count ON a.id = ak_count.article_id
                WHERE a.language = 'EN'
                  AND a.created_at >= %s
                  AND COALESCE(ak_count.cnt, 0) < %s
                ORDER BY a.created_at
                LIMIT %s
            """

            cur.execute(query, (window_start, self.cap_per_article, self.batch_size))
            articles = cur.fetchall()
            logger.debug(
                f"Batch loaded: {len(articles)} articles (cap < {self.cap_per_article}, last {hours_back}h)"
            )
            return articles

        finally:
            cur.close()
            
    def extract_keywords_for_article(self, article_data: Tuple[int, str, str, str, int], 
                                     frequent_bigrams: Set[str]) -> List[Tuple[int, str, float]]:
        """Extract keywords for a single article (worker function)"""
        article_id, title, summary, content, current_count = article_data
        
        # Determine extraction mode
        actual_mode = self.determine_mode(content, "auto")
        
        # Determine how many keywords we can add
        if actual_mode == "short":
            max_keywords = 4
        else:
            max_keywords = 8
            
        keywords_to_add = max_keywords - current_count
        if keywords_to_add <= 0:
            return []  # Already at cap
            
        try:
            # Extract keywords based on mode
            if actual_mode == "short":
                # Use the existing method signature
                keywords = self.extract_short_keywords(
                    (article_id, title, summary, content), frequent_bigrams
                )
            else:
                # Use the existing method signature
                keywords = self.extract_full_keywords(
                    (article_id, title, summary, content)
                )
                
            # Limit to available slots
            keywords = keywords[:keywords_to_add]
            
            # Return as (article_id, keyword, score) tuples
            result = []
            for keyword, kw_type, score in keywords:
                result.append((article_id, keyword, float(score)))
            
            return result
            
        except Exception as e:
            logger.warning(f"Error processing article {article_id}: {e}")
            return []
    
    def process_articles_chunked(self, hours_back: int = 72, dry_run: bool = False) -> Dict[str, int]:
        """Main chunked processing function with time budget and parallel workers"""
        start_time = time.time()
        
        logger.info(
            f"Starting chunked keyword extraction: batch_size={self.batch_size}, "
            f"time_budget={self.time_budget_seconds}s, workers={self.max_workers}"
        )

        conn = self.get_db_connection()
        stats = {
            'batches_processed': 0,
            'articles_processed': 0,
            'keywords_inserted': 0,
            'articles_skipped': 0,
            'elapsed_seconds': 0
        }

        try:
            # Build frequent bigrams once (for all batches)
            frequent_bigrams = self.build_frequent_bigrams(conn, hours_back)
            
            # Process in chunks until time budget or no more articles
            while time.time() - start_time < self.time_budget_seconds:
                batch_start_time = time.time()
                
                # Get next batch of articles
                articles = self.get_articles_batch(conn, hours_back)
                
                if not articles:
                    logger.info("No more articles to process")
                    break
                    
                logger.info(f"Processing batch of {len(articles)} articles")
                
                # Process batch sequentially (parallel processing disabled for now)
                all_keywords_data = []
                for article_data in articles:
                    keywords = self.extract_keywords_for_article(article_data, frequent_bigrams)
                    
                    # Convert to upsert format
                    for article_id, keyword, score in keywords:
                        article_title = article_data[1]  # Get title from article_data
                        all_keywords_data.append((article_id, article_title, keyword, "extracted", float(score)))
                
                # Insert keywords (commit per batch)
                if not dry_run and all_keywords_data:
                    inserted_count = self.upsert_keywords(conn, all_keywords_data)
                    stats['keywords_inserted'] += inserted_count
                else:
                    logger.info(f"DRY RUN: Would insert {len(all_keywords_data)} keywords")
                    stats['keywords_inserted'] += len(all_keywords_data)
                
                # Update stats
                stats['batches_processed'] += 1
                stats['articles_processed'] += len(articles)
                
                batch_elapsed = time.time() - batch_start_time
                logger.info(f"Batch completed in {batch_elapsed:.1f}s: "
                           f"{len(all_keywords_data)} keywords from {len(articles)} articles")
                
                # Check time budget
                elapsed = time.time() - start_time
                if elapsed >= self.time_budget_seconds:
                    logger.info(f"Time budget reached: {elapsed:.1f}s")
                    break
            
            stats['elapsed_seconds'] = time.time() - start_time
            
            logger.info("Chunked extraction completed:")
            logger.info(f"  Batches processed: {stats['batches_processed']}")
            logger.info(f"  Articles processed: {stats['articles_processed']}")
            logger.info(f"  Keywords inserted: {stats['keywords_inserted']}")
            logger.info(f"  Elapsed time: {stats['elapsed_seconds']:.1f}s")
            
            return stats

        finally:
            conn.close()

    def upsert_keywords(self, conn, keywords_data: List[Tuple]):
        """Upsert keywords and article_keywords with proper handling"""
        if not keywords_data:
            return 0

        cur = conn.cursor()

        try:
            # Group by keyword text and type for keywords table
            keyword_info = {}  # {keyword_text: keyword_type}
            for _, _, kw_text, kw_type, _ in keywords_data:
                if kw_text not in keyword_info:
                    keyword_info[kw_text] = kw_type

            # Upsert keywords table
            keyword_upserts = []
            for kw_text, kw_type in keyword_info.items():
                keyword_upserts.append((kw_text, kw_type))

            execute_values(
                cur,
                """
                INSERT INTO keywords (keyword, keyword_type) 
                VALUES %s 
                ON CONFLICT (keyword) DO UPDATE SET
                    keyword_type = EXCLUDED.keyword_type,
                    updated_at = now()
                """,
                keyword_upserts,
            )

            # Get keyword IDs for relationships
            keyword_texts = list(keyword_info.keys())
            format_strings = ",".join(["%s"] * len(keyword_texts))
            cur.execute(
                f"""
                SELECT keyword, id FROM keywords 
                WHERE keyword IN ({format_strings})
            """,
                keyword_texts,
            )

            keyword_id_map = {keyword: kid for keyword, kid in cur.fetchall()}

            # Prepare article_keywords data
            article_keyword_data = []
            for article_id, _, kw_text, kw_type, score in keywords_data:
                if kw_text in keyword_id_map:
                    article_keyword_data.append(
                        (
                            article_id,
                            keyword_id_map[kw_text],
                            "combined",  # extraction_method (use allowed value)
                            score,  # extraction_score
                            score,  # strategic_score (same for now)
                            1,  # keyword_rank
                        )
                    )

            # Insert article-keyword relationships
            execute_values(
                cur,
                """
                INSERT INTO article_keywords 
                (article_id, keyword_id, extraction_method, extraction_score, strategic_score, keyword_rank)
                VALUES %s
                ON CONFLICT (article_id, keyword_id) DO UPDATE SET
                    extraction_score = GREATEST(article_keywords.extraction_score, EXCLUDED.extraction_score),
                    strategic_score = GREATEST(article_keywords.strategic_score, EXCLUDED.strategic_score)
                """,
                article_keyword_data,
            )

            conn.commit()
            logger.info(
                f"Upserted {len(keyword_upserts)} keywords and {len(article_keyword_data)} article-keyword relationships"
            )
            return len(article_keyword_data)

        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting keywords: {e}")
            return 0
        finally:
            cur.close()

    def process_articles(self, hours_back: int = 72, mode: str = "auto"):
        """Legacy method for backward compatibility - delegates to chunked processor"""
        logger.info("Delegating to chunked processor (mode parameter ignored)")
        stats = self.process_articles_chunked(hours_back, dry_run=False)
        return stats


def main():
    """CLI interface with chunked worker parameters"""
    parser = argparse.ArgumentParser(description="Chunked Keyword Extraction Pipeline")
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "short", "full"],
        default="auto",
        help="Extraction mode: auto (default), short, or full (legacy - now uses auto internally)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=200, help="Articles to process per batch (default: 200)"
    )
    parser.add_argument(
        "--time-budget-seconds", type=int, default=600, help="Max processing time in seconds (default: 600)"
    )
    parser.add_argument(
        "--max-workers", type=int, default=1, help="Max parallel workers (default: 1 = sequential)"
    )
    parser.add_argument(
        "--cap-per-article", type=int, default=8, help="Stop once article has >= cap keywords (default: 8)"
    )
    parser.add_argument(
        "--only-new", type=int, default=1, help="Skip articles that meet cap (default: 1)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without inserting"
    )

    args = parser.parse_args()

    # Create extractor with chunked parameters
    extractor = UnifiedKeywordExtractor(
        batch_size=args.batch_size,
        time_budget_seconds=args.time_budget_seconds,
        max_workers=args.max_workers,
        cap_per_article=args.cap_per_article,
        only_new=bool(args.only_new)
    )

    try:
        stats = extractor.process_articles_chunked(args.window, dry_run=args.dry_run)
        
        # Exit 0 if any work done; non-zero only on crash
        work_done = stats['articles_processed'] > 0
        logger.info(f"Chunked keyword extraction completed: {'SUCCESS' if work_done else 'NO_WORK'}")
        return 0 if work_done else 0  # Always return 0 unless crash

    except Exception as e:
        logger.error(f"Chunked keyword extraction failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
