#!/usr/bin/env python3
"""
Keyword Normalizer and Canonicalizer
Strategic Narrative Intelligence ETL Pipeline

Normalizes keywords and maps them to canonical forms using synonyms, persons,
and concept clusters from data/keyword_synonyms.yml.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger(__name__)


class KeywordNormalizer:
    """Normalizes and canonicalizes keywords using YAML configuration."""

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

        # Concept clusters for overlap counting
        self.concept_clusters = self._build_concept_clusters()

        logger.info(f"Loaded normalizer with {len(self.variant_to_canonical)} mappings")

    def _load_config(self) -> Dict:
        """Load YAML configuration file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}

    def _build_variant_map(self) -> Dict[str, str]:
        """Build variant -> canonical mapping from synonyms and persons."""
        variant_map = {}

        # Process synonyms section
        synonyms = self.config.get("synonyms", {})
        for canonical, variants in synonyms.items():
            canonical_norm = self._normalize_text(canonical)
            variant_map[canonical_norm] = canonical_norm  # Self-map canonical

            for variant in variants:
                variant_norm = self._normalize_text(variant)
                variant_map[variant_norm] = canonical_norm

        # Process persons section
        persons = self.config.get("persons", {})
        for canonical, variants in persons.items():
            canonical_norm = self._normalize_text(canonical)
            variant_map[canonical_norm] = canonical_norm  # Self-map canonical

            for variant in variants:
                variant_norm = self._normalize_text(variant)
                variant_map[variant_norm] = canonical_norm

        return variant_map

    def _build_concept_clusters(self) -> Dict[str, str]:
        """Build concept cluster mappings for overlap counting."""
        cluster_map = {}

        concept_clusters = self.config.get("concept_clusters", {})
        for cluster_name, members in concept_clusters.items():
            cluster_norm = self._normalize_text(cluster_name)

            # Map cluster name to itself
            cluster_map[cluster_norm] = cluster_norm

            # Map all members to cluster name
            for member in members:
                member_norm = self._normalize_text(member)
                cluster_map[member_norm] = cluster_norm

        return cluster_map

    def _normalize_text(self, text: str) -> str:
        """Apply normalization rules from config."""
        if not text:
            return ""

        normalized = text

        norm_config = self.config.get("normalization", {})

        if norm_config.get("lowercase", True):
            normalized = normalized.lower()

        if norm_config.get("strip_dots", True):
            normalized = normalized.replace(".", "")

        if norm_config.get("strip_punct_keep_hyphen", True):
            # Remove punctuation except hyphens, spaces, and slashes (for dates like 9/11)
            normalized = re.sub(r"[^\w\s/-]", "", normalized)

        if norm_config.get("collapse_spaces", True):
            normalized = re.sub(r"\s+", " ", normalized)

        normalized = normalized.strip()

        # Handle hyphen-space variants
        if norm_config.get("hyphen_space_variants", True):
            # Normalize "f-16", "f 16", "f16" to consistent form
            normalized = re.sub(r"([a-zA-Z])[\s-]+(\d)", r"\1-\2", normalized)

        return normalized

    def should_keep_keyword(self, text: str) -> bool:
        """Check if keyword should be kept based on filters."""
        normalized = self._normalize_text(text)

        # Always keep whitelisted phrases
        if normalized in self.phrase_whitelist:
            return True

        # Keep keeper regex patterns (codes like F-16, COP28, 9/11)
        for pattern in self.keeper_regex_patterns:
            if pattern.match(normalized):
                return True

        # Drop stop words
        if normalized in self.stop_words:
            return False

        # Drop stop phrases
        if normalized in self.stop_phrases:
            return False

        # Drop stop regex patterns
        for pattern in self.stop_regex_patterns:
            if pattern.search(normalized):
                return False

        return True

    def normalize_and_canonicalize(self, text: str) -> Tuple[str, str, float]:
        """
        Normalize text and return canonical form.

        Returns:
            Tuple of (normalized_text, canonical_text, confidence)
        """
        if not text:
            return "", "", 0.0

        normalized = self._normalize_text(text)

        if not self.should_keep_keyword(normalized):
            return normalized, "", 0.0  # Empty canonical means filtered out

        # Check for direct canonical mapping
        if normalized in self.variant_to_canonical:
            canonical = self.variant_to_canonical[normalized]
            return normalized, canonical, 1.0

        # No mapping found - return normalized form as canonical
        return normalized, normalized, 0.8

    def get_concept_cluster(self, canonical_text: str) -> str:
        """Get concept cluster name for canonical text (for overlap counting)."""
        normalized = self._normalize_text(canonical_text)
        return self.concept_clusters.get(normalized, canonical_text)

    def batch_normalize(self, keywords: List[str]) -> List[Tuple[str, str, str, float]]:
        """
        Batch normalize keywords.

        Returns:
            List of (original, normalized, canonical, confidence) tuples
        """
        results = []
        for keyword in keywords:
            normalized, canonical, confidence = self.normalize_and_canonicalize(keyword)
            if canonical:  # Only include if not filtered out
                results.append((keyword, normalized, canonical, confidence))
        return results


# Global instance for reuse
_global_normalizer = None


def get_normalizer() -> KeywordNormalizer:
    """Get or create global normalizer instance."""
    global _global_normalizer
    if _global_normalizer is None:
        _global_normalizer = KeywordNormalizer()
    return _global_normalizer


if __name__ == "__main__":
    # Test the normalizer
    normalizer = KeywordNormalizer()

    test_cases = [
        "U.S.",
        "united states",
        "President Trump",
        "F-16",
        "f 16",
        "COP28",
        "cop 28",
        "yesterday",
        "negotiation",
        "peace talks",
        "9/11",
    ]

    print("=== Keyword Normalization Test ===")
    for text in test_cases:
        norm, canon, conf = normalizer.normalize_and_canonicalize(text)
        cluster = normalizer.get_concept_cluster(canon) if canon else ""
        print(
            f"'{text}' -> '{norm}' -> '{canon}' (conf: {conf:.1f}) [cluster: {cluster}]"
        )
