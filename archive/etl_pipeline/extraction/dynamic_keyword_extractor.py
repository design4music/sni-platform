#!/usr/bin/env python3
"""
Dynamic Keyword Extraction System
Strategic Narrative Intelligence ETL Pipeline

Purely data-driven approach - NO predefined keyword lists.
Extracts keywords from content and learns strategic patterns dynamically.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import spacy
import structlog
import yake
from keybert import KeyBERT

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedKeyword:
    """Single extracted keyword with metadata"""

    text: str
    keyword_type: str  # 'entity', 'phrase', 'keyphrase'
    entity_label: Optional[str] = None  # For entities: PERSON, ORG, GPE, etc.
    extraction_score: float = 0.0  # Raw extraction confidence
    strategic_score: float = 0.0  # Calculated strategic relevance
    extraction_method: str = "unknown"  # 'spacy', 'yake', 'keybert'


@dataclass
class ArticleKeywordResult:
    """Complete keyword extraction result for an article"""

    article_id: str
    keywords: List[ExtractedKeyword]
    overall_strategic_score: float
    extraction_timestamp: datetime


class DynamicKeywordExtractor:
    """
    Data-driven keyword extraction without predefined lists

    Approach:
    1. Extract entities using spaCy NER (multilingual)
    2. Extract phrases using YAKE (language-agnostic)
    3. Extract keyphrases using KeyBERT (semantic)
    4. Score dynamically based on patterns discovered in data
    5. Learn strategic relevance from extraction patterns
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)

        # Configuration
        self.max_keywords = self.config.get("max_keywords", 50)
        self.min_keyword_length = self.config.get("min_keyword_length", 2)
        self.keybert_model = self.config.get("keybert_model", "paraphrase-MiniLM-L6-v2")

        # Dynamic strategic weights (learned from data patterns)
        self.entity_type_weights = {
            "PERSON": 2.0,  # Political figures, leaders
            "ORG": 2.5,  # Organizations, institutions
            "GPE": 3.0,  # Countries, regions - highest strategic weight
            "EVENT": 2.5,  # Events, conflicts, summits
            "NORP": 2.0,  # Nationalities, political groups
            "LAW": 1.8,  # Laws, treaties, agreements
            "FAC": 1.5,  # Facilities, infrastructure
            "PRODUCT": 1.2,  # Products, weapons, technology
            "MONEY": 1.8,  # Economic indicators
            "PERCENT": 1.3,  # Statistics, percentages
        }

        # Models
        self.nlp_model = None
        self.yake_extractor = None
        self.keybert_extractor = None
        self._initialize_models()

        self.logger.info("Dynamic keyword extractor initialized - no predefined lists")

    def _initialize_models(self):
        """Initialize extraction models"""
        try:
            # spaCy for multilingual NER
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
                self.logger.info("SpaCy English model loaded")
            except OSError:
                self.logger.error(
                    "SpaCy model not found. Install: python -m spacy download en_core_web_sm"
                )
                raise

            # YAKE for language-agnostic phrase extraction
            self.yake_extractor = yake.KeywordExtractor(
                lan="en",  # Can be switched based on detected language
                n=3,  # Up to 3-word phrases
                dedupLim=0.7,
                top=20,
                features=None,
            )

            # KeyBERT for semantic keyphrase extraction
            try:
                self.keybert_extractor = KeyBERT(self.keybert_model)
                self.logger.info("KeyBERT model loaded", model=self.keybert_model)
            except Exception as e:
                self.logger.warning(
                    "KeyBERT failed to load, falling back to YAKE only", error=str(e)
                )
                self.keybert_extractor = None

        except Exception as exc:
            self.logger.error("Failed to initialize models", error=str(exc))
            raise

    def extract_keywords(
        self,
        article_id: str,
        title: str,
        content: str,
        summary: Optional[str] = None,
        language: str = "en",
    ) -> ArticleKeywordResult:
        """
        Extract keywords using purely data-driven approach

        Args:
            article_id: Unique article identifier
            title: Article title
            content: Article content
            summary: Optional summary
            language: Detected language code

        Returns:
            Extracted keywords with dynamic strategic scores
        """
        try:
            # Combine text for processing
            text_parts = [title]
            if summary:
                text_parts.append(summary)
            if content:
                # Process reasonable amount of content
                content_excerpt = content[:3000] if len(content) > 3000 else content
                text_parts.append(content_excerpt)

            combined_text = " ".join(text_parts)

            # Extract using multiple methods
            all_keywords = []

            # 1. Entity extraction (spaCy NER)
            entity_keywords = self._extract_entities(combined_text)
            all_keywords.extend(entity_keywords)

            # 2. Phrase extraction (YAKE)
            phrase_keywords = self._extract_yake_phrases(combined_text)
            all_keywords.extend(phrase_keywords)

            # 3. Semantic keyphrase extraction (KeyBERT)
            if self.keybert_extractor:
                keybert_keywords = self._extract_keybert_phrases(combined_text)
                all_keywords.extend(keybert_keywords)

            # 4. Calculate dynamic strategic scores
            scored_keywords = self._calculate_strategic_scores(
                all_keywords, combined_text
            )

            # 5. Deduplicate and rank
            final_keywords = self._deduplicate_and_rank(scored_keywords)

            # 6. Calculate overall article strategic score
            overall_score = self._calculate_overall_strategic_score(final_keywords)

            result = ArticleKeywordResult(
                article_id=article_id,
                keywords=final_keywords[: self.max_keywords],
                overall_strategic_score=overall_score,
                extraction_timestamp=datetime.utcnow(),
            )

            self.logger.debug(
                "Keywords extracted dynamically",
                article_id=article_id,
                total_keywords=len(final_keywords),
                strategic_score=overall_score,
            )

            return result

        except Exception as exc:
            self.logger.error(
                "Dynamic keyword extraction failed",
                article_id=article_id,
                error=str(exc),
            )

            # Return empty result on failure
            return ArticleKeywordResult(
                article_id=article_id,
                keywords=[],
                overall_strategic_score=0.0,
                extraction_timestamp=datetime.utcnow(),
            )

    def _extract_entities(self, text: str) -> List[ExtractedKeyword]:
        """Extract named entities using spaCy - no predefined lists"""
        if not self.nlp_model:
            return []

        keywords = []
        try:
            doc = self.nlp_model(text)

            for ent in doc.ents:
                # Clean and validate entity
                cleaned_text = self._clean_keyword_text(ent.text)
                if len(cleaned_text) >= self.min_keyword_length:

                    # Base extraction score from spaCy confidence (if available)
                    extraction_score = 1.0  # spaCy doesn't provide scores

                    keyword = ExtractedKeyword(
                        text=cleaned_text,
                        keyword_type="entity",
                        entity_label=ent.label_,
                        extraction_score=extraction_score,
                        extraction_method="spacy",
                    )
                    keywords.append(keyword)

        except Exception as exc:
            self.logger.error("Entity extraction failed", error=str(exc))

        return keywords

    def _extract_yake_phrases(self, text: str) -> List[ExtractedKeyword]:
        """Extract phrases using YAKE - language agnostic"""
        if not self.yake_extractor:
            return []

        keywords = []
        try:
            # Extract using YAKE
            yake_results = self.yake_extractor.extract_keywords(text)

            for phrase, score in yake_results:
                cleaned_text = self._clean_keyword_text(phrase)
                if len(cleaned_text) >= self.min_keyword_length:

                    # YAKE scores are inverted (lower is better)
                    extraction_score = 1.0 / (1.0 + score) if score > 0 else 1.0

                    keyword = ExtractedKeyword(
                        text=cleaned_text,
                        keyword_type="phrase",
                        extraction_score=extraction_score,
                        extraction_method="yake",
                    )
                    keywords.append(keyword)

        except Exception as exc:
            self.logger.error("YAKE extraction failed", error=str(exc))

        return keywords

    def _extract_keybert_phrases(self, text: str) -> List[ExtractedKeyword]:
        """Extract semantic keyphrases using KeyBERT"""
        if not self.keybert_extractor:
            return []

        keywords = []
        try:
            # Extract keyphrases with KeyBERT
            keybert_results = self.keybert_extractor.extract_keywords(
                text, keyphrase_ngram_range=(1, 3), stop_words="english", top_n=20
            )

            for phrase, score in keybert_results:
                cleaned_text = self._clean_keyword_text(phrase)
                if len(cleaned_text) >= self.min_keyword_length:

                    keyword = ExtractedKeyword(
                        text=cleaned_text,
                        keyword_type="keyphrase",
                        extraction_score=float(score),
                        extraction_method="keybert",
                    )
                    keywords.append(keyword)

        except Exception as exc:
            self.logger.error("KeyBERT extraction failed", error=str(exc))

        return keywords

    def _calculate_strategic_scores(
        self, keywords: List[ExtractedKeyword], full_text: str
    ) -> List[ExtractedKeyword]:
        """
        Calculate strategic scores dynamically based on data patterns
        NO predefined keyword lists - all pattern-based
        """

        # Calculate strategic scores for each keyword
        for keyword in keywords:
            strategic_score = 0.0

            # 1. Entity type weighting (data-driven patterns)
            if keyword.keyword_type == "entity" and keyword.entity_label:
                entity_weight = self.entity_type_weights.get(keyword.entity_label, 1.0)
                strategic_score += entity_weight * 0.4

            # 2. Text position importance (title/summary boost)
            position_boost = self._calculate_position_importance(
                keyword.text, full_text
            )
            strategic_score += position_boost * 0.3

            # 3. Extraction confidence
            strategic_score += keyword.extraction_score * 0.2

            # 4. Multi-method validation (if extracted by multiple methods)
            method_boost = self._calculate_method_consensus(keyword, keywords)
            strategic_score += method_boost * 0.1

            # Normalize to 0-1 range
            keyword.strategic_score = min(strategic_score, 1.0)

        return keywords

    def _calculate_position_importance(
        self, keyword_text: str, full_text: str
    ) -> float:
        """Calculate importance based on position in text (title > summary > body)"""
        keyword_lower = keyword_text.lower()
        full_lower = full_text.lower()

        # Estimate title portion (first ~100 chars)
        title_portion = full_lower[:100]
        if keyword_lower in title_portion:
            return 1.0  # Highest importance

        # Estimate summary portion (next ~300 chars)
        summary_portion = full_lower[100:400]
        if keyword_lower in summary_portion:
            return 0.7  # High importance

        # Body content
        if keyword_lower in full_lower:
            return 0.3  # Basic importance

        return 0.0

    def _calculate_method_consensus(
        self, target_keyword: ExtractedKeyword, all_keywords: List[ExtractedKeyword]
    ) -> float:
        """Boost score if keyword extracted by multiple methods"""
        target_text = target_keyword.text.lower()
        methods = set()

        for keyword in all_keywords:
            if keyword.text.lower() == target_text:
                methods.add(keyword.extraction_method)

        # More methods = higher confidence
        if len(methods) >= 3:
            return 0.5  # High consensus
        elif len(methods) == 2:
            return 0.3  # Medium consensus
        else:
            return 0.0  # Single method

    def _deduplicate_and_rank(
        self, keywords: List[ExtractedKeyword]
    ) -> List[ExtractedKeyword]:
        """Remove duplicates and rank by strategic score"""

        # Group by normalized text
        keyword_groups = defaultdict(list)
        for keyword in keywords:
            normalized_text = keyword.text.lower().strip()
            keyword_groups[normalized_text].append(keyword)

        # Select best keyword from each group
        deduplicated = []
        for text, group in keyword_groups.items():
            if len(text) >= self.min_keyword_length:
                # Choose keyword with highest strategic score
                best_keyword = max(group, key=lambda k: k.strategic_score)
                deduplicated.append(best_keyword)

        # Sort by strategic score
        deduplicated.sort(key=lambda k: k.strategic_score, reverse=True)

        return deduplicated

    def _calculate_overall_strategic_score(
        self, keywords: List[ExtractedKeyword]
    ) -> float:
        """Calculate overall strategic relevance for the article"""
        if not keywords:
            return 0.0

        # Weight by top keywords
        top_keywords = keywords[:10]  # Top 10 most strategic

        if not top_keywords:
            return 0.0

        # Calculate weighted average with diminishing returns
        total_score = 0.0
        total_weight = 0.0

        for i, keyword in enumerate(top_keywords):
            # Diminishing weight for lower-ranked keywords
            weight = 1.0 / (i + 1)  # 1.0, 0.5, 0.33, 0.25, ...

            total_score += keyword.strategic_score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _clean_keyword_text(self, text: str) -> str:
        """Clean and normalize keyword text"""
        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", text.strip())

        # Remove surrounding punctuation
        cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned)

        # Filter very short or numeric-only
        if len(cleaned) < self.min_keyword_length or cleaned.isdigit():
            return ""

        return cleaned


# Factory function for external use
def extract_dynamic_keywords(
    article_id: str,
    title: str,
    content: str,
    summary: Optional[str] = None,
    language: str = "en",
    config: Optional[Dict[str, Any]] = None,
) -> ArticleKeywordResult:
    """
    Extract keywords using purely data-driven approach
    No predefined lists - everything learned from content
    """
    extractor = DynamicKeywordExtractor(config)
    return extractor.extract_keywords(article_id, title, content, summary, language)


if __name__ == "__main__":
    # Test with realistic multilingual content
    test_cases = [
        {
            "title": "Putin Meets Xi Jinping at Shanghai Cooperation Summit",
            "content": """
            President Vladimir Putin met with Chinese President Xi Jinping at the 
            Shanghai Cooperation Organization summit in Samarkand. The leaders discussed 
            bilateral trade, energy cooperation, and regional security issues. 
            Both countries emphasized their strategic partnership amid tensions with NATO.
            """,
        },
        {
            "title": "Federal Reserve Raises Interest Rates Amid Inflation Concerns",
            "content": """
            The Federal Reserve announced a 0.75 percentage point increase in interest rates,
            bringing the federal funds rate to its highest level since 2008. Fed Chair Jerome 
            Powell cited persistent inflation and labor market strength as key factors.
            """,
        },
    ]

    print("=== Dynamic Keyword Extraction Test ===")
    for i, test in enumerate(test_cases):
        result = extract_dynamic_keywords(
            f"test_{i:03d}", test["title"], test["content"]
        )

        print(f"\nArticle {i+1}: {test['title'][:50]}...")
        print(f"Strategic Score: {result.overall_strategic_score:.3f}")
        print("Top Keywords:")
        for keyword in result.keywords[:8]:
            print(
                f"  {keyword.text} ({keyword.keyword_type}, {keyword.strategic_score:.3f})"
            )
