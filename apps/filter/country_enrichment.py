"""
Country Enrichment for Person Entities

Auto-adds country to titles.entities when a PERSON entity is detected,
based on the iso_code field in data_entities table.

Example:
- "Donald Trump" detected → iso_code="US" → add "United States" to entities
- "Vladimir Putin" detected → iso_code="RU" → add "Russia" to entities
"""

from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session


class CountryEnricher:
    """
    Enriches entity lists with inferred countries based on person iso_codes.

    Lazy-loads mapping on first use to avoid database overhead.
    """

    def __init__(self):
        self._person_to_country: Optional[Dict[str, str]] = (
            None  # entity_id -> country_name
        )
        self._name_to_entity_id: Optional[Dict[str, str]] = None  # name_en -> entity_id
        self._entity_id_to_name: Optional[Dict[str, str]] = None  # entity_id -> name_en

    def _load_mappings(self) -> None:
        """
        Load all necessary mappings from data_entities table.

        Creates three mappings:
        1. person_to_country: PERSON entity_id -> country name_en
        2. name_to_entity_id: entity name_en -> entity_id (reverse lookup)
        3. entity_id_to_name: entity_id -> name_en (for all entities)
        """
        if self._person_to_country is not None:
            return  # Already loaded

        logger.info("Loading country enrichment mappings...")

        self._person_to_country = {}
        self._name_to_entity_id = {}
        self._entity_id_to_name = {}

        with get_db_session() as session:
            # Load PERSON entities with iso_code
            person_query = """
            SELECT p.entity_id, p.name_en, p.iso_code, c.name_en as country_name
            FROM data_entities p
            LEFT JOIN data_entities c ON p.iso_code = c.entity_id
            WHERE p.entity_type = 'PERSON' AND p.iso_code IS NOT NULL
            ORDER BY p.entity_id;
            """

            results = session.execute(text(person_query)).fetchall()
            for row in results:
                person_id = row.entity_id
                person_name = row.name_en
                country_name = row.country_name

                if country_name:
                    # Map person entity_id to country name
                    self._person_to_country[person_id] = country_name
                    # Map person name to entity_id (for reverse lookup)
                    if person_name:
                        self._name_to_entity_id[person_name.lower()] = person_id

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
            f"Country enrichment loaded: {len(self._person_to_country)} people with countries, "
            f"{len(self._name_to_entity_id)} total entities"
        )

    def enrich_with_countries(self, entity_names: List[str]) -> List[str]:
        """
        Enrich entity list with inferred countries from PERSON entities.

        Args:
            entity_names: List of entity names (name_en format)

        Returns:
            Enriched list with countries added for detected people

        Example:
            Input:  ["Donald Trump", "NATO"]
            Output: ["Donald Trump", "NATO", "United States"]
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

            # Check if this person has an associated country
            country_name = self._person_to_country.get(entity_id)
            if country_name:
                # Only add if not already in the list (avoid duplicates)
                if (
                    country_name not in enriched
                    and country_name not in countries_to_add
                ):
                    countries_to_add.append(country_name)
                    logger.debug(
                        f"Auto-adding country '{country_name}' for person '{entity_name}'"
                    )

        # Add countries at the end
        enriched.extend(countries_to_add)

        return enriched

    def get_country_for_person(self, person_name: str) -> Optional[str]:
        """
        Get the country name for a given person name.

        Args:
            person_name: Person's name (name_en format)

        Returns:
            Country name if person has iso_code, None otherwise
        """
        self._load_mappings()

        person_lower = person_name.lower()
        entity_id = self._name_to_entity_id.get(person_lower)
        if not entity_id:
            return None

        return self._person_to_country.get(entity_id)


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
        Enriched list with countries added for detected people
    """
    enricher = get_country_enricher()
    return enricher.enrich_with_countries(entity_names)
