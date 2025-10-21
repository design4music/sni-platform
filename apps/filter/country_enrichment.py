"""
Country Enrichment for All Entity Types

Auto-adds country to titles.entities when ANY entity with iso_code is detected,
based on the iso_code field in data_entities table.

Examples:
- "Donald Trump" (PERSON) → iso_code="US" → add "United States"
- "Vladimir Putin" (PERSON) → iso_code="RU" → add "Russia"
- "FBI" (ORG) → iso_code="US" → add "United States"
- "Pentagon" (ORG) → iso_code="US" → add "United States"
- "Bundestag" (ORG) → iso_code="DE" → add "Germany"
"""

from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session


class CountryEnricher:
    """
    Enriches entity lists with inferred countries based on iso_codes.

    Works with ALL entity types (PERSON, ORG, Company, etc.) that have iso_code populated.
    Lazy-loads mapping on first use to avoid database overhead.
    """

    def __init__(self):
        self._entity_to_country: Optional[Dict[str, str]] = (
            None  # entity_id -> country_name
        )
        self._name_to_entity_id: Optional[Dict[str, str]] = None  # name_en -> entity_id
        self._entity_id_to_name: Optional[Dict[str, str]] = None  # entity_id -> name_en

    def _load_mappings(self) -> None:
        """
        Load all necessary mappings from data_entities table.

        Creates three mappings:
        1. entity_to_country: ANY entity_id with iso_code -> country name_en
        2. name_to_entity_id: entity name_en -> entity_id (reverse lookup)
        3. entity_id_to_name: entity_id -> name_en (for all entities)

        Works with ALL entity types (PERSON, ORG, Company, etc.)
        """
        if self._entity_to_country is not None:
            return  # Already loaded

        logger.info("Loading country enrichment mappings...")

        self._entity_to_country = {}
        self._name_to_entity_id = {}
        self._entity_id_to_name = {}

        with get_db_session() as session:
            # Load ALL entities with iso_code (not just PERSON)
            entities_with_country_query = """
            SELECT e.entity_id, e.name_en, e.entity_type, e.iso_code, c.name_en as country_name
            FROM data_entities e
            LEFT JOIN data_entities c ON e.iso_code = c.entity_id
            WHERE e.iso_code IS NOT NULL
            ORDER BY e.entity_id;
            """

            results = session.execute(text(entities_with_country_query)).fetchall()
            for row in results:
                entity_id = row.entity_id
                entity_name = row.name_en
                country_name = row.country_name

                if country_name:
                    # Map entity_id to country name
                    self._entity_to_country[entity_id] = country_name
                    # Map entity name to entity_id (for reverse lookup)
                    if entity_name:
                        self._name_to_entity_id[entity_name.lower()] = entity_id

            # Load ALL entities for name -> entity_id mapping
            all_entities_query = """
            SELECT entity_id, name_en
            FROM data_entities
            ORDER BY entity_id;
            """

            results = session.execute(text(all_entities_query)).fetchall()
            for row in results:
                entity_id = row.entity_id
                name_en = row.name_en

                if name_en:
                    # Store both directions
                    self._entity_id_to_name[entity_id] = name_en
                    # Prefer shorter entity_id for ambiguous names
                    name_lower = name_en.lower()
                    if name_lower not in self._name_to_entity_id or len(
                        entity_id
                    ) < len(self._name_to_entity_id[name_lower]):
                        self._name_to_entity_id[name_lower] = entity_id

        logger.info(
            f"Country enrichment loaded: {len(self._entity_to_country)} entities with countries, "
            f"{len(self._name_to_entity_id)} total entities in lookup"
        )

    def enrich_with_countries(self, entity_names: List[str]) -> List[str]:
        """
        Enrich entity list with inferred countries from ANY entity with iso_code.

        Args:
            entity_names: List of entity names (name_en format)

        Returns:
            Enriched list with countries added for detected entities

        Examples:
            Input:  ["Donald Trump", "NATO"]
            Output: ["Donald Trump", "NATO", "United States"]

            Input:  ["FBI", "MI6"]
            Output: ["FBI", "MI6", "United States", "United Kingdom"]
        """
        if not entity_names:
            return entity_names

        # Ensure mappings are loaded
        self._load_mappings()

        enriched = list(entity_names)  # Copy original list
        countries_to_add = []

        for entity_name in entity_names:
            entity_lower = entity_name.lower()

            # Look up entity_id from name
            entity_id = self._name_to_entity_id.get(entity_lower)
            if not entity_id:
                continue

            # Check if this entity has an associated country
            country_name = self._entity_to_country.get(entity_id)
            if country_name:
                # Only add if not already in the list (avoid duplicates)
                if (
                    country_name not in enriched
                    and country_name not in countries_to_add
                ):
                    countries_to_add.append(country_name)
                    logger.debug(
                        f"Auto-adding country '{country_name}' for entity '{entity_name}'"
                    )

        # Add countries at the end
        enriched.extend(countries_to_add)

        return enriched

    def get_country_for_entity(self, entity_name: str) -> Optional[str]:
        """
        Get the country name for a given entity name.

        Args:
            entity_name: Entity's name (name_en format)

        Returns:
            Country name if entity has iso_code, None otherwise
        """
        self._load_mappings()

        entity_lower = entity_name.lower()
        entity_id = self._name_to_entity_id.get(entity_lower)
        if not entity_id:
            return None

        return self._entity_to_country.get(entity_id)


# Global instance (lazy-loaded on first use)
_country_enricher: Optional[CountryEnricher] = None


def get_country_enricher() -> CountryEnricher:
    """Get or create global CountryEnricher instance"""
    global _country_enricher
    if _country_enricher is None:
        _country_enricher = CountryEnricher()
    return _country_enricher


def enrich_entities_with_countries(entity_names: List[str]) -> List[str]:
    """
    Convenience function to enrich entity list with countries.

    Args:
        entity_names: List of entity names (name_en format)

    Returns:
        Enriched list with countries added for ALL detected entities with iso_code
        (people, organizations, companies, etc.)
    """
    enricher = get_country_enricher()
    return enricher.enrich_with_countries(entity_names)
