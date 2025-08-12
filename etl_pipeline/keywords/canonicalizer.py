#!/usr/bin/env python3
"""
Enhanced Keyword Canonicalizer
Strategic Narrative Intelligence ETL Pipeline

Advanced canonicalization with:
- Title/honorific stripping
- Acronym expansion
- Demonym->country conversion (standalone only)
- Punctuation normalization
- Database integration
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger(__name__)


class AdvancedCanonicalizer:
    """Enhanced canonicalizer with titles, acronyms, and demonyms."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = (
            config_path
            or Path(__file__).parent.parent.parent / "data" / "keyword_synonyms.yml"
        )
        self.config = self._load_config()

        # Build lookup tables
        self.variant_to_canonical = self._build_variant_map()
        self.phrase_whitelist = set(self.config.get("phrases_whitelist", []))
        self.stop_words = set(self.config.get("stop_words", []))
        self.stop_phrases = set(self.config.get("stop_phrases", []))
        self.stop_regex_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get("stop_regex", [])
        ]
        self.keeper_regex_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get("keepers_regex", [])
        ]

        # Enhanced features
        self.titles_honorifics = self._build_titles_set()
        self.acronym_expansions = self._build_acronym_map()
        self.demonym_countries = self._build_demonym_map()
        self.concept_clusters = self._build_concept_clusters()

        logger.info(
            f"Enhanced canonicalizer loaded: {len(self.variant_to_canonical)} mappings, "
            f"{len(self.acronym_expansions)} acronyms, {len(self.demonym_countries)} demonyms"
        )

    def _load_config(self) -> Dict:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}

    def _build_titles_set(self) -> Set[str]:
        """Build set of titles and honorifics to strip."""
        titles = {
            # Political titles
            "president",
            "prime minister",
            "pm",
            "chancellor",
            "minister",
            "secretary",
            "governor",
            "mayor",
            "senator",
            "congressman",
            "congresswoman",
            "representative",
            "ambassador",
            "envoy",
            "deputy",
            "vice president",
            "vp",
            # Honorifics
            "mr",
            "mrs",
            "ms",
            "miss",
            "sir",
            "madam",
            "dr",
            "prof",
            "professor",
            # Military
            "general",
            "admiral",
            "colonel",
            "major",
            "captain",
            "lieutenant",
            # Business
            "ceo",
            "cfo",
            "cto",
            "chairman",
            "director",
            "executive",
            # Religious
            "pope",
            "bishop",
            "cardinal",
            "rabbi",
            "imam",
            "pastor",
            "reverend",
        }
        return titles

    def _build_acronym_map(self) -> Dict[str, str]:
        """Build acronym -> expanded form mapping from synonyms."""
        acronyms = {}

        synonyms = self.config.get("synonyms", {})
        for canonical, variants in synonyms.items():
            for variant in variants:
                variant_norm = self._normalize_text_basic(variant)
                # Check if variant looks like acronym (short, mostly uppercase letters)
                if len(variant_norm) <= 4 and re.match(r"^[a-z]+$", variant_norm):
                    acronyms[variant_norm] = canonical

        # Add common acronyms not in synonyms
        additional_acronyms = {
            "us": "united states",
            "usa": "united states",
            "uk": "united kingdom",
            "eu": "european union",
            "prc": "china",
            "uae": "united arab emirates",
            "un": "united nations",
            "nato": "nato",  # Keep as-is (already in synonyms)
            "imf": "international monetary fund",
            "who": "world health organization",
            "fbi": "federal bureau of investigation",
            "cia": "central intelligence agency",
        }
        acronyms.update(additional_acronyms)

        return acronyms

    def _build_demonym_map(self) -> Dict[str, str]:
        """Build demonym -> country mapping (for standalone use only)."""
        demonyms = {
            "american": "united states",
            "british": "united kingdom",
            "chinese": "china",
            "russian": "russia",
            "ukrainian": "ukraine",
            "israeli": "israel",
            "palestinian": "palestine",
            "iranian": "iran",
            "iraqi": "iraq",
            "syrian": "syria",
            "egyptian": "egypt",
            "turkish": "turkey",
            "german": "germany",
            "french": "france",
            "italian": "italy",
            "spanish": "spain",
            "japanese": "japan",
            "korean": "korea",
            "indian": "india",
            "pakistani": "pakistan",
            "bangladeshi": "bangladesh",
            "afghan": "afghanistan",
            "lebanese": "lebanon",
            "jordanian": "jordan",
            "saudi": "saudi arabia",
            "kuwaiti": "kuwait",
            "qatari": "qatar",
            "emirati": "united arab emirates",
        }
        return demonyms

    def _build_variant_map(self) -> Dict[str, str]:
        """Build variant -> canonical mapping from synonyms and persons."""
        variant_map = {}

        # Process synonyms section
        synonyms = self.config.get("synonyms", {})
        for canonical, variants in synonyms.items():
            canonical_norm = self._normalize_text_basic(canonical)
            variant_map[canonical_norm] = canonical_norm  # Self-map canonical

            for variant in variants:
                variant_norm = self._normalize_text_basic(variant)
                variant_map[variant_norm] = canonical_norm

        # Process persons section
        persons = self.config.get("persons", {})
        for canonical, variants in persons.items():
            canonical_norm = self._normalize_text_basic(canonical)
            variant_map[canonical_norm] = canonical_norm  # Self-map canonical

            for variant in variants:
                variant_norm = self._normalize_text_basic(variant)
                variant_map[variant_norm] = canonical_norm

        return variant_map

    def _build_concept_clusters(self) -> Dict[str, str]:
        """Build concept cluster mappings for overlap counting."""
        cluster_map = {}

        concept_clusters = self.config.get("concept_clusters", {})
        for cluster_name, members in concept_clusters.items():
            cluster_norm = self._normalize_text_basic(cluster_name)

            # Map cluster name to itself
            cluster_map[cluster_norm] = cluster_norm

            # Map all members to cluster name
            for member in members:
                member_norm = self._normalize_text_basic(member)
                cluster_map[member_norm] = cluster_norm

        return cluster_map

    def _normalize_text_basic(self, text: str) -> str:
        """Apply basic normalization rules."""
        if not text:
            return ""

        normalized = text.lower()

        # Strip dots (U.S. -> us)
        normalized = normalized.replace(".", "")

        # Remove punctuation except hyphens and slashes
        normalized = re.sub(r"[^\w\s/-]", "", normalized)

        # Collapse spaces
        normalized = re.sub(r"\s+", " ", normalized)

        # Handle hyphen-space variants (f-16 == f 16 == f16)
        normalized = re.sub(r"([a-zA-Z])[\s-]+(\d)", r"\1-\2", normalized)

        return normalized.strip()

    def normalize_token(self, text: str) -> str:
        """
        Main normalization function with all enhancements.

        Steps:
        1. Basic normalization (lowercase, dots, punctuation, spaces)
        2. Strip titles/honorifics
        3. Acronym expansion
        4. Demonym -> country conversion (standalone only)
        5. Synonym resolution
        """
        if not text:
            return ""

        # Step 1: Basic normalization
        normalized = self._normalize_text_basic(text)

        if not self._should_keep_keyword(normalized):
            return ""  # Filtered out

        # Step 2: Strip titles/honorifics
        normalized = self._strip_titles(normalized)

        # Step 3: Acronym expansion (word-by-word for phrases)
        words = normalized.split()
        expanded_words = []
        for word in words:
            if word in self.acronym_expansions:
                expanded_words.append(self.acronym_expansions[word])
            else:
                expanded_words.append(word)
        normalized = " ".join(expanded_words)

        # Step 4: Demonym -> country (standalone only)
        if normalized in self.demonym_countries:
            # Only convert if it's a standalone demonym, not a modifier
            if self._is_standalone_demonym(text, normalized):
                normalized = self.demonym_countries[normalized]

        # Step 5: Synonym resolution
        if normalized in self.variant_to_canonical:
            normalized = self.variant_to_canonical[normalized]

        return normalized

    def _strip_titles(self, text: str) -> str:
        """Remove titles and honorifics from text."""
        words = text.split()
        filtered_words = []

        # Handle multi-word titles like "prime minister"
        i = 0
        while i < len(words):
            word = words[i]

            # Check for multi-word titles
            if i < len(words) - 1:
                two_word_title = f"{word} {words[i+1]}"
                if two_word_title in self.titles_honorifics:
                    i += 2  # Skip both words
                    continue

            # Check single word title
            if word not in self.titles_honorifics:
                filtered_words.append(word)

            i += 1

        result = " ".join(filtered_words).strip()
        return result if result else text  # Return original if everything was stripped

    def _is_standalone_demonym(
        self, original_text: str, normalized_demonym: str
    ) -> bool:
        """
        Check if demonym appears standalone (not as modifier).

        Examples:
        - "russian" (standalone) -> russia ✓
        - "russian oil" (modifier) -> keep as "russian" ✗
        """
        # Simple heuristic: if original text is just the demonym, it's standalone
        orig_normalized = self._normalize_text_basic(original_text)
        return orig_normalized == normalized_demonym

    def _should_keep_keyword(self, text: str) -> bool:
        """Check if keyword should be kept based on filters."""
        # Always keep whitelisted phrases
        if text in self.phrase_whitelist:
            return True

        # Keep keeper regex patterns (codes like F-16, COP28, 9/11)
        for pattern in self.keeper_regex_patterns:
            if pattern.match(text):
                return True

        # Drop stop words
        if text in self.stop_words:
            return False

        # Drop stop phrases
        if text in self.stop_phrases:
            return False

        # Drop stop regex patterns
        for pattern in self.stop_regex_patterns:
            if pattern.search(text):
                return False

        return True

    def get_concept_cluster(self, canonical_text: str) -> str:
        """Get concept cluster name for canonical text (for overlap counting)."""
        normalized = self._normalize_text_basic(canonical_text)
        return self.concept_clusters.get(normalized, canonical_text)

    def batch_normalize(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """
        Batch normalize tokens.

        Returns:
            List of (original, canonical) tuples for non-filtered tokens
        """
        results = []
        for token in tokens:
            canonical = self.normalize_token(token)
            if canonical:  # Only include if not filtered out
                results.append((token, canonical))
        return results


# Global instance for reuse
_global_canonicalizer = None


def get_canonicalizer() -> AdvancedCanonicalizer:
    """Get or create global canonicalizer instance."""
    global _global_canonicalizer
    if _global_canonicalizer is None:
        _global_canonicalizer = AdvancedCanonicalizer()
    return _global_canonicalizer


def normalize_token(text: str) -> str:
    """Convenience function for single token normalization."""
    return get_canonicalizer().normalize_token(text)


if __name__ == "__main__":
    # Test the enhanced canonicalizer
    canonicalizer = AdvancedCanonicalizer()

    test_cases = [
        # Title stripping
        "President Trump",
        "Prime Minister Netanyahu",
        "Mr. Biden",
        "Chancellor Merkel",
        # Acronym expansion
        "U.S.",
        "USA",
        "UK",
        "EU",
        "PRC",
        # Demonym conversion
        "russian",  # standalone -> russia
        "russian oil",  # modifier -> keep as russian
        "israeli",  # standalone -> israel
        "chinese",  # standalone -> china
        # Combined cases
        "President Putin",
        "U.S. forces",
        # Existing functionality
        "F-16",
        "9/11",
        "negotiation",
    ]

    print("=== Enhanced Canonicalization Test ===")
    for text in test_cases:
        canonical = canonicalizer.normalize_token(text)
        cluster = canonicalizer.get_concept_cluster(canonical) if canonical else ""
        print(f"'{text}' -> '{canonical}' [cluster: {cluster}]")
