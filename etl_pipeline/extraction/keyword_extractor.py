#!/usr/bin/env python3
"""
Keyword Extraction Infrastructure
Strategic Narrative Intelligence ETL Pipeline

Replaces semantic clustering with dynamic keyword extraction system.
Provides entity extraction, key phrase extraction, and strategic scoring.
"""

import logging
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import spacy
import structlog
import yake
from sklearn.feature_extraction.text import TfidfVectorizer

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedEntity:
    """Extracted named entity"""

    text: str
    label: str  # PERSON, ORG, GPE, EVENT, etc.
    start_char: int
    end_char: int
    confidence: float


@dataclass
class KeyPhrase:
    """Extracted key phrase"""

    phrase: str
    score: float
    method: str  # 'yake', 'tfidf', 'entity'


@dataclass
class ArticleKeywords:
    """Complete keyword extraction result for an article"""

    article_id: str
    entities: List[ExtractedEntity]
    key_phrases: List[KeyPhrase]
    strategic_score: float
    top_keywords: List[str]  # Combined ranked keywords


class KeywordExtractor:
    """
    Comprehensive keyword extraction system for articles

    Uses multiple methods:
    1. Named Entity Recognition (spaCy)
    2. Key phrase extraction (YAKE)
    3. TF-IDF term extraction
    4. Strategic relevance scoring
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)

        # Configuration parameters
        self.strategic_entity_types = self.config.get(
            "strategic_entity_types", ["PERSON", "ORG", "GPE", "EVENT", "NORP"]
        )
        self.min_entity_length = self.config.get("min_entity_length", 2)
        self.max_phrases = self.config.get("max_phrases", 20)
        self.yake_ngram_size = self.config.get("yake_ngram_size", 3)
        self.yake_deduplication_threshold = self.config.get(
            "yake_deduplication_threshold", 0.7
        )

        # Strategic keyword patterns
        self.strategic_patterns = self._load_strategic_patterns()

        # Initialize models
        self.nlp_model = None
        self.yake_extractor = None
        self.tfidf_vectorizer = None
        self._initialize_models()

        self.logger.info(
            "Keyword extractor initialized",
            strategic_entity_types=self.strategic_entity_types,
        )

    def _initialize_models(self):
        """Initialize NLP models and extractors"""
        try:
            # Load spaCy model
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
                self.logger.info("SpaCy model loaded successfully")
            except OSError:
                self.logger.error(
                    "SpaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm"
                )
                raise

            # Initialize YAKE extractor
            self.yake_extractor = yake.KeywordExtractor(
                lan="en",
                n=self.yake_ngram_size,
                dedupLim=self.yake_deduplication_threshold,
                top=self.max_phrases,
                features=None,
            )

            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                stop_words="english",
                lowercase=True,
                token_pattern=r"\b[A-Za-z][A-Za-z0-9-]*[A-Za-z0-9]\b|\b[A-Za-z]\b",
            )

        except Exception as exc:
            self.logger.error("Failed to initialize models", error=str(exc))
            raise

    def _load_strategic_patterns(self) -> Dict[str, List[str]]:
        """Load strategic keyword patterns for scoring"""
        return {
            "geopolitical": [
                "sanctions",
                "diplomacy",
                "treaty",
                "alliance",
                "summit",
                "bilateral",
                "trade war",
                "embargo",
                "negotiations",
                "diplomatic",
                "sovereignty",
            ],
            "security": [
                "military",
                "defense",
                "security",
                "intelligence",
                "terrorism",
                "conflict",
                "warfare",
                "peacekeeping",
                "arms",
                "nuclear",
                "cyber",
                "surveillance",
            ],
            "economic": [
                "tariffs",
                "trade",
                "economy",
                "financial",
                "currency",
                "market",
                "investment",
                "economic policy",
                "inflation",
                "gdp",
                "recession",
            ],
            "technology": [
                "artificial intelligence",
                "ai",
                "technology",
                "semiconductor",
                "tech",
                "digital",
                "cyber",
                "innovation",
                "data",
                "privacy",
                "blockchain",
            ],
            "international": [
                "united nations",
                "nato",
                "eu",
                "european union",
                "g7",
                "g20",
                "international",
                "global",
                "multilateral",
                "regional",
            ],
        }

    def extract_keywords(
        self, article_id: str, title: str, content: str, summary: Optional[str] = None
    ) -> ArticleKeywords:
        """
        Extract keywords from article using all methods

        Args:
            article_id: Unique article identifier
            title: Article title
            content: Article content
            summary: Optional article summary

        Returns:
            Complete keyword extraction results
        """
        try:
            # Combine text sources
            text_parts = [title]
            if summary:
                text_parts.append(summary)
            if content:
                # Take first 2000 characters to avoid processing very long articles
                content_excerpt = content[:2000] if len(content) > 2000 else content
                text_parts.append(content_excerpt)

            combined_text = " ".join(text_parts)

            # Extract using different methods
            entities = self._extract_entities(combined_text)
            yake_phrases = self._extract_yake_phrases(combined_text)
            tfidf_phrases = self._extract_tfidf_phrases([combined_text])

            # Combine and rank keywords
            all_phrases = (
                yake_phrases + tfidf_phrases + self._entities_to_phrases(entities)
            )
            top_keywords = self._rank_combined_keywords(all_phrases)

            # Calculate strategic score
            strategic_score = self._calculate_strategic_score(
                entities, all_phrases, combined_text
            )

            result = ArticleKeywords(
                article_id=article_id,
                entities=entities,
                key_phrases=all_phrases,
                strategic_score=strategic_score,
                top_keywords=top_keywords[:20],  # Top 20 keywords
            )

            self.logger.debug(
                "Keywords extracted",
                article_id=article_id,
                entities=len(entities),
                phrases=len(all_phrases),
                strategic_score=strategic_score,
            )

            return result

        except Exception as exc:
            self.logger.error(
                "Keyword extraction failed", article_id=article_id, error=str(exc)
            )
            # Return empty result on failure
            return ArticleKeywords(
                article_id=article_id,
                entities=[],
                key_phrases=[],
                strategic_score=0.0,
                top_keywords=[],
            )

    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract named entities using spaCy"""
        if not self.nlp_model:
            return []

        entities = []
        try:
            doc = self.nlp_model(text)

            for ent in doc.ents:
                if (
                    ent.label_ in self.strategic_entity_types
                    and len(ent.text.strip()) >= self.min_entity_length
                ):

                    # Clean entity text
                    entity_text = self._clean_entity_text(ent.text)
                    if entity_text:
                        entities.append(
                            ExtractedEntity(
                                text=entity_text,
                                label=ent.label_,
                                start_char=ent.start_char,
                                end_char=ent.end_char,
                                confidence=1.0,  # spaCy doesn't provide confidence scores
                            )
                        )

            # Deduplicate entities
            entities = self._deduplicate_entities(entities)

        except Exception as exc:
            self.logger.error("Entity extraction failed", error=str(exc))

        return entities

    def _extract_yake_phrases(self, text: str) -> List[KeyPhrase]:
        """Extract key phrases using YAKE algorithm"""
        if not self.yake_extractor:
            return []

        phrases = []
        try:
            # Extract keywords using YAKE
            keywords = self.yake_extractor.extract_keywords(text)

            for keyword, score in keywords:
                # YAKE scores are inverted (lower is better), so invert for consistency
                normalized_score = 1.0 / (1.0 + score) if score > 0 else 1.0

                phrases.append(
                    KeyPhrase(
                        phrase=keyword.lower().strip(),
                        score=normalized_score,
                        method="yake",
                    )
                )

        except Exception as exc:
            self.logger.error("YAKE extraction failed", error=str(exc))

        return phrases

    def _extract_tfidf_phrases(self, texts: List[str]) -> List[KeyPhrase]:
        """Extract key phrases using TF-IDF"""
        if not self.tfidf_vectorizer or not texts:
            return []

        phrases = []
        try:
            # Fit TF-IDF on the texts
            if len(texts) == 1:
                # For single document, create a dummy corpus to avoid TF-IDF issues
                texts = texts + ["dummy document for tfidf"]

            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()

            # Get TF-IDF scores for first document (the actual article)
            if tfidf_matrix.shape[0] > 0:
                scores = tfidf_matrix[0].toarray()[0]

                # Create phrases from top-scoring terms
                for i, score in enumerate(scores):
                    if score > 0:
                        phrases.append(
                            KeyPhrase(
                                phrase=feature_names[i].lower(),
                                score=float(score),
                                method="tfidf",
                            )
                        )

                # Sort by score and take top phrases
                phrases.sort(key=lambda x: x.score, reverse=True)
                phrases = phrases[: self.max_phrases]

        except Exception as exc:
            self.logger.error("TF-IDF extraction failed", error=str(exc))

        return phrases

    def _entities_to_phrases(self, entities: List[ExtractedEntity]) -> List[KeyPhrase]:
        """Convert entities to key phrases with strategic scoring"""
        phrases = []

        # Count entity frequencies
        entity_counts = Counter(entity.text.lower() for entity in entities)
        max_count = max(entity_counts.values()) if entity_counts else 1

        for entity in entities:
            entity_lower = entity.text.lower()
            frequency_score = entity_counts[entity_lower] / max_count

            # Boost score for strategic entity types
            strategic_boost = 1.0
            if entity.label in ["PERSON", "ORG", "GPE"]:
                strategic_boost = 1.5
            elif entity.label == "EVENT":
                strategic_boost = 1.3

            final_score = frequency_score * strategic_boost

            phrases.append(
                KeyPhrase(phrase=entity_lower, score=final_score, method="entity")
            )

        return phrases

    def _rank_combined_keywords(self, phrases: List[KeyPhrase]) -> List[str]:
        """Combine and rank keywords from all extraction methods"""
        # Group phrases by text
        phrase_groups = defaultdict(list)
        for phrase in phrases:
            phrase_groups[phrase.phrase].extend([phrase])

        # Calculate combined scores
        scored_keywords = []
        for phrase_text, phrase_list in phrase_groups.items():
            # Combine scores from different methods
            yake_score = max(
                [p.score for p in phrase_list if p.method == "yake"], default=0.0
            )
            tfidf_score = max(
                [p.score for p in phrase_list if p.method == "tfidf"], default=0.0
            )
            entity_score = max(
                [p.score for p in phrase_list if p.method == "entity"], default=0.0
            )

            # Weighted combination
            combined_score = yake_score * 0.4 + tfidf_score * 0.4 + entity_score * 0.2

            # Boost strategic keywords
            strategic_boost = self._get_strategic_boost(phrase_text)
            final_score = combined_score * strategic_boost

            scored_keywords.append((phrase_text, final_score))

        # Sort by score and return keyword list
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        return [keyword for keyword, score in scored_keywords]

    def _calculate_strategic_score(
        self, entities: List[ExtractedEntity], phrases: List[KeyPhrase], text: str
    ) -> float:
        """Calculate overall strategic relevance score for article"""
        strategic_score = 0.0

        # Score based on strategic entities
        strategic_entity_count = sum(
            1
            for entity in entities
            if entity.label in ["PERSON", "ORG", "GPE", "EVENT"]
        )
        entity_score = min(strategic_entity_count / 10.0, 1.0)  # Normalize to 0-1

        # Score based on strategic phrases
        strategic_phrases = 0
        for phrase in phrases:
            if self._get_strategic_boost(phrase.phrase) > 1.0:
                strategic_phrases += 1

        phrase_score = min(strategic_phrases / 10.0, 1.0)  # Normalize to 0-1

        # Score based on strategic patterns in text
        pattern_score = self._score_strategic_patterns(text.lower())

        # Combine scores
        strategic_score = entity_score * 0.4 + phrase_score * 0.3 + pattern_score * 0.3

        return strategic_score

    def _get_strategic_boost(self, phrase: str) -> float:
        """Get strategic relevance boost for a phrase"""
        phrase_lower = phrase.lower()

        for category, keywords in self.strategic_patterns.items():
            for keyword in keywords:
                if keyword in phrase_lower:
                    return 1.5  # 50% boost for strategic keywords

        return 1.0  # No boost for non-strategic phrases

    def _score_strategic_patterns(self, text: str) -> float:
        """Score text for strategic patterns"""
        total_patterns = 0
        matched_patterns = 0

        for category, keywords in self.strategic_patterns.items():
            total_patterns += len(keywords)
            for keyword in keywords:
                if keyword in text:
                    matched_patterns += 1

        return matched_patterns / total_patterns if total_patterns > 0 else 0.0

    def _clean_entity_text(self, text: str) -> str:
        """Clean and normalize entity text"""
        # Remove extra whitespace and punctuation
        cleaned = re.sub(r"\s+", " ", text.strip())
        cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned)

        # Filter out very short or invalid entities
        if len(cleaned) < 2:
            return ""

        # Filter out common noise patterns
        noise_patterns = [r"^\d+$", r"^[A-Z]$", r"^(the|a|an|and|or|but)$"]
        for pattern in noise_patterns:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return ""

        return cleaned

    def _deduplicate_entities(
        self, entities: List[ExtractedEntity]
    ) -> List[ExtractedEntity]:
        """Remove duplicate entities"""
        seen = set()
        deduplicated = []

        for entity in entities:
            entity_key = (entity.text.lower(), entity.label)
            if entity_key not in seen:
                seen.add(entity_key)
                deduplicated.append(entity)

        return deduplicated


# Convenience function for external usage
def extract_article_keywords(
    article_id: str,
    title: str,
    content: str,
    summary: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> ArticleKeywords:
    """Extract keywords from a single article"""
    extractor = KeywordExtractor(config)
    return extractor.extract_keywords(article_id, title, content, summary)


if __name__ == "__main__":
    # Test the keyword extractor
    test_title = (
        "Trump Administration Imposes New Tariffs on Chinese Technology Imports"
    )
    test_content = """
    The Trump administration announced sweeping new tariffs on Chinese technology imports, 
    escalating the ongoing trade war between the two superpowers. The tariffs target 
    artificial intelligence chips, semiconductors, and telecommunications equipment from 
    major Chinese companies including Huawei and ZTE. 
    
    Trade officials in Washington said the measures are necessary to protect American 
    national security interests and reduce dependence on Chinese technology. The move 
    comes as tensions rise over Taiwan and South China Sea territorial disputes.
    
    Chinese officials condemned the tariffs as protectionist and vowed to retaliate 
    with their own trade restrictions on American agricultural exports.
    """

    # Extract keywords
    result = extract_article_keywords("test_001", test_title, test_content)

    print("=== Keyword Extraction Test ===")
    print(f"Strategic Score: {result.strategic_score:.3f}")
    print(f"Entities: {[e.text + ' (' + e.label + ')' for e in result.entities]}")
    print(f"Top Keywords: {result.top_keywords[:10]}")
