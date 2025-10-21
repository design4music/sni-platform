"""
Multi-Vocabulary Taxonomy Extractor
Single source of truth for strategic/non-strategic detection using multiple go/stop lists
Used by both CLUST-1 (Strategic Gate) and CLUST-2 (Big-Bucket Grouping)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Pattern, Tuple


class VocabType(Enum):
    """Vocabulary types for strategic filtering"""

    GO_ACTORS = "go_actors"
    GO_PEOPLE = "go_people"
    GO_TAXONOMY = "go_taxonomy"  # Future
    STOP_CULTURE = "stop_culture"


@dataclass
class MatchResult:
    """Enhanced match result with classification"""

    entity_id: str
    vocab_type: VocabType
    is_strategic: bool  # True for GO lists, False for STOP lists


class MultiVocabTaxonomyExtractor:
    """
    Multi-vocabulary extractor supporting go/stop list architecture.

    Key Logic:
    - STOP lists override GO lists (stop_culture.csv beats everything)
    - GO lists (actors, people, taxonomy) mark content as strategic
    - Identical normalization and matching rules across CLUST-1 and CLUST-2
    """

    def __init__(
        self,
        go_actors: Dict[str, List[str]],
        go_people: Dict[str, List[str]],
        stop_culture: Dict[str, List[str]],
        go_taxonomy: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Initialize with multiple vocabulary dictionaries.

        Args:
            go_actors: Actors vocabulary (countries, orgs, movements)
            go_people: People vocabulary (leaders, influencers, etc.)
            stop_culture: Stop culture vocabulary (fashion, sports, lifestyle)
            go_taxonomy: Future taxonomy vocabulary (optional)
        """

        # Separate pattern storage by type
        self._go_patterns: Dict[
            VocabType, List[Tuple[str, Optional[Pattern], Optional[str], bool]]
        ] = {
            VocabType.GO_ACTORS: [],
            VocabType.GO_PEOPLE: [],
            VocabType.GO_TAXONOMY: [],
        }
        self._stop_patterns: Dict[
            VocabType, List[Tuple[str, Optional[Pattern], Optional[str], bool]]
        ] = {VocabType.STOP_CULTURE: []}

        # Mapping entity_id -> display name (first alias is name_en from database)
        self._entity_display_names: Dict[str, str] = {}

        # Build patterns for each vocabulary
        self._build_patterns(go_actors, VocabType.GO_ACTORS, is_strategic=True)
        self._build_patterns(go_people, VocabType.GO_PEOPLE, is_strategic=True)
        self._build_patterns(stop_culture, VocabType.STOP_CULTURE, is_strategic=False)
        if go_taxonomy:
            self._build_patterns(go_taxonomy, VocabType.GO_TAXONOMY, is_strategic=True)

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text using identical rules as title_norm processing.

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text (NFKC, lowercase, collapsed whitespace, no periods)
        """
        if not text:
            return ""

        # NFKC Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Remove periods (for matching "U.S." to "us", "U.K." to "uk", etc.)
        text = text.replace(".", "")

        # Lowercase and collapse whitespace
        text = re.sub(r"\s+", " ", text.lower()).strip()

        return text

    def _has_substring_script_chars(self, text: str) -> bool:
        """Check if text contains scripts that need substring matching (no word boundaries)"""
        return any(
            "\u4e00" <= char <= "\u9fff"  # Chinese (Han ideographs)
            or "\u3040" <= char <= "\u309f"  # Japanese Hiragana
            or "\u30a0" <= char <= "\u30ff"  # Japanese Katakana
            or "\u0e00" <= char <= "\u0e7f"  # Thai
            for char in text
        )

    def _is_common_word_false_positive(self, alias_lower: str) -> bool:
        """
        Filter out common English words that match entity codes.
        These cause false positives (e.g., "in" matching India "IN", "who" matching WHO).
        """
        common_words = {
            # 2-letter words
            "in",
            "is",
            "it",
            "as",
            "or",
            "no",
            "so",
            "to",
            "an",
            "at",
            "be",
            "by",
            "do",
            "go",
            "he",
            "if",
            "me",
            "my",
            "of",
            "on",
            "we",
            # 3-letter words
            "who",
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
        }
        return alias_lower in common_words

    def _build_patterns(
        self, aliases: Dict[str, List[str]], vocab_type: VocabType, is_strategic: bool
    ) -> None:
        """
        Precompile regex patterns for vocabulary matching.

        Args:
            aliases: Vocabulary aliases dictionary
            vocab_type: Type of vocabulary being processed
            is_strategic: Whether this vocabulary marks content as strategic
        """

        target_dict = self._go_patterns if is_strategic else self._stop_patterns
        pattern_list = []

        for entity_id, alias_list in aliases.items():
            # Store display name (first alias is name_en from database)
            if (
                is_strategic
                and alias_list
                and entity_id not in self._entity_display_names
            ):
                self._entity_display_names[entity_id] = alias_list[0]

            for alias in alias_list:
                alias_lower = alias.strip().lower()

                # Skip common English words that are false positives (e.g., "in" for India)
                if self._is_common_word_false_positive(alias_lower):
                    continue

                # Check if alias contains scripts that need substring matching
                has_substring_script = self._has_substring_script_chars(alias)

                if has_substring_script:
                    # For Chinese/Japanese/Thai only, use substring matching (no word boundaries)
                    pattern_list.append((entity_id, None, alias_lower, True))
                else:
                    # For Latin/Cyrillic (both single-word and multi-word), use strict word boundary regex
                    # This prevents "ROK" from matching "brokeback" and "EU" from matching "museum"
                    pattern = re.compile(
                        r"\b" + re.escape(alias_lower) + r"\b", re.IGNORECASE
                    )
                    pattern_list.append((entity_id, pattern, None, False))

        target_dict[vocab_type] = pattern_list

    def strategic_first_hit(self, text: str) -> Optional[str]:
        """
        CLUST-1 Strategic Gate logic with go/stop list precedence.

        Args:
            text: Text to analyze for strategic content

        Returns:
            entity_id if strategic, None if non-strategic or no match

        Logic:
        1. Check STOP lists first (override everything)
        2. Check GO lists (any hit = strategic)
        3. No matches = non-strategic
        """
        normalized_text = self.normalize(text)
        if not normalized_text:
            return None

        # 1. Check STOP lists first (blocks strategic classification)
        for vocab_type, patterns in self._stop_patterns.items():
            stop_match = self._check_patterns(normalized_text, patterns)
            if stop_match:
                return None  # STOP list blocks -> non-strategic

        # 2. Check GO lists (any hit = strategic)
        for vocab_type, patterns in self._go_patterns.items():
            go_match = self._check_patterns(normalized_text, patterns)
            if go_match:
                # Return display name instead of entity_id
                return self._entity_display_names.get(go_match, go_match)

        return None  # No matches -> non-strategic

    def all_strategic_hits(self, text: str) -> List[str]:
        """
        CLUST-2 Actor Set logic with go/stop list awareness.

        Args:
            text: Text to analyze for strategic actors

        Returns:
            List of strategic entity names (empty if blocked by stop list)
            Auto-enriched with countries for detected PERSON entities

        Logic:
        1. Check STOP lists first (blocks everything)
        2. Collect all GO matches if not blocked
        3. Auto-add countries for detected people (based on iso_code)
        """
        normalized_text = self.normalize(text)
        if not normalized_text:
            return []

        # 1. Check STOP lists first (blocks everything)
        for vocab_type, patterns in self._stop_patterns.items():
            if self._check_patterns(normalized_text, patterns):
                return []  # STOP list blocks -> no actors for clustering

        # 2. Collect all GO matches
        hits = []
        seen = set()

        for vocab_type, patterns in self._go_patterns.items():
            for entity_id, pattern, alias, use_substring in patterns:
                if entity_id in seen:
                    continue

                matched = False
                if use_substring:
                    if alias and alias in normalized_text:
                        matched = True
                else:
                    if pattern and pattern.search(normalized_text):
                        matched = True

                if matched:
                    seen.add(entity_id)
                    # Append display name instead of entity_id
                    display_name = self._entity_display_names.get(entity_id, entity_id)
                    hits.append(display_name)

        # 3. Auto-add countries for detected people
        from apps.filter.country_enrichment import \
            enrich_entities_with_countries

        enriched_hits = enrich_entities_with_countries(hits)

        return enriched_hits

    def _check_patterns(self, text: str, patterns: List) -> Optional[str]:
        """Check patterns and return first match entity_id"""
        for entity_id, pattern, alias, use_substring in patterns:
            if use_substring:
                if alias and alias in text:
                    return entity_id
            else:
                if pattern and pattern.search(text):
                    return entity_id
        return None


# Factory Functions
def create_multi_vocab_taxonomy_extractor() -> MultiVocabTaxonomyExtractor:
    """
    Factory function to create enhanced TaxonomyExtractor with multiple vocabularies.
    Now uses database-backed vocab loader instead of CSV files.

    Returns:
        MultiVocabTaxonomyExtractor instance with all loaded vocabularies
    """
    from apps.filter.vocab_loader_db import (load_actor_aliases,
                                             load_go_people_aliases,
                                             load_go_taxonomy_aliases,
                                             load_stop_culture_phrases)

    # Load all vocabularies from database (stop_culture still from CSV)
    go_actors = load_actor_aliases()
    go_people = load_go_people_aliases()
    stop_culture = load_stop_culture_phrases()
    go_taxonomy = load_go_taxonomy_aliases()

    return MultiVocabTaxonomyExtractor(go_actors, go_people, stop_culture, go_taxonomy)
