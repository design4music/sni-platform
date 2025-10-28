"""
Phase 3.5a: Interpretive Seed Validation - Individual title validation before EF creation

Validates each title in a mechanical cluster individually using micro-prompts.
Only creates EF if cluster has >=MIN_CLUSTER_SIZE validated titles.
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

from loguru import logger

from core.config import get_config
from core.llm_client import get_llm_client


class SeedValidator:
    """
    Phase 3.5a: Validate mechanical seed clusters before EF creation

    Each title gets individual validation to prevent noise from entering EFs.
    """

    def __init__(self):
        self.config = get_config()
        self.llm_client = get_llm_client()
        self.MIN_CLUSTER_SIZE = self.config.p35a_min_cluster_size

    def validate_seed_cluster(
        self, seed_cluster: List[Dict], cluster_id: Optional[str] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate each title in mechanical cluster individually

        Args:
            seed_cluster: List of title dicts with 'text', 'id', 'entities'
            cluster_id: Optional cluster identifier for logging

        Returns:
            Tuple of (validated_titles, rejected_titles)
        """
        if not seed_cluster:
            return [], []

        # Single-title clusters go directly to recycling
        if len(seed_cluster) == 1:
            logger.debug(
                f"Single-title cluster {cluster_id or 'unknown'} - sending to recycling"
            )
            return [], seed_cluster

        # Generate brief theme from most frequent entities
        brief_theme = self._generate_brief_theme(seed_cluster)

        logger.info(
            f"Validating cluster {cluster_id or 'unknown'}: {len(seed_cluster)} titles, theme: '{brief_theme}'"
        )

        validated_titles = []
        rejected_titles = []

        # Validate each title individually
        for title in seed_cluster:
            is_valid = self._validate_title_against_theme(title["text"], brief_theme)

            if is_valid:
                validated_titles.append(title)
            else:
                rejected_titles.append(title)
                logger.debug(
                    f"REJECTED: '{title['text'][:60]}...' (doesn't fit theme '{brief_theme}')"
                )

        logger.info(
            f"Cluster validation complete: {len(validated_titles)} validated, "
            f"{len(rejected_titles)} rejected"
        )

        return validated_titles, rejected_titles

    def _generate_brief_theme(self, seed_cluster: List[Dict]) -> str:
        """
        Generate brief theme from top 3 most frequent entities in cluster

        Args:
            seed_cluster: List of title dicts with 'entities'

        Returns:
            Brief theme string (e.g., "Gaza + Israel + Hamas")
        """
        # Collect all entities from cluster
        all_entities = []
        for title in seed_cluster:
            entities = title.get("entities") or title.get("extracted_actors") or []

            # Handle both list and dict formats
            if isinstance(entities, list):
                all_entities.extend(entities)
            elif isinstance(entities, dict):
                actors_list = entities.get("actors", [])
                all_entities.extend(actors_list)

        if not all_entities:
            return "unknown topic"

        # Get top 3 most frequent entities
        entity_counts = Counter(all_entities)
        top_entities = [entity for entity, _ in entity_counts.most_common(3)]

        if not top_entities:
            return "unknown topic"

        brief_theme = " + ".join(top_entities)
        return brief_theme

    def _validate_title_against_theme(self, title_text: str, brief_theme: str) -> bool:
        """
        Micro-prompt: Does this title belong to the cluster theme?

        Args:
            title_text: Headline text
            brief_theme: Brief theme description from entities

        Returns:
            True if title fits theme, False otherwise
        """
        from core.llm_client import build_seed_validation_prompt

        system_prompt, user_prompt = build_seed_validation_prompt(
            title_text, brief_theme
        )

        try:
            response = self.llm_client._call_llm_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.p35a_validation_max_tokens,
                temperature=self.config.p35a_validation_temperature,
            )

            answer = response.strip().upper()
            return "YES" in answer

        except Exception as e:
            logger.error(f"Seed validation micro-prompt failed: {e}")
            # On error, include title (fail open to avoid losing data)
            return True

    def should_create_ef(self, validated_titles: List[Dict]) -> bool:
        """
        Determine if validated cluster is large enough to create EF

        Args:
            validated_titles: List of validated title dicts

        Returns:
            True if cluster meets minimum size requirement
        """
        return len(validated_titles) >= self.MIN_CLUSTER_SIZE


# Global validator instance
_seed_validator: Optional[SeedValidator] = None


def get_seed_validator() -> SeedValidator:
    """Get global seed validator instance"""
    global _seed_validator
    if _seed_validator is None:
        _seed_validator = SeedValidator()
    return _seed_validator


# CLI interface for testing
if __name__ == "__main__":
    # Test with sample cluster
    sample_cluster = [
        {
            "id": "test-1",
            "text": "Gaza ceasefire negotiations continue in Cairo",
            "entities": ["Gaza", "Israel", "Egypt"],
        },
        {
            "id": "test-2",
            "text": "Israel agrees to humanitarian pause in Gaza fighting",
            "entities": ["Israel", "Gaza", "Hamas"],
        },
        {
            "id": "test-3",
            "text": "Trump announces new trade tariffs on Chinese imports",
            "entities": ["United States", "China", "Trump"],
        },
    ]

    validator = SeedValidator()
    validated, rejected = validator.validate_seed_cluster(sample_cluster, "TEST")

    print("\n" + "=" * 60)
    print("SEED VALIDATION TEST RESULTS")
    print("=" * 60)
    print(f"Input titles: {len(sample_cluster)}")
    print(f"Validated: {len(validated)}")
    print(f"Rejected: {len(rejected)}")
    print(f"Should create EF: {validator.should_create_ef(validated)}")
    print("=" * 60)

    if rejected:
        print("\nRejected titles:")
        for title in rejected:
            print(f"  - {title['text']}")
