#!/usr/bin/env python3
"""
Improved Dynamic Keyword Extraction System
Strategic Narrative Intelligence ETL Pipeline

Improvements:
1. HTML stripping from content
2. Better entity classification
3. Normalization (lowercase, lemmatization)
4. Noise filtering (numbers, temporal words, boilerplate)
5. Signal preservation (geopolitical phrases, codes)
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import spacy
import structlog
import yake
from bs4 import BeautifulSoup
from keybert import KeyBERT

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedKeyword:
    """Single extracted keyword with metadata"""
    text: str
    keyword_type: str  # 'entity', 'phrase', 'keyphrase'
    entity_label: Optional[str] = None
    extraction_score: float = 0.0
    strategic_score: float = 0.0
    extraction_method: str = "unknown"


@dataclass
class ArticleKeywordResult:
    """Complete keyword extraction result for an article"""
    article_id: str
    keywords: List[ExtractedKeyword]
    overall_strategic_score: float
    extraction_timestamp: datetime
    filter_stats: Dict[str, int]  # Filtering statistics


class DynamicKeywordExtractor:
    """Improved keyword extraction with quality filters"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)

        # Configuration
        self.max_keywords = self.config.get("max_keywords", 50)
        self.min_keyword_length = self.config.get("min_keyword_length", 2)
        self.keybert_model = self.config.get("keybert_model", "paraphrase-MiniLM-L6-v2")

        # Load filter lists
        self._load_filter_lists()

        # Entity type weights with improved mappings
        self.entity_type_weights = {
            "PERSON": 2.0,
            "ORG": 2.5,
            "GPE": 3.0,  # Geopolitical entities
            "EVENT": 2.5,
            "NORP": 2.0,  # Nationalities, political groups
            "LAW": 1.8,
            "FAC": 1.5,
            "PRODUCT": 1.2,
            "MONEY": 1.8,
            "PERCENT": 1.3,
        }

        # Models
        self.nlp_model = None
        self.yake_extractor = None
        self.keybert_extractor = None
        self._initialize_models()

        self.logger.info("Improved keyword extractor initialized with quality filters")

    def _load_filter_lists(self):
        """Load whitelist and stopword files"""
        data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Load phrase whitelist
        phrase_file = data_dir / "phrase_whitelist.txt"
        self.phrase_whitelist = set()
        if phrase_file.exists():
            with open(phrase_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.phrase_whitelist.add(line.lower())
        
        # Load keyword whitelist
        keyword_file = data_dir / "keyword_whitelist.txt"
        self.keyword_whitelist = set()
        if keyword_file.exists():
            with open(keyword_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.keyword_whitelist.add(line.lower())

        # Stopwords and noise patterns
        self.stop_words_en = {
            'today', 'yesterday', 'tomorrow', 'daily', 'annually', 'annual',
            'earlier', 'recently', 'months', 'years', 'decades', 'summertime',
            'weekend', 'weekday', 'weekdays', 'weekends',
            # Written-out numbers and ordinals
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
            'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 
            'eighteen', 'nineteen', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
            'eighty', 'ninety', 'hundred', 'thousand', 'million', 'billion',
            'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 
            'ninth', 'tenth', 'eleventh', 'twelfth'
        }

        self.stop_phrases_en = {
            'continue reading', 'live blog', 'breaking news', 'live updates',
            'as it happens', 'watch', 'listen', 'newsletter', 'subscribe',
            'click here', 'read more', 'learn more'
        }

        # Regex patterns for temporal and noise filtering
        self.stop_regex_patterns = [
            r'\b(last|this|next)\s+(week|month|year|weekend|summer|winter|spring|fall|autumn)\b',
            r'\b\d+-day(s)?\b',
            r'\b\d+-month(s)?\b', 
            r'\b\d+-year(s)?\b',
            r'\bthis\s+(week|month|year|summer)\b'
        ]

        # Keep patterns (signal)
        self.keep_patterns = [
            r'^G\d{1,2}$',  # G7, G20
            r'^COP\d{2}$',  # COP28, COP29
            r'^[A-Za-z]{1,4}-?\d+[A-Za-z]*$',  # F-16, A320neo, H5N1
            r'^\d+[A-Za-z]+$',  # 737MAX, 5G
            r'^[A-Z]{1,3}\d{2,4}$',  # MH17, PS752
            r'^\d{1,2}/\d{1,2}$'  # 9/11, 7/7
        ]

        # Weekdays and months for filtering
        self.weekdays_en = {
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        }
        self.months_en = {
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        }

    def _initialize_models(self):
        """Initialize extraction models"""
        try:
            # spaCy for multilingual NER
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
                self.logger.info("SpaCy English model loaded")
            except OSError:
                self.logger.error("SpaCy model not found. Install: python -m spacy download en_core_web_sm")
                raise

            # YAKE for language-agnostic phrase extraction
            self.yake_extractor = yake.KeywordExtractor(
                lan="en",
                n=3,
                dedupLim=0.7,
                top=20,
                features=None,
            )

            # KeyBERT for semantic keyphrase extraction
            try:
                self.keybert_extractor = KeyBERT(self.keybert_model)
                self.logger.info("KeyBERT model loaded", model=self.keybert_model)
            except Exception as e:
                self.logger.warning("KeyBERT failed to load", error=str(e))
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
        """Extract keywords with improved quality filtering"""
        
        filter_stats = {
            'kept_keywords': 0,
            'dropped_html': 0,
            'dropped_temporal': 0,
            'dropped_boilerplate': 0,
            'dropped_numbers': 0,
            'kept_whitelist': 0,
            'kept_patterns': 0,
            'skipped_non_english': 0
        }
        
        # English-only filter for MVP
        if language != "en":
            filter_stats['skipped_non_english'] = 1
            self.logger.debug(f"Skipped non-English article {article_id} (language: {language})")
            return ArticleKeywordResult(
                article_id=article_id,
                keywords=[],
                overall_strategic_score=0.0,
                extraction_timestamp=datetime.utcnow(),
                filter_stats=filter_stats
            )

        try:
            # 1. HTML stripping
            clean_title = self._strip_html(title)
            clean_content = self._strip_html(content) if content else ""
            clean_summary = self._strip_html(summary) if summary else ""

            # Combine text for processing
            text_parts = [clean_title]
            if clean_summary:
                text_parts.append(clean_summary)
            if clean_content:
                content_excerpt = clean_content[:3000] if len(clean_content) > 3000 else clean_content
                text_parts.append(content_excerpt)

            combined_text = " ".join(text_parts)

            # 2. Extract using multiple methods
            all_keywords = []

            # Entity extraction with improved classification
            entity_keywords = self._extract_entities_improved(combined_text)
            all_keywords.extend(entity_keywords)

            # Phrase extraction
            phrase_keywords = self._extract_yake_phrases(combined_text)
            all_keywords.extend(phrase_keywords)

            # Semantic keyphrase extraction
            if self.keybert_extractor:
                keybert_keywords = self._extract_keybert_phrases(combined_text)
                all_keywords.extend(keybert_keywords)

            # 3. Apply quality filters
            filtered_keywords = self._apply_quality_filters(
                all_keywords, combined_text, filter_stats
            )

            # 4. Calculate strategic scores
            scored_keywords = self._calculate_strategic_scores(
                filtered_keywords, combined_text
            )

            # 5. Deduplicate and rank
            final_keywords = self._deduplicate_and_rank(scored_keywords)

            # 6. Calculate overall strategic score
            overall_score = self._calculate_overall_strategic_score(final_keywords)

            filter_stats['kept_keywords'] = len(final_keywords)

            result = ArticleKeywordResult(
                article_id=article_id,
                keywords=final_keywords[:self.max_keywords],
                overall_strategic_score=overall_score,
                extraction_timestamp=datetime.utcnow(),
                filter_stats=filter_stats
            )

            self.logger.debug(
                "Keywords extracted with quality filters",
                article_id=article_id,
                **filter_stats
            )

            return result

        except Exception as exc:
            self.logger.error(
                "Improved keyword extraction failed",
                article_id=article_id,
                error=str(exc),
            )

            return ArticleKeywordResult(
                article_id=article_id,
                keywords=[],
                overall_strategic_score=0.0,
                extraction_timestamp=datetime.utcnow(),
                filter_stats=filter_stats
            )

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags and entities from text"""
        if not text:
            return ""
        
        try:
            # Use BeautifulSoup to properly handle HTML
            soup = BeautifulSoup(text, 'html.parser')
            cleaned = soup.get_text(separator=' ')
            
            # Clean up extra whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip()
            
        except Exception:
            # Fallback: basic regex HTML removal
            cleaned = re.sub(r'<[^>]+>', ' ', text)
            cleaned = re.sub(r'&[a-zA-Z0-9#]+;', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip()

    def _extract_entities_improved(self, text: str) -> List[ExtractedKeyword]:
        """Extract entities with improved classification"""
        if not self.nlp_model:
            return []

        keywords = []
        try:
            doc = self.nlp_model(text)

            for ent in doc.ents:
                # Clean entity text
                cleaned_text = self._clean_keyword_text(ent.text)
                if len(cleaned_text) < self.min_keyword_length:
                    continue

                # Improved entity classification
                entity_label = self._improve_entity_classification(cleaned_text, ent.label_)
                
                keyword = ExtractedKeyword(
                    text=cleaned_text,
                    keyword_type="entity",
                    entity_label=entity_label,
                    extraction_score=1.0,
                    extraction_method="spacy",
                )
                keywords.append(keyword)

        except Exception as exc:
            self.logger.error("Entity extraction failed", error=str(exc))

        return keywords

    def _improve_entity_classification(self, text: str, original_label: str) -> str:
        """Improve entity classification based on context"""
        text_lower = text.lower()
        
        # Fix common misclassifications
        known_people = {'trump', 'biden', 'putin', 'xi jinping', 'macron', 'merkel'}
        known_orgs = {'nato', 'eu', 'un', 'who', 'imf', 'world bank', 'federal reserve'}
        known_places = {'ben gurion', 'heathrow', 'jfk airport'}
        
        if any(person in text_lower for person in known_people):
            return "PERSON"
        elif any(org in text_lower for org in known_orgs):
            return "ORG"
        elif any(place in text_lower for place in known_places):
            return "FAC"  # Facility for airports
        
        # Keep original if no improvement found
        return original_label

    def _extract_yake_phrases(self, text: str) -> List[ExtractedKeyword]:
        """Extract phrases using YAKE"""
        if not self.yake_extractor:
            return []

        keywords = []
        try:
            yake_results = self.yake_extractor.extract_keywords(text)

            for phrase, score in yake_results:
                cleaned_text = self._clean_keyword_text(phrase)
                if len(cleaned_text) >= self.min_keyword_length:
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

    def _apply_quality_filters(
        self, keywords: List[ExtractedKeyword], full_text: str, stats: Dict[str, int]
    ) -> List[ExtractedKeyword]:
        """Apply quality filters to remove noise and preserve signals"""
        
        filtered = []
        
        # Build phrase context from title + summary for whitelist checking
        title_summary_text = full_text[:400].lower()  # First 400 chars
        
        for keyword in keywords:
            text_lower = keyword.text.lower().strip()
            
            # Always keep whitelisted terms
            if text_lower in self.keyword_whitelist:
                filtered.append(keyword)
                stats['kept_whitelist'] += 1
                continue
            
            # Check if part of whitelisted phrase
            if any(phrase in title_summary_text for phrase in self.phrase_whitelist if text_lower in phrase):
                filtered.append(keyword)
                stats['kept_whitelist'] += 1
                continue
            
            # Keep patterns that match signal rules
            if any(re.match(pattern, text_lower, re.IGNORECASE) for pattern in self.keep_patterns):
                filtered.append(keyword)
                stats['kept_patterns'] += 1
                continue
            
            # Filter noise patterns
            should_drop = False
            
            # Drop pure numbers and ordinals
            if re.match(r'^\d+$', text_lower):  # Pure numbers
                should_drop = True
                stats['dropped_numbers'] += 1
            elif re.match(r'^\d{4}$', text_lower):  # Years
                should_drop = True
                stats['dropped_numbers'] += 1
            elif re.match(r'^\d+(st|nd|rd|th)$', text_lower):  # Ordinals
                should_drop = True
                stats['dropped_numbers'] += 1
            
            # Drop temporal words
            elif text_lower in self.stop_words_en:
                should_drop = True
                stats['dropped_temporal'] += 1
            elif text_lower in self.weekdays_en or text_lower in self.months_en:
                should_drop = True
                stats['dropped_temporal'] += 1
            
            # Drop boilerplate phrases
            elif text_lower in self.stop_phrases_en:
                should_drop = True
                stats['dropped_boilerplate'] += 1
            
            # Drop temporal regex patterns
            elif any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.stop_regex_patterns):
                should_drop = True
                stats['dropped_temporal'] += 1
            
            if not should_drop:
                filtered.append(keyword)
        
        return filtered

    def _calculate_strategic_scores(
        self, keywords: List[ExtractedKeyword], full_text: str
    ) -> List[ExtractedKeyword]:
        """Calculate strategic scores dynamically"""
        
        for keyword in keywords:
            strategic_score = 0.0

            # Entity type weighting
            if keyword.keyword_type == "entity" and keyword.entity_label:
                entity_weight = self.entity_type_weights.get(keyword.entity_label, 1.0)
                strategic_score += entity_weight * 0.4

            # Text position importance
            position_boost = self._calculate_position_importance(keyword.text, full_text)
            strategic_score += position_boost * 0.3

            # Extraction confidence
            strategic_score += keyword.extraction_score * 0.2

            # Multi-method validation
            method_boost = self._calculate_method_consensus(keyword, keywords)
            strategic_score += method_boost * 0.1

            # Normalize to 0-1 range
            keyword.strategic_score = min(strategic_score, 1.0)

        return keywords

    def _calculate_position_importance(self, keyword_text: str, full_text: str) -> float:
        """Calculate importance based on position in text"""
        keyword_lower = keyword_text.lower()
        full_lower = full_text.lower()

        # Title portion (first ~100 chars)
        title_portion = full_lower[:100]
        if keyword_lower in title_portion:
            return 1.0

        # Summary portion (next ~300 chars)
        summary_portion = full_lower[100:400]
        if keyword_lower in summary_portion:
            return 0.7

        # Body content
        if keyword_lower in full_lower:
            return 0.3

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

        if len(methods) >= 3:
            return 0.5
        elif len(methods) == 2:
            return 0.3
        else:
            return 0.0

    def _deduplicate_and_rank(self, keywords: List[ExtractedKeyword]) -> List[ExtractedKeyword]:
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
                best_keyword = max(group, key=lambda k: k.strategic_score)
                deduplicated.append(best_keyword)

        # Sort by strategic score
        deduplicated.sort(key=lambda k: k.strategic_score, reverse=True)
        return deduplicated

    def _calculate_overall_strategic_score(self, keywords: List[ExtractedKeyword]) -> float:
        """Calculate overall strategic relevance for the article"""
        if not keywords:
            return 0.0

        top_keywords = keywords[:10]
        if not top_keywords:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for i, keyword in enumerate(top_keywords):
            weight = 1.0 / (i + 1)
            total_score += keyword.strategic_score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _clean_keyword_text(self, text: str) -> str:
        """Clean and normalize keyword text"""
        # Strip HTML artifacts
        cleaned = re.sub(r'[<>]', ' ', text)
        cleaned = re.sub(r'\d+(\.\d+)?(em|px|%);?', ' ', cleaned)  # CSS values
        cleaned = re.sub(r'(div|span|class|style|href)', ' ', cleaned)  # HTML terms
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())

        # Remove surrounding punctuation
        cleaned = re.sub(r'^[^\w]+|[^\w]+$', '', cleaned)

        # Normalize case (lowercase for processing)
        cleaned = cleaned.lower()

        # Filter very short or pure numeric
        if len(cleaned) < self.min_keyword_length or cleaned.isdigit():
            return ""

        return cleaned


# Global singleton extractor to avoid reloading models
_global_extractor = None

def get_singleton_extractor(config: Optional[Dict[str, Any]] = None) -> DynamicKeywordExtractor:
    """Get or create singleton extractor to reuse models"""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = DynamicKeywordExtractor(config)
    return _global_extractor

# Factory function for external use
def extract_dynamic_keywords(
    article_id: str,
    title: str,
    content: str,
    summary: Optional[str] = None,
    language: str = "en",
    config: Optional[Dict[str, Any]] = None,
) -> ArticleKeywordResult:
    """Extract keywords with improved quality filtering using singleton extractor"""
    extractor = get_singleton_extractor(config)
    return extractor.extract_keywords(article_id, title, content, summary, language)


if __name__ == "__main__":
    # Test with realistic content including HTML artifacts
    test_content = """
    <div class="article-content" style="margin: 1.2em;"><p>
    President Donald Trump met with Chinese President Xi Jinping at Mar-a-Lago yesterday.
    The leaders discussed trade agreements and tariffs affecting billions of dollars.
    <span class="highlight">Continue reading for live updates.</span>
    </p></div>
    """
    
    print("=== Improved Keyword Extraction Test ===")
    result = extract_dynamic_keywords(
        "test_001", 
        "Trump Meets Xi at Mar-a-Lago Summit", 
        test_content
    )
    
    print(f"Strategic Score: {result.overall_strategic_score:.3f}")
    print(f"Filter Stats: {result.filter_stats}")
    print("Top Keywords:")
    for keyword in result.keywords[:10]:
        print(f"  {keyword.text} ({keyword.keyword_type}, {keyword.strategic_score:.3f})")