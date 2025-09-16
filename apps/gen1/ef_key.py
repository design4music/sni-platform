"""
EF Key System - Deterministic Event Family Keys
Provides functions for generating and managing ef_key values for continuous merging
"""

import hashlib
from typing import List, Dict, Any, Optional
from loguru import logger


def normalize_actors(actors: List[str]) -> List[str]:
    """
    Normalize actor names for consistent ef_key generation
    
    Args:
        actors: List of actor names
        
    Returns:
        List of normalized, deduplicated, sorted actor names
    """
    if not actors:
        return []
    
    # Normalize and deduplicate
    normalized = []
    seen = set()
    
    for actor in actors:
        # Strip whitespace and normalize case for comparison
        clean_actor = actor.strip()
        if not clean_actor:
            continue
            
        # Use original case for final output but lowercase for dedup check
        lower_actor = clean_actor.lower()
        if lower_actor not in seen:
            normalized.append(clean_actor)
            seen.add(lower_actor)
    
    # Sort for deterministic ordering
    return sorted(normalized)


def generate_ef_key(actors: List[str], primary_theater: str, event_type: str) -> str:
    """
    Generate deterministic ef_key for Event Family using 2-Parameter Matching
    
    CRITICAL CHANGE: Only uses theater + event_type to prevent fragmentation.
    Actors can be diverse within the same EF.
    
    Args:
        actors: List of actor names (IGNORED for ef_key generation)
        primary_theater: Theater code (e.g., "UKRAINE", "GAZA")  
        event_type: Event type (e.g., "Strategy/Tactics", "Diplomacy/Negotiations")
        
    Returns:
        16-character hexadecimal ef_key hash
        
    Example:
        theater = "UKRAINE"
        event_type = "Strategy/Tactics"
        -> ef_key = "ukraine_strategy" (regardless of actors)
    """
    # Build key string: theater|event_type (actors ignored!)
    key_parts = [
        primary_theater.strip(),
        event_type.strip()
    ]
    key_string = "|".join(key_parts)
    
    # Generate SHA-256 hash and take first 16 characters
    hash_object = hashlib.sha256(key_string.encode('utf-8'))
    ef_key = hash_object.hexdigest()[:16]
    
    logger.debug(f"Generated ef_key: {ef_key} from key_string: {key_string} (actors ignored)")
    return ef_key


def parse_ef_key_components(ef_data: Dict[str, Any]) -> tuple[List[str], str, str]:
    """
    Extract ef_key components from Event Family data
    
    Args:
        ef_data: Event Family data dictionary
        
    Returns:
        Tuple of (actors, primary_theater, event_type)
    """
    actors = ef_data.get('key_actors', [])
    if isinstance(actors, str):
        # Handle single actor as string
        actors = [actors]
    
    primary_theater = ef_data.get('primary_theater', ef_data.get('geography', ''))
    event_type = ef_data.get('event_type', '')
    
    return actors, primary_theater, event_type


def generate_ef_key_from_data(ef_data: Dict[str, Any]) -> str:
    """
    Generate ef_key from Event Family data dictionary
    
    Args:
        ef_data: Event Family data with keys: key_actors, primary_theater, event_type
        
    Returns:
        Generated ef_key
    """
    actors, primary_theater, event_type = parse_ef_key_components(ef_data)
    return generate_ef_key(actors, primary_theater, event_type)


def validate_ef_key_components(actors: List[str], primary_theater: str, event_type: str) -> bool:
    """
    Validate that ef_key components are valid
    
    Args:
        actors: List of actors
        primary_theater: Theater code
        event_type: Event type
        
    Returns:
        True if components are valid for ef_key generation
    """
    # Must have at least one actor
    if not actors or not any(actor.strip() for actor in actors):
        logger.warning("ef_key validation failed: No valid actors provided")
        return False
    
    # Must have theater
    if not primary_theater or not primary_theater.strip():
        logger.warning("ef_key validation failed: No primary_theater provided")
        return False
    
    # Must have event type
    if not event_type or not event_type.strip():
        logger.warning("ef_key validation failed: No event_type provided")
        return False
    
    return True


def actors_similarity(actors1: List[str], actors2: List[str]) -> float:
    """
    Calculate Jaccard similarity between two actor sets
    
    Args:
        actors1: First actor list
        actors2: Second actor list
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not actors1 and not actors2:
        return 1.0
    
    if not actors1 or not actors2:
        return 0.0
    
    # Normalize both sets
    set1 = set(actor.lower().strip() for actor in actors1)
    set2 = set(actor.lower().strip() for actor in actors2)
    
    # Remove empty strings
    set1.discard('')
    set2.discard('')
    
    if not set1 and not set2:
        return 1.0
    
    if not set1 or not set2:
        return 0.0
    
    # Jaccard similarity: intersection / union
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def should_consider_for_merge(ef1_data: Dict[str, Any], ef2_data: Dict[str, Any]) -> bool:
    """
    Check if two Event Families should be considered for LLM merge evaluation
    Based on matching theater + event_type but different actors
    
    Args:
        ef1_data: First Event Family data
        ef2_data: Second Event Family data
        
    Returns:
        True if they should be considered for merge by LLM
    """
    actors1, theater1, type1 = parse_ef_key_components(ef1_data)
    actors2, theater2, type2 = parse_ef_key_components(ef2_data)
    
    # Must have same theater and event type
    if theater1.strip() != theater2.strip():
        return False
    
    if type1.strip() != type2.strip():
        return False
    
    # Must have different actors (otherwise they'd have same ef_key)
    if generate_ef_key(actors1, theater1, type1) == generate_ef_key(actors2, theater2, type2):
        return False
    
    return True


# Test functions
def test_ef_key_generation():
    """Test ef_key generation with various scenarios"""
    logger.info("=== Testing EF Key Generation ===")
    
    # Test case 1: Basic generation
    actors = ["Russia", "Ukraine"]
    theater = "UKRAINE"
    event_type = "Strategy/Tactics"
    key1 = generate_ef_key(actors, theater, event_type)
    logger.info(f"Test 1: {actors} + {theater} + {event_type} -> {key1}")
    
    # Test case 2: Same input should generate same key
    key2 = generate_ef_key(actors, theater, event_type)
    assert key1 == key2, "Same input should generate same key"
    logger.info(f"Test 2: Deterministic ✓ {key1 == key2}")
    
    # Test case 3: Different order of actors should generate same key
    actors_reversed = ["Ukraine", "Russia"]
    key3 = generate_ef_key(actors_reversed, theater, event_type)
    assert key1 == key3, "Actor order should not affect key"
    logger.info(f"Test 3: Order independence ✓ {key1 == key3}")
    
    # Test case 4: Different actors should generate different key
    actors_different = ["Russia", "Ukraine", "NATO"]
    key4 = generate_ef_key(actors_different, theater, event_type)
    assert key1 != key4, "Different actors should generate different key"
    logger.info(f"Test 4: Different actors -> different keys ✓ {key1 != key4}")
    
    # Test case 5: Actor similarity calculation
    similarity = actors_similarity(actors, actors_different)
    logger.info(f"Test 5: Actor similarity {actors} vs {actors_different} = {similarity:.2f}")
    
    logger.info("✅ All EF key tests passed!")


if __name__ == "__main__":
    test_ef_key_generation()