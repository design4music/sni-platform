"""
Database-backed Vocabulary Loader for Strategic Gate
Loads entity aliases from data_entities table instead of CSV files

Migration from CSV-based vocab_loader.py to database-backed system
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

from sqlalchemy import text

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402


def load_actor_aliases() -> Dict[str, List[str]]:
    """
    Load actor aliases from data_entities table.

    Returns:
        Dict mapping entity_id to list of all aliases across languages

    Example:
        {'US': ['United States', 'USA', 'U.S.', 'Washington', 'Estados Unidos', ...]}
    """
    return _load_entities_by_type(["COUNTRY", "ORG", "CAPITAL"])


def load_go_people_aliases() -> Dict[str, List[str]]:
    """
    Load people aliases from data_entities table.

    Returns:
        Dict mapping entity_id to list of all aliases across languages

    Example:
        {'donald_trump': ['Donald Trump', 'President Trump', 'Trump', ...]}
    """
    return _load_entities_by_type(["PERSON"])


def load_stop_culture_phrases(path: str | None = None) -> Dict[str, List[str]]:
    """
    Load culture/lifestyle stop phrases from CSV (not migrated yet).
    Falls back to legacy CSV loader for now.

    Args:
        path: Optional path to stop_culture.csv

    Returns:
        Dict mapping entity_id to list of all phrases across languages
    """
    # Import legacy CSV loader for stop_culture (not in data_entities yet)
    from apps.filter.vocab_loader import \
        load_stop_culture_phrases as legacy_loader

    return legacy_loader(path)


def load_go_taxonomy_aliases(path: str | None = None) -> Dict[str, List[str]]:
    """
    Load future go taxonomy aliases (when ready).
    Currently returns empty dict as this vocabulary isn't defined yet.

    Returns:
        Empty dict (future-proofing)
    """
    return {}


def _is_usable_short_code(alias: str) -> bool:
    """
    Check if a short code/abbreviation is commonly used in news headlines.

    Whitelist of codes that ARE used in real news:
    - US, USA, UK, UAE - commonly used country abbreviations
    - UN, EU, NATO, WHO, IMF, WTO - commonly used organizations

    Also filters out ambiguous terms that could refer to multiple entities.

    Args:
        alias: The alias to check

    Returns:
        True if the code should be kept, False if it should be filtered out
    """
    # Whitelist of commonly-used codes in news headlines
    usable_codes = {
        # Countries
        "US",
        "USA",
        "U.S.",
        "U.S.A.",
        "UK",
        "U.K.",
        "UAE",
        "U.A.E.",
        # International Organizations
        "UN",
        "EU",
        "NATO",
        "WHO",
        "IMF",
        "WTO",
        "OECD",
        "OPEC",
        "BRICS",
        "ASEAN",
        "G7",
        "G20",
        "ICC",
        "WTO",
    }

    # Blacklist of ambiguous terms that should never be used as aliases
    # (e.g., "China" for Taiwan, "America" could mean US or continent)
    ambiguous_terms = {
        "China",  # Used for both PRC and Taiwan (ROC)
        "America",  # Could mean US or the continent
        "States",  # Too generic
    }

    # Check blacklist first
    if alias in ambiguous_terms:
        return False

    alias_upper = alias.upper().replace(" ", "")

    # If it's in the whitelist, keep it
    if alias_upper in usable_codes:
        return True

    # Filter out 2-3 letter all-uppercase codes (ISO codes like "AD", "AND", "ROC")
    if len(alias) <= 3 and alias.isupper() and alias.isalpha():
        return False

    # Filter out very short lowercase codes (like "ae" for UAE)
    if len(alias) <= 2 and alias.islower() and alias.isalpha():
        return False

    # Keep everything else
    return True


def _load_entities_by_type(entity_types: List[str]) -> Dict[str, List[str]]:
    """
    Load entities from data_entities table by entity_type(s).

    Args:
        entity_types: List of entity types to load (COUNTRY, PERSON, ORG, CAPITAL)

    Returns:
        Dict mapping entity_id to flattened list of all aliases across languages
    """
    aliases_dict: Dict[str, List[str]] = {}

    with get_db_session() as session:
        stmt = text(
            """
            SELECT entity_id, name_en, aliases
            FROM data_entities
            WHERE entity_type = ANY(:entity_types)
            ORDER BY entity_id
            """
        )

        result = session.execute(stmt, {"entity_types": entity_types})

        for row in result:
            entity_id = row.entity_id
            name_en = row.name_en
            aliases_json = row.aliases

            # Parse JSONB aliases: {"en": ["USA", "U.S."], "ru": ["США"], ...}
            aliases_data = (
                json.loads(aliases_json)
                if isinstance(aliases_json, str)
                else aliases_json
            )

            # Flatten all language aliases into a single list
            bag = []

            # Always include primary English name first
            if name_en:
                bag.append(name_en)

            # Add aliases from all languages (filter out problematic short codes)
            if isinstance(aliases_data, dict):
                for lang, lang_aliases in aliases_data.items():
                    if isinstance(lang_aliases, list):
                        # Filter out ISO codes and short codes that aren't commonly used
                        filtered_aliases = [
                            alias
                            for alias in lang_aliases
                            if _is_usable_short_code(alias)
                        ]
                        bag.extend(filtered_aliases)

            # Deduplicate while preserving order, case-insensitive
            # Keep name_en first (it was added first to bag)
            unique_aliases = []
            seen = set()
            for alias in bag:
                if alias and alias.lower() not in seen:
                    unique_aliases.append(alias)
                    seen.add(alias.lower())

            # Don't sort - preserve order with name_en first
            aliases_dict[entity_id] = unique_aliases

    return aliases_dict


def get_actor_count() -> int:
    """Get total number of actors in the database"""
    with get_db_session() as session:
        stmt = text(
            """
            SELECT COUNT(*)
            FROM data_entities
            WHERE entity_type IN ('COUNTRY', 'ORG', 'CAPITAL')
            """
        )
        result = session.execute(stmt).scalar()
        return result or 0


def get_person_count() -> int:
    """Get total number of people in the database"""
    with get_db_session() as session:
        stmt = text(
            """
            SELECT COUNT(*)
            FROM data_entities
            WHERE entity_type = 'PERSON'
            """
        )
        result = session.execute(stmt).scalar()
        return result or 0


def validate_vocabularies() -> Dict[str, any]:
    """
    Validate that data_entities table is populated and accessible.

    Returns:
        Validation results dictionary
    """
    results = {
        "db_accessible": False,
        "actors_count": 0,
        "go_people_count": 0,
        "stop_culture_count": 0,
        "total_actor_aliases": 0,
        "total_go_people_aliases": 0,
        "total_stop_culture_phrases": 0,
        "errors": [],
    }

    # Check database access and actor entities
    try:
        aliases = load_actor_aliases()
        results["db_accessible"] = True
        results["actors_count"] = len(aliases)
        results["total_actor_aliases"] = sum(
            len(alias_list) for alias_list in aliases.values()
        )
    except Exception as e:
        results["errors"].append(f"Actor loading error: {e}")

    # Check people entities
    try:
        people = load_go_people_aliases()
        results["go_people_count"] = len(people)
        results["total_go_people_aliases"] = sum(
            len(alias_list) for alias_list in people.values()
        )
    except Exception as e:
        results["errors"].append(f"Go people loading error: {e}")

    # Check stop_culture (still CSV-based)
    try:
        culture = load_stop_culture_phrases()
        results["stop_culture_count"] = len(culture)
        results["total_stop_culture_phrases"] = sum(
            len(phrase_list) for phrase_list in culture.values()
        )
    except Exception as e:
        results["errors"].append(f"Stop culture loading error: {e}")

    return results


if __name__ == "__main__":
    # Quick validation when run directly
    print("Database-backed Vocabulary Validation")
    print("=" * 40)

    validation = validate_vocabularies()

    print(f"Database accessible: {validation['db_accessible']}")
    print(f"Actor entities: {validation['actors_count']}")
    print(f"Go people entities: {validation['go_people_count']}")
    print(f"Stop culture entities: {validation['stop_culture_count']}")
    print(f"Total actor aliases: {validation['total_actor_aliases']}")
    print(f"Total go people aliases: {validation['total_go_people_aliases']}")
    print(f"Total stop culture phrases: {validation['total_stop_culture_phrases']}")

    if validation["errors"]:
        print("\nErrors:")
        for error in validation["errors"]:
            print(f"  - {error}")
    else:
        print("\nAll vocabularies loaded successfully from database!")

    # Show sample entities
    print("\n" + "=" * 40)
    print("Sample Actor Entities:")
    actors = load_actor_aliases()
    for entity_id in list(actors.keys())[:5]:
        print(f"  {entity_id}: {actors[entity_id][:3]}...")

    print("\nSample People Entities:")
    people = load_go_people_aliases()
    for entity_id in list(people.keys())[:5]:
        print(f"  {entity_id}: {people[entity_id][:3]}...")
