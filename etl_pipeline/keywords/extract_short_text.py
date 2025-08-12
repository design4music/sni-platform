#!/usr/bin/env python3
"""
Short-Text Keyword Extraction for Strategic Narrative Intelligence
Targets articles with ≤500 characters that regular extraction misses

Requirements:
- Scope: articles.language='EN' AND published_at >= now()-interval '300 hours'
- Target: length(coalesce(content,'')) <= 500 OR content IS NULL
- Extract from title (+summary/dek if available) only
- spaCy NER: keep PERSON|ORG|GPE
- Title bigrams (tokenized; stopwords removed); keep if ≥2 times in corpus
- Canonicalize via keyword_canon_map
- Cap: 4 tokens/article
- Upsert into keywords + article_keywords with strategic scores
"""

import logging
import re
# Import canonicalizer
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import psycopg2
import spacy
from psycopg2.extras import execute_values

sys.path.append(str(Path(__file__).parent))
from canonicalizer import get_canonicalizer

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ShortTextExtractor:
    """Extract keywords from short articles (≤500 chars)"""

    def __init__(self):
        self.canonicalizer = get_canonicalizer()

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm"
            )
            raise

        # Strategic scores by type
        self.strategic_scores = {
            "PERSON": 0.9,
            "ORG": 0.8,
            "GPE": 0.8,  # Geopolitical entity
            "bigram": 0.7,
        }

        # Common English stopwords for bigram filtering
        self.stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
        }

        logger.info("ShortTextExtractor initialized with spaCy NER and canonicalizer")

    def connect_db(self):
        """Connect to database"""
        return psycopg2.connect(
            host="localhost",
            port=5432,
            database="narrative_intelligence",
            user="postgres",
            password="postgres",
        )

    def get_target_articles(self, conn) -> List[Tuple]:
        """Get articles ≤500 chars from last 300h that don't have keywords"""
        cur = conn.cursor()

        query = """
            SELECT a.id, a.title, a.summary, a.content
            FROM articles a
            LEFT JOIN article_keywords ak ON a.id = ak.article_id
            WHERE a.language = 'EN'
              AND a.published_at >= now() - interval '300 hours'
              AND (length(coalesce(a.content, '')) <= 500 OR a.content IS NULL)
              AND ak.article_id IS NULL  -- Articles without keywords
            ORDER BY a.published_at DESC
        """

        cur.execute(query)
        articles = cur.fetchall()
        cur.close()

        logger.info(f"Found {len(articles)} target articles (≤500 chars, no keywords)")
        return articles

    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract PERSON|ORG|GPE entities using spaCy NER"""
        if not text:
            return []

        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE"]:
                # Clean and normalize entity text
                clean_text = re.sub(r"[^\w\s-]", "", ent.text).strip().lower()
                if len(clean_text) >= 2:  # Minimum length filter
                    entities.append((clean_text, ent.label_))

        return entities

    def extract_bigrams(self, text: str) -> List[str]:
        """Extract meaningful bigrams from tokenized text"""
        if not text:
            return []

        # Tokenize and clean
        tokens = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())

        # Remove stopwords
        filtered_tokens = [token for token in tokens if token not in self.stopwords]

        # Generate bigrams
        bigrams = []
        for i in range(len(filtered_tokens) - 1):
            bigram = f"{filtered_tokens[i]} {filtered_tokens[i+1]}"
            bigrams.append(bigram)

        return bigrams

    def get_corpus_bigram_counts(self, conn) -> Dict[str, int]:
        """Get bigram frequency counts from 300h corpus titles"""
        cur = conn.cursor()

        # Get all titles from 300h window
        cur.execute(
            """
            SELECT title
            FROM articles
            WHERE language = 'EN'
              AND published_at >= now() - interval '300 hours'
              AND title IS NOT NULL
        """
        )

        titles = [row[0] for row in cur.fetchall()]
        cur.close()

        # Extract all bigrams from corpus
        all_bigrams = []
        for title in titles:
            bigrams = self.extract_bigrams(title)
            all_bigrams.extend(bigrams)

        # Count occurrences
        bigram_counts = Counter(all_bigrams)

        # Filter to bigrams appearing ≥2 times
        frequent_bigrams = {
            bigram: count for bigram, count in bigram_counts.items() if count >= 2
        }

        logger.info(
            f"Found {len(frequent_bigrams)} frequent bigrams (≥2 occurrences) in corpus"
        )
        return frequent_bigrams

    def extract_keywords_from_article(
        self, article_data: Tuple, frequent_bigrams: Dict[str, int]
    ) -> List[Tuple[str, str, float]]:
        """Extract keywords from single article"""
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

        # Remove duplicates and cap at 4
        unique_keywords = []
        seen = set()
        for keyword, kw_type, score in keywords:
            if keyword not in seen and len(keyword.strip()) >= 2:
                unique_keywords.append((keyword.strip(), kw_type, score))
                seen.add(keyword)
                if len(unique_keywords) >= 4:
                    break

        return unique_keywords

    def upsert_keywords(self, conn, keywords_data: List[Tuple]):
        """Upsert keywords and article_keywords with proper handling"""
        cur = conn.cursor()

        try:
            # Group by keyword text and type for keywords table
            keyword_info = {}  # {keyword_text: keyword_type}
            for _, _, kw_text, kw_type, _ in keywords_data:
                if kw_text not in keyword_info:
                    keyword_info[kw_text] = kw_type

            # Upsert keywords table with keyword_type
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

            # Get keyword IDs
            keyword_texts = list(keyword_info.keys())
            format_strings = ",".join(["%s"] * len(keyword_texts))
            cur.execute(
                f"""
                SELECT id, keyword 
                FROM keywords 
                WHERE keyword IN ({format_strings})
            """,
                keyword_texts,
            )

            keyword_id_map = {keyword: kid for kid, keyword in cur.fetchall()}

            # Upsert article_keywords with required fields
            article_keyword_upserts = []
            for article_id, _, kw_text, kw_type, score in keywords_data:
                if kw_text in keyword_id_map:
                    article_keyword_upserts.append(
                        (
                            article_id,
                            keyword_id_map[kw_text],
                            "combined",  # extraction_method (spaCy + bigrams)
                            0.8,  # extraction_score (fixed for short-text method)
                            float(score),  # strategic_score
                            1,  # keyword_rank (simplified for short-text)
                            True,  # appears_in_title (we extract from title)
                            False,  # appears_in_summary (may not have summary)
                            0.8,  # position_importance (title is important)
                        )
                    )

            execute_values(
                cur,
                """
                INSERT INTO article_keywords (
                    article_id, keyword_id, extraction_method, extraction_score, 
                    strategic_score, keyword_rank, appears_in_title, 
                    appears_in_summary, position_importance
                ) 
                VALUES %s 
                ON CONFLICT (article_id, keyword_id) 
                DO UPDATE SET 
                    extraction_method = EXCLUDED.extraction_method,
                    strategic_score = EXCLUDED.strategic_score,
                    extraction_score = EXCLUDED.extraction_score,
                    position_importance = EXCLUDED.position_importance
                """,
                article_keyword_upserts,
            )

            conn.commit()
            logger.info(
                f"Upserted {len(keyword_upserts)} keywords and {len(article_keyword_upserts)} article-keyword relationships"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Error upserting keywords: {e}")
            raise
        finally:
            cur.close()

    def process_short_articles(self):
        """Main processing function"""
        logger.info("Starting short-text keyword extraction for articles ≤500 chars")

        with self.connect_db() as conn:
            # Get target articles
            articles = self.get_target_articles(conn)
            if not articles:
                logger.info("No target articles found")
                return

            # Get corpus bigram frequencies
            frequent_bigrams = self.get_corpus_bigram_counts(conn)

            # Process articles and extract keywords
            all_keywords_data = []
            processed_count = 0

            for article_data in articles:
                article_id = article_data[0]
                keywords = self.extract_keywords_from_article(
                    article_data, frequent_bigrams
                )

                # Add to batch
                for keyword_text, kw_type, score in keywords:
                    all_keywords_data.append(
                        (article_id, article_id, keyword_text, kw_type, score)
                    )

                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count}/{len(articles)} articles")

            # Upsert all keywords
            if all_keywords_data:
                self.upsert_keywords(conn, all_keywords_data)
                inserted_count = len(all_keywords_data)
            else:
                inserted_count = 0

            logger.info(
                f"Short-text extraction completed: processed {processed_count} articles, inserted {inserted_count} keywords"
            )


def main():
    """Main entry point"""
    extractor = ShortTextExtractor()
    extractor.process_short_articles()


if __name__ == "__main__":
    main()
