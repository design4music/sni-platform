"""
Vocabulary Loader for Strategic Gate
Loads actor aliases and mechanism anchors from data files (not embedded in code)
"""

from __future__ import annotations

import csv
import json
import pathlib
from dataclasses import dataclass
from typing import Dict, List

DATA_DIR = pathlib.Path("data")


@dataclass
class MechanismAnchors:
    """Container for mechanism anchor phrases and metadata"""

    labels: List[str]  # mechanism codes (e.g., "sanctions")
    centroids_texts: Dict[str, List[str]]  # code -> list of anchor phrases
    metadata: Dict[str, Dict[str, any]]  # code -> {label, guarded, scope_note}


def load_actor_aliases(path: str | None = None) -> Dict[str, List[str]]:
    """
    Load actor aliases from CSV file.

    Args:
        path: Optional path to actors.csv, defaults to data/actors.csv

    Returns:
        Dict mapping entity_id to list of all aliases across languages

    Example:
        {'US': ['United States', 'USA', 'U.S.', 'Washington', 'Estados Unidos', ...]}
    """
    path = pathlib.Path(path) if path else (DATA_DIR / "actors.csv")
    return _load_csv_aliases(path)


def load_go_people_aliases(path: str | None = None) -> Dict[str, List[str]]:
    """
    Load people aliases from go_people.csv using same format as actors.csv.

    Args:
        path: Optional path to go_people.csv, defaults to data/go_people.csv

    Returns:
        Dict mapping entity_id to list of all aliases across languages

    Example:
        {'donald_trump': ['Donald Trump', 'President Trump', 'Trump', ...]}
    """
    path = pathlib.Path(path) if path else (DATA_DIR / "go_people.csv")
    return _load_csv_aliases(path)


def load_stop_culture_phrases(path: str | None = None) -> Dict[str, List[str]]:
    """
    Load culture/lifestyle stop phrases from stop_culture.csv using same format.

    Args:
        path: Optional path to stop_culture.csv, defaults to data/stop_culture.csv

    Returns:
        Dict mapping entity_id to list of all phrases across languages

    Example:
        {'culture_fashion': ['fashion', 'fashion week', 'designer', 'brand', ...]}
    """
    path = pathlib.Path(path) if path else (DATA_DIR / "stop_culture.csv")
    return _load_csv_aliases(path)


def load_go_taxonomy_aliases(path: str | None = None) -> Dict[str, List[str]]:
    """
    Load future go taxonomy aliases (when ready).

    Args:
        path: Optional path to go_taxonomy.csv, defaults to data/go_taxonomy.csv

    Returns:
        Dict mapping entity_id to list of aliases, empty dict if file doesn't exist
    """
    path = pathlib.Path(path) if path else (DATA_DIR / "go_taxonomy.csv")
    if not path.exists():
        return {}  # Future-proofing - return empty if not ready
    return _load_csv_aliases(path)


def _load_csv_aliases(path: pathlib.Path) -> Dict[str, List[str]]:
    """
    Shared CSV loading logic for all vocabulary files.

    Args:
        path: Path to CSV file

    Returns:
        Dict mapping entity_id to list of all aliases across languages
    """
    aliases: Dict[str, List[str]] = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row.get("entity_id")
            if not entity_id:
                continue  # Skip rows without entity_id

            bag = []

            # Collect aliases from all language columns (including German if present)
            alias_columns = [
                "aliases_en",
                "aliases_es",
                "aliases_fr",
                "aliases_ru",
                "aliases_zh",
                "aliases_de",
            ]
            for col in alias_columns:
                if row.get(col):
                    # Split on pipe and clean up
                    lang_aliases = [a.strip() for a in row[col].split("|") if a.strip()]
                    bag.extend(lang_aliases)

            # Deduplicate while preserving order, case-insensitive sort
            unique_aliases = []
            seen = set()
            for alias in bag:
                if alias.lower() not in seen:
                    unique_aliases.append(alias)
                    seen.add(alias.lower())

            aliases[entity_id] = sorted(unique_aliases, key=str.lower)

    return aliases


def load_mechanism_anchors(path: str | None = None) -> MechanismAnchors:
    """
    Load mechanism anchor phrases from JSON file.

    Args:
        path: Optional path to mechanisms.json, defaults to data/mechanisms.json

    Returns:
        MechanismAnchors with labels, anchor phrases, and metadata
    """
    path = pathlib.Path(path) if path else (DATA_DIR / "mechanisms.json")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    labels = []
    centroids = {}
    metadata = {}

    for code, spec in data.items():
        phrases = spec.get("anchors_en", [])
        if phrases:  # Only include mechanisms with anchor phrases
            labels.append(code)
            centroids[code] = phrases
            metadata[code] = {
                "label": spec.get("label", code),
                "guarded": spec.get("guarded", False),
                "scope_note": spec.get("scope_note", ""),
            }

    return MechanismAnchors(labels=labels, centroids_texts=centroids, metadata=metadata)


def get_actor_count() -> int:
    """Get total number of actors in the vocabulary"""
    try:
        aliases = load_actor_aliases()
        return len(aliases)
    except FileNotFoundError:
        return 0


def get_mechanism_count() -> int:
    """Get total number of mechanisms in the vocabulary"""
    try:
        anchors = load_mechanism_anchors()
        return len(anchors.labels)
    except FileNotFoundError:
        return 0


def validate_vocabularies() -> Dict[str, any]:
    """
    Validate that vocabulary files exist and are well-formed.

    Returns:
        Validation results dictionary
    """
    results = {
        "actors_file_exists": False,
        "go_people_file_exists": False,
        "stop_culture_file_exists": False,
        "actors_count": 0,
        "go_people_count": 0,
        "stop_culture_count": 0,
        "total_actor_aliases": 0,
        "total_go_people_aliases": 0,
        "total_stop_culture_phrases": 0,
        "errors": [],
    }

    # Check actors file
    try:
        aliases = load_actor_aliases()
        results["actors_file_exists"] = True
        results["actors_count"] = len(aliases)
        results["total_actor_aliases"] = sum(
            len(alias_list) for alias_list in aliases.values()
        )
    except Exception as e:
        results["errors"].append(f"Actor loading error: {e}")

    # Check go_people file
    try:
        people = load_go_people_aliases()
        results["go_people_file_exists"] = True
        results["go_people_count"] = len(people)
        results["total_go_people_aliases"] = sum(
            len(alias_list) for alias_list in people.values()
        )
    except Exception as e:
        results["errors"].append(f"Go people loading error: {e}")

    # Check stop_culture file
    try:
        culture = load_stop_culture_phrases()
        results["stop_culture_file_exists"] = True
        results["stop_culture_count"] = len(culture)
        results["total_stop_culture_phrases"] = sum(
            len(phrase_list) for phrase_list in culture.values()
        )
    except Exception as e:
        results["errors"].append(f"Stop culture loading error: {e}")

    return results


if __name__ == "__main__":
    # Quick validation when run directly
    print("Strategic Gate Vocabulary Validation")
    print("=" * 40)

    validation = validate_vocabularies()

    print(f"Actors file exists: {validation['actors_file_exists']}")
    print(f"Go people file exists: {validation['go_people_file_exists']}")
    print(f"Stop culture file exists: {validation['stop_culture_file_exists']}")
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
        print("\nAll vocabulary files loaded successfully!")
