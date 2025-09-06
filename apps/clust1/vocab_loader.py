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
    labels: List[str]                           # mechanism codes (e.g., "sanctions")
    centroids_texts: Dict[str, List[str]]       # code -> list of anchor phrases
    metadata: Dict[str, Dict[str, any]]         # code -> {label, guarded, scope_note}


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
    aliases: Dict[str, List[str]] = {}
    
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row["entity_id"]
            bag = []
            
            # Collect aliases from all language columns
            for col in ["aliases_en", "aliases_es", "aliases_fr", "aliases_ru", "aliases_zh"]:
                if row.get(col):
                    # Split on semicolon and clean up
                    lang_aliases = [a.strip() for a in row[col].split(";") if a.strip()]
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
                "scope_note": spec.get("scope_note", "")
            }
    
    return MechanismAnchors(
        labels=labels,
        centroids_texts=centroids,
        metadata=metadata
    )


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
        "mechanisms_file_exists": False,
        "actors_count": 0,
        "mechanisms_count": 0,
        "total_actor_aliases": 0,
        "total_anchor_phrases": 0,
        "errors": []
    }
    
    # Check actors file
    try:
        aliases = load_actor_aliases()
        results["actors_file_exists"] = True
        results["actors_count"] = len(aliases)
        results["total_actor_aliases"] = sum(len(alias_list) for alias_list in aliases.values())
    except Exception as e:
        results["errors"].append(f"Actor loading error: {e}")
    
    # Check mechanisms file
    try:
        anchors = load_mechanism_anchors()
        results["mechanisms_file_exists"] = True
        results["mechanisms_count"] = len(anchors.labels)
        results["total_anchor_phrases"] = sum(len(phrases) for phrases in anchors.centroids_texts.values())
    except Exception as e:
        results["errors"].append(f"Mechanism loading error: {e}")
    
    return results


if __name__ == "__main__":
    # Quick validation when run directly
    print("Strategic Gate Vocabulary Validation")
    print("=" * 40)
    
    validation = validate_vocabularies()
    
    print(f"Actors file exists: {validation['actors_file_exists']}")
    print(f"Mechanisms file exists: {validation['mechanisms_file_exists']}")
    print(f"Actor entities: {validation['actors_count']}")
    print(f"Total actor aliases: {validation['total_actor_aliases']}")
    print(f"Mechanism types: {validation['mechanisms_count']}")
    print(f"Total anchor phrases: {validation['total_anchor_phrases']}")
    
    if validation["errors"]:
        print("\nErrors:")
        for error in validation["errors"]:
            print(f"  - {error}")
    else:
        print("\nAll vocabulary files loaded successfully!")