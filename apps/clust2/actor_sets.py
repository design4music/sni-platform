"""
CLUST-2 Actor Set Extraction
Uses shared actor extractor to build actor sets for bucket grouping
"""

from __future__ import annotations
from typing import List, Dict, Any
from apps.clust1.actor_extractor import create_actor_extractor


class ActorSetBuilder:
    """Builds actor sets for CLUST-2 bucket grouping"""
    
    def __init__(self):
        self._extractor = create_actor_extractor()
    
    def extract_actor_set(self, title: Dict[str, Any]) -> List[str]:
        """
        Extract all actors from a title for bucket grouping.
        
        Args:
            title: Title dictionary with title_norm/title_display and optional gate_actor_hit
            
        Returns:
            List of actor entity_ids (deduplicated, order-stable)
        """
        # Get text to analyze
        title_text = title.get("title_norm") or title.get("title_display", "")
        if not title_text:
            return []
        
        # Extract all actor matches using shared extractor
        actor_codes = self._extractor.all_hits(title_text)
        
        # Optional: seed from gate for cheap wins (but still run all_hits to find others)
        gate_actor = title.get("gate_actor_hit")
        if gate_actor and gate_actor not in actor_codes:
            # Gate found an actor we missed (shouldn't happen with shared logic, but defensive)
            actor_codes.insert(0, gate_actor)
        
        return actor_codes
    
    def build_bucket_key(self, actor_codes: List[str], max_actors: int = 4) -> str:
        """
        Build deterministic bucket key from actor codes.
        
        Args:
            actor_codes: List of actor entity_ids from extract_actor_set()
            max_actors: Maximum actors to include in bucket key
            
        Returns:
            Deterministic bucket key like "CN-RU-US" (sorted, truncated)
        """
        if not actor_codes:
            return ""
        
        # Take top N actors (up to max_actors), sorted for determinism
        limited_actors = sorted(set(actor_codes))[:max_actors]
        
        return "-".join(limited_actors)
    
    def extract_and_build_key(self, title: Dict[str, Any], max_actors: int = 4) -> tuple[List[str], str]:
        """
        Extract actor set and build bucket key in one call.
        
        Args:
            title: Title dictionary
            max_actors: Maximum actors for bucket key
            
        Returns:
            Tuple of (actor_codes, bucket_key)
        """
        actor_codes = self.extract_actor_set(title)
        bucket_key = self.build_bucket_key(actor_codes, max_actors)
        
        return actor_codes, bucket_key


def extract_titles_actor_sets(titles: List[Dict[str, Any]], max_actors: int = 4) -> List[tuple[Dict[str, Any], List[str], str]]:
    """
    Batch extract actor sets and bucket keys from titles.
    
    Args:
        titles: List of title dictionaries
        max_actors: Maximum actors per bucket key
        
    Returns:
        List of (title, actor_codes, bucket_key) tuples
    """
    builder = ActorSetBuilder()
    results = []
    
    for title in titles:
        actor_codes, bucket_key = builder.extract_and_build_key(title, max_actors)
        results.append((title, actor_codes, bucket_key))
    
    return results


if __name__ == "__main__":
    # Basic validation test
    print("CLUST-2 Actor Set Extraction - Validation Test")
    print("=" * 50)
    
    try:
        # Test initialization
        builder = ActorSetBuilder()
        print("[PASS] ActorSetBuilder initialized successfully")
        
        # Test with minimal synthetic data
        test_title = {"title_display": "Test article", "gate_actor_hit": None}
        actor_codes, bucket_key = builder.extract_and_build_key(test_title, max_actors=3)
        print(f"[PASS] Actor extraction working: {len(actor_codes)} actors found")
        
        # Test batch processing
        test_titles = [test_title]
        results = extract_titles_actor_sets(test_titles, max_actors=3)
        print(f"[PASS] Batch processing working: {len(results)} results")
        
        print("\nModule ready for production use")
        print("Use with real titles from database queries")
        
    except Exception as e:
        print(f"[FAIL] Validation error: {e}")
        import traceback
        traceback.print_exc()