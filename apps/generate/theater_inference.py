"""
Theater Inference Module - EF Generation v2 Phase 1

Determines primary theater from entity frequency analysis.
Supports:
- Single country dominance
- Bilateral theaters (US-China, Russia-Ukraine, Israel-Palestine)
- Regional groupings (if needed by LLM later)
- Global theater (tech, general news)
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

from loguru import logger

from apps.filter.country_enrichment import get_country_enricher


class TheaterInferenceEngine:
    """
    Infers theater(s) from entity list using frequency analysis and priority rules.
    """

    # Bilateral theater patterns (order matters for canonical naming)
    BILATERAL_PATTERNS = {
        # US relations
        ("United States", "China"): "US-China Relations",
        ("United States", "Russia"): "US-Russia Relations",
        ("United States", "Iran"): "US-Iran Relations",
        ("United States", "North Korea"): "US-North Korea Relations",
        # Regional conflicts
        ("Russia", "Ukraine"): "Russia-Ukraine Conflict",
        ("Israel", "State of Palestine"): "Israel-Palestine Conflict",
        ("India", "Pakistan"): "India-Pakistan Relations",
        ("India", "China"): "India-China Relations",
        # Other key bilateral relationships
        ("China", "Taiwan"): "China-Taiwan Relations",
        ("Saudi Arabia", "Iran"): "Saudi-Iran Relations",
    }

    # Countries to filter out (not primary theaters themselves)
    NON_THEATER_ENTITIES = {
        "NATO",  # Organization, not a theater
        "EU",  # Organization, not a theater
        "UN",  # Organization, not a theater
        "United Nations",
    }

    def __init__(self):
        self.country_enricher = get_country_enricher()

    def infer_theater(
        self, all_entities: List[str], event_type: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Infer primary theater from entity frequency analysis.

        Args:
            all_entities: All entities from titles in cluster (with duplicates)
            event_type: Event type (helps with Global vs specific theater)

        Returns:
            (theater_name, confidence_score)

        Logic:
        1. Filter for country entities only
        2. Count frequencies
        3. Check bilateral patterns (2 dominant countries)
        4. Check single dominance (>60%)
        5. Check tech/global indicators
        6. Fallback: Most frequent country
        """
        if not all_entities:
            return ("Global", 0.3)

        # 1. Filter for countries only, get frequencies
        country_freq = self._get_country_frequencies(all_entities)

        if not country_freq:
            # No countries detected → likely tech/general news
            if self._is_tech_or_global_event(all_entities, event_type):
                return ("Global", 0.7)
            return ("Global", 0.4)

        # 2. Get top countries
        top_countries = country_freq.most_common(3)
        total_count = sum(country_freq.values())

        # 3. Check for bilateral patterns (exactly 2 dominant countries)
        if len(top_countries) >= 2:
            country1, count1 = top_countries[0]
            country2, count2 = top_countries[1]

            # Both countries are significant (each >20% of mentions)
            pct1 = count1 / total_count
            pct2 = count2 / total_count

            if pct1 > 0.2 and pct2 > 0.2:
                bilateral_theater = self._check_bilateral_pattern(country1, country2)
                if bilateral_theater:
                    confidence = min(pct1 + pct2, 0.95)  # High confidence for bilateral
                    logger.debug(
                        f"Bilateral theater detected: {bilateral_theater} "
                        f"({country1}: {pct1:.1%}, {country2}: {pct2:.1%})"
                    )
                    return (bilateral_theater, confidence)

        # 4. Check single country dominance
        dominant_country, dominant_count = top_countries[0]
        dominance_pct = dominant_count / total_count

        if dominance_pct > 0.6:
            # Clear single country dominance
            logger.debug(
                f"Single country dominance: {dominant_country} ({dominance_pct:.1%})"
            )
            return (dominant_country, dominance_pct)

        # 5. Check if this is tech/global despite having countries
        if self._is_tech_or_global_event(all_entities, event_type):
            logger.debug("Tech/global event detected despite country mentions")
            return ("Global", 0.6)

        # 6. Fallback: Most frequent country (lower confidence)
        logger.debug(
            f"Fallback to most frequent: {dominant_country} ({dominance_pct:.1%})"
        )
        return (dominant_country, dominance_pct * 0.8)  # Reduce confidence for fallback

    def _get_country_frequencies(self, entities: List[str]) -> Counter:
        """
        Filter for country entities and count frequencies.

        Returns:
            Counter of country names → frequency
        """
        country_freq = Counter()

        for entity in entities:
            entity_lower = entity.lower().strip()

            # Skip non-theater entities
            if entity in self.NON_THEATER_ENTITIES:
                continue

            # Check if this is a country
            # Option 1: Check against data_entities for entity_type=COUNTRY
            # Option 2: Heuristic - if enricher knows about it as a country
            # For now, simple approach: if it appears in our bilateral patterns or looks like a country
            if self._is_country_entity(entity):
                country_freq[entity] += 1

        return country_freq

    def _is_country_entity(self, entity: str) -> bool:
        """
        Check if entity is a country.

        Simple heuristic for now - can be enhanced with data_entities query.
        """
        # Known countries from bilateral patterns
        known_countries = set()
        for (c1, c2), _ in self.BILATERAL_PATTERNS.items():
            known_countries.add(c1)
            known_countries.add(c2)

        if entity in known_countries:
            return True

        # Additional common countries
        common_countries = {
            "United States",
            "China",
            "Russia",
            "India",
            "United Kingdom",
            "France",
            "Germany",
            "Japan",
            "South Korea",
            "Australia",
            "Canada",
            "Brazil",
            "Mexico",
            "Italy",
            "Spain",
            "Turkey",
            "Saudi Arabia",
            "Egypt",
            "South Africa",
            "Nigeria",
            "Kenya",
            "Indonesia",
            "Thailand",
            "Vietnam",
            "Philippines",
            "Poland",
            "Ukraine",
            "Iran",
            "Iraq",
            "Syria",
            "Afghanistan",
            "Israel",
            "State of Palestine",
            "Lebanon",
            "Jordan",
            "UAE",
            "Qatar",
        }

        return entity in common_countries

    def _check_bilateral_pattern(self, country1: str, country2: str) -> Optional[str]:
        """
        Check if two countries match a known bilateral pattern.

        Returns canonical theater name or None.
        """
        # Check both orders
        pattern_key = (country1, country2)
        if pattern_key in self.BILATERAL_PATTERNS:
            return self.BILATERAL_PATTERNS[pattern_key]

        pattern_key_rev = (country2, country1)
        if pattern_key_rev in self.BILATERAL_PATTERNS:
            return self.BILATERAL_PATTERNS[pattern_key_rev]

        return None

    def _is_tech_or_global_event(
        self, entities: List[str], event_type: Optional[str]
    ) -> bool:
        """
        Determine if this is a tech/global event (not country-specific).

        Indicators:
        - Tech companies mentioned (Meta, Google, Apple, etc.)
        - Event type is Technology
        - Global organizations (UN, WHO) without specific country context
        """
        tech_indicators = {
            "Meta",
            "Facebook",
            "Google",
            "Apple",
            "Microsoft",
            "Amazon",
            "Tesla",
            "SpaceX",
            "TikTok",
            "ByteDance",
            "Alibaba",
            "Tencent",
            "OpenAI",
            "Anthropic",
            "DeepMind",
            "Nvidia",
            "AMD",
            "Intel",
        }

        # Check for tech companies
        for entity in entities:
            if entity in tech_indicators:
                return True

        # Check event type
        if event_type and "Technology" in event_type:
            return True

        return False


def infer_theater_from_entities(
    entities: List[str], event_type: Optional[str] = None
) -> Tuple[str, float]:
    """
    Convenience function to infer theater from entity list.

    Args:
        entities: List of entity names (name_en format, with duplicates)
        event_type: Optional event type for context

    Returns:
        (theater_name, confidence_score)

    Examples:
        ["Russia", "Russia", "Ukraine"] → ("Russia-Ukraine Conflict", 0.85)
        ["United States", "China", "China"] → ("US-China Relations", 0.80)
        ["France", "France", "Germany"] → ("France", 0.67)
        ["Meta", "Google", "AI"] → ("Global", 0.70)
    """
    engine = TheaterInferenceEngine()
    return engine.infer_theater(entities, event_type)


# For testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Bilateral: Russia-Ukraine
        (["Russia", "Russia", "Ukraine", "NATO"], None, "Russia-Ukraine Conflict"),
        # Bilateral: US-China
        (["United States", "China", "China", "Taiwan"], None, "US-China Relations"),
        # Bilateral: Israel-Palestine
        (
            ["Israel", "State of Palestine", "Israel", "Gaza"],
            None,
            "Israel-Palestine Conflict",
        ),
        # Single dominance: Russia
        (["Russia", "Russia", "Russia", "France"], None, "Russia"),
        # Tech/Global
        (["Meta", "Google", "Apple"], "Technology", "Global"),
        # Mixed with clear dominant
        (
            ["United States", "United States", "United States", "Canada"],
            None,
            "United States",
        ),
    ]

    for entities, event_type, expected in test_cases:
        theater, confidence = infer_theater_from_entities(entities, event_type)
        status = "✓" if theater == expected else "✗"
        print(
            f"{status} {entities[:3]}... → {theater} ({confidence:.0%}) [expected: {expected}]"
        )
