"""
Shared Actor Extractor
Single source of truth for actor detection used by both CLUST-1 (gate) and CLUST-2 (bucketing)
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Pattern, Tuple


class ActorExtractor:
    """Shared actor extraction logic with identical normalization and matching rules"""

    def __init__(self, aliases: Dict[str, List[str]]):
        """
        Initialize with actor aliases dictionary from vocab_loader.load_actor_aliases()

        Args:
            aliases: Dict mapping entity_id to list of aliases (e.g., {'US': ['United States', 'USA', ...]})
        """
        self._patterns: List[Tuple[str, Optional[Pattern], Optional[str], bool]] = []
        self._build_patterns(aliases)

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text using identical rules as title_norm processing

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text (NFKC, lowercase, collapsed whitespace)
        """
        if not text:
            return ""

        # NFKC Unicode normalization
        text = unicodedata.normalize("NFKC", text)

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

    def _build_patterns(self, aliases: Dict[str, List[str]]) -> None:
        """
        Precompile regex patterns for actor alias matching (identical to CLUST-1 logic)

        Args:
            aliases: Actor aliases dictionary
        """
        self._patterns = []

        for entity_id, alias_list in aliases.items():
            for alias in alias_list:
                alias_lower = alias.strip().lower()
                # Check if alias contains scripts that need substring matching
                has_substring_script = self._has_substring_script_chars(alias)

                if has_substring_script:
                    # For Chinese/Japanese/Thai only, use substring matching (no word boundaries)
                    self._patterns.append((entity_id, None, alias_lower, True))
                else:
                    # For Latin/Cyrillic (both single-word and multi-word), use strict word boundary regex
                    # This prevents "ROK" from matching "brokeback" and "EU" from matching "museum"
                    pattern = re.compile(
                        r"\b" + re.escape(alias_lower) + r"\b", re.IGNORECASE
                    )
                    self._patterns.append((entity_id, pattern, None, False))

    def first_hit(self, text: str) -> Optional[str]:
        """
        Find first actor match in text (used by CLUST-1 Strategic Gate)

        Args:
            text: Text to search for actors

        Returns:
            First matching entity_id or None if no match
        """
        normalized_text = self.normalize(text)
        if not normalized_text:
            return None

        for entity_id, pattern, alias, use_substring in self._patterns:
            if use_substring:
                # Substring check for CJK or single words
                if alias and alias in normalized_text:
                    return entity_id
            else:
                # Regex word boundary matching for Latin with spaces
                if pattern and pattern.search(normalized_text):
                    return entity_id

        return None

    def all_hits(self, text: str) -> List[str]:
        """
        Find all actor matches in text (used by CLUST-2 for actor sets)

        Args:
            text: Text to search for actors

        Returns:
            List of matching entity_ids (deduplicated, order-stable)
        """
        normalized_text = self.normalize(text)
        if not normalized_text:
            return []

        hits: List[str] = []
        seen = set()

        for entity_id, pattern, alias, use_substring in self._patterns:
            if entity_id in seen:
                continue

            matched = False
            if use_substring:
                # Substring check for CJK or single words
                if alias and alias in normalized_text:
                    matched = True
            else:
                # Regex word boundary matching for Latin with spaces
                if pattern and pattern.search(normalized_text):
                    matched = True

            if matched:
                seen.add(entity_id)
                hits.append(entity_id)

        return hits


def create_actor_extractor() -> ActorExtractor:
    """
    Factory function to create ActorExtractor with loaded aliases

    Returns:
        ActorExtractor instance initialized with current actor vocabulary
    """
    from apps.clust1.vocab_loader import load_actor_aliases
    from core.config import get_config

    config = get_config()
    aliases = load_actor_aliases(config.actors_csv_path)
    return ActorExtractor(aliases)
