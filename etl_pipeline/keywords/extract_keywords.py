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
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Tuple

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
    """Unified keyword extractor with short/full/auto modes"""

    def __init__(self):
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

        logger.info("Unified keyword extractor initialized")

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

    def get_articles_to_process(self, conn, hours_back: int, mode: str) -> List[Tuple]:
        """Get articles that need keyword processing"""
        cur = conn.cursor()
        try:
            window_start = datetime.now() - timedelta(hours=hours_back)

            # Base query for articles in time window
            base_query = """
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
            """

            if mode == "short":
                # Short mode: only articles ≤500 chars, not at cap (4)
                query = (
                    base_query
                    + """
                    AND (LENGTH(COALESCE(a.content, '')) <= 500 OR a.content IS NULL)
                    AND COALESCE(ak_count.cnt, 0) < 4
                """
                )
            elif mode == "full":
                # Full mode: only articles >500 chars, not at cap (8)
                query = (
                    base_query
                    + """
                    AND LENGTH(COALESCE(a.content, '')) > 500
                    AND COALESCE(ak_count.cnt, 0) < 8
                """
                )
            else:  # auto mode
                # Auto mode: any article not at its respective cap
                query = (
                    base_query
                    + """
                    AND (
                        (LENGTH(COALESCE(a.content, '')) <= 500 AND COALESCE(ak_count.cnt, 0) < 4)
                        OR 
                        (LENGTH(COALESCE(a.content, '')) > 500 AND COALESCE(ak_count.cnt, 0) < 8)
                    )
                """
                )

            cur.execute(query, (window_start,))
            articles = cur.fetchall()

            logger.info(f"Found {len(articles)} articles to process in {mode} mode")
            return articles

        finally:
            cur.close()

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
        """Main processing function"""
        logger.info(
            f"Starting unified keyword extraction (window={hours_back}h, mode={mode})"
        )

        conn = self.get_db_connection()

        try:
            # Get articles to process
            articles = self.get_articles_to_process(conn, hours_back, mode)

            if not articles:
                logger.info("No articles need keyword processing")
                return

            # Build frequent bigrams for short mode (only if needed)
            frequent_bigrams = set()
            needs_bigrams = (
                any(len(article[3] or "") <= 500 for article in articles)
                or mode == "short"
                or mode == "auto"
            )

            if needs_bigrams:
                frequent_bigrams = self.build_frequent_bigrams(conn, hours_back)

            # Process articles
            all_keywords_data = []
            short_processed = 0
            full_processed = 0

            for article_data in articles:
                article_id, title, summary, content, current_count = article_data

                # Determine actual extraction mode for this article
                actual_mode = self.determine_mode(content, mode)

                # Determine how many keywords we can add
                if actual_mode == "short":
                    max_keywords = 4
                else:
                    max_keywords = 8

                keywords_to_add = max_keywords - current_count
                if keywords_to_add <= 0:
                    continue  # Already at cap

                try:
                    # Extract keywords based on mode
                    if actual_mode == "short":
                        keywords = self.extract_short_keywords(
                            (article_id, title, summary, content), frequent_bigrams
                        )
                        short_processed += 1
                    else:
                        keywords = self.extract_full_keywords(
                            (article_id, title, summary, content)
                        )
                        full_processed += 1

                    # Limit to available slots
                    keywords = keywords[:keywords_to_add]

                    # Add to batch
                    for keyword, kw_type, score in keywords:
                        all_keywords_data.append(
                            (article_id, title, keyword, kw_type, score)
                        )

                except Exception as e:
                    logger.warning(f"Failed to process article {article_id}: {e}")
                    continue

            # Upsert all keywords
            total_inserted = self.upsert_keywords(conn, all_keywords_data)

            logger.info("Unified extraction completed:")
            logger.info(f"  Short mode processed: {short_processed} articles")
            logger.info(f"  Full mode processed: {full_processed} articles")
            logger.info(f"  Total keywords inserted: {total_inserted}")

        finally:
            conn.close()


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description="Unified Keyword Extraction Pipeline")
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "short", "full"],
        default="auto",
        help="Extraction mode: auto (default), short, or full",
    )

    args = parser.parse_args()

    extractor = UnifiedKeywordExtractor()

    try:
        extractor.process_articles(args.window, args.mode)
        logger.info("Unified keyword extraction completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Unified keyword extraction failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
