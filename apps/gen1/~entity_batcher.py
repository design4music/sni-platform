#!/usr/bin/env python3
"""
Simple Entity-Based Batching for GEN-1
Purely mechanical grouping based on entity combinations - no hardcoded rules
"""

from collections import defaultdict
from typing import Any, Dict, List

from loguru import logger


def group_titles_by_entities(titles: List[Dict[str, Any]], target_batch_size: int = 50) -> List[Dict[str, Any]]:
    """
    Group strategic titles by exact entity combinations for coherent LLM batching
    
    Purely mechanical approach:
    - Same entity combination = same batch
    - No hardcoded rules or special cases
    - Scalable to any future entity combinations
    
    Args:
        titles: List of title dictionaries with 'entities' field
        target_batch_size: Target batch size for LLM processing
        
    Returns:
        List of batch dictionaries with 'titles', 'entity_key', and 'entity_context'
    """
    logger.info(f"Grouping {len(titles)} strategic titles by entity combinations (target: {target_batch_size})")
    
    # Group by exact entity combination
    entity_groups = defaultdict(list)
    
    for title in titles:
        entities = title.get('entities')
        
        # Create deterministic key from entity combination
        entity_key = create_entity_key(entities)
        entity_groups[entity_key].append(title)
    
    logger.info(f"Created {len(entity_groups)} unique entity combinations")
    
    # Log top combinations
    sorted_groups = sorted(entity_groups.items(), key=lambda x: len(x[1]), reverse=True)
    for entity_key, group in sorted_groups[:10]:
        logger.info(f"  {entity_key}: {len(group)} titles")
    
    # Convert groups to batches, splitting large groups
    batches = []
    
    for entity_key, titles_group in entity_groups.items():
        if len(titles_group) <= target_batch_size:
            # Group fits in one batch
            batches.append({
                'titles': titles_group,
                'entity_key': entity_key,
                'entity_context': extract_entity_context(titles_group),
                'size': len(titles_group)
            })
        else:
            # Split large group into multiple batches
            batch_count = 0
            for i in range(0, len(titles_group), target_batch_size):
                batch_count += 1
                batch_titles = titles_group[i:i + target_batch_size]
                
                batches.append({
                    'titles': batch_titles,
                    'entity_key': f"{entity_key}__batch_{batch_count}",
                    'entity_context': extract_entity_context(batch_titles),
                    'size': len(batch_titles)
                })
                
                logger.info(f"Split large group '{entity_key}': batch {batch_count} with {len(batch_titles)} titles")
    
    logger.info(f"Final result: {len(batches)} entity-coherent batches")
    
    # Sort batches by size (largest first for efficient processing)
    batches.sort(key=lambda x: x['size'], reverse=True)
    
    return batches


def create_entity_key(entities: Any) -> str:
    """
    Create deterministic key from entity combination
    
    Args:
        entities: Entity data from titles.entities column
        
    Returns:
        Deterministic string key for grouping
    """
    if not entities or not isinstance(entities, dict):
        return "no_entities"
    
    # Extract actors list (main grouping criterion based on our analysis)
    actors = entities.get('actors', [])
    
    if not actors:
        return "no_actors"
    
    # Sort actors for deterministic key
    sorted_actors = sorted(actors)
    
    # Create key from sorted actor list
    if len(sorted_actors) == 1:
        return f"single__{sorted_actors[0]}"
    else:
        return f"multi__{'+'.join(sorted_actors)}"


def extract_entity_context(titles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract entity context summary for a batch
    
    Args:
        titles: List of titles in the batch
        
    Returns:
        Context dictionary with entity statistics
    """
    from collections import Counter
    
    all_actors = []
    strategic_count = 0
    
    for title in titles:
        entities = title.get('entities', {})
        if isinstance(entities, dict):
            actors = entities.get('actors', [])
            all_actors.extend(actors)
            
            # Count strategic titles
            if entities.get('is_strategic', False):
                strategic_count += 1
    
    actor_counts = Counter(all_actors)
    
    return {
        'total_titles': len(titles),
        'strategic_titles': strategic_count,
        'unique_actors': len(actor_counts),
        'top_actors': [actor for actor, _ in actor_counts.most_common(5)],
        'actor_distribution': dict(actor_counts.most_common(10)),
        'dominant_actor': actor_counts.most_common(1)[0][0] if actor_counts else None,
        'multi_actor_titles': len([t for t in titles 
                                  if isinstance(t.get('entities', {}), dict) 
                                  and len(t.get('entities', {}).get('actors', [])) > 1])
    }


def analyze_batch_distribution(batches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the distribution of batches for logging/debugging
    
    Args:
        batches: List of batch dictionaries
        
    Returns:
        Analysis summary
    """
    total_titles = sum(batch['size'] for batch in batches)
    batch_sizes = [batch['size'] for batch in batches]
    
    # Count entity types
    single_entity_batches = len([b for b in batches if b['entity_key'].startswith('single__')])
    multi_entity_batches = len([b for b in batches if b['entity_key'].startswith('multi__')])
    no_entity_batches = len([b for b in batches if 'no_' in b['entity_key']])
    
    return {
        'total_batches': len(batches),
        'total_titles': total_titles,
        'avg_batch_size': total_titles / len(batches) if batches else 0,
        'max_batch_size': max(batch_sizes) if batch_sizes else 0,
        'min_batch_size': min(batch_sizes) if batch_sizes else 0,
        'single_entity_batches': single_entity_batches,
        'multi_entity_batches': multi_entity_batches,
        'no_entity_batches': no_entity_batches,
        'largest_batches': sorted([
            (b['entity_key'], b['size']) for b in batches
        ], key=lambda x: x[1], reverse=True)[:5]
    }


if __name__ == "__main__":
    # Test with real database data
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from sqlalchemy import create_engine, text

    from core.config import get_config
    
    print("Entity Batcher - Testing with Real Data")
    
    try:
        config = get_config()
        engine = create_engine(config.database_url)
        
        with engine.connect() as conn:
            # Get strategic titles with entities (limit for testing)
            result = conn.execute(text("""
                SELECT 
                    id::text as id,
                    title_display,
                    entities
                FROM titles 
                WHERE gate_keep = true 
                  AND entities IS NOT NULL
                ORDER BY pubdate_utc DESC
                LIMIT 200
            """))
            
            titles = []
            for row in result.fetchall():
                titles.append({
                    'id': row.id,
                    'title_display': row.title_display,
                    'entities': row.entities
                })
            
            print(f"\nLoaded {len(titles)} strategic titles with entities")
            
            # Test batching
            batches = group_titles_by_entities(titles, target_batch_size=50)
            analysis = analyze_batch_distribution(batches)
            
            print(f"\n{'='*60}")
            print("REAL DATA BATCHING RESULTS")
            print('='*60)
            print(f"Total batches: {analysis['total_batches']}")
            print(f"Average batch size: {analysis['avg_batch_size']:.1f}")
            print(f"Size range: {analysis['min_batch_size']} - {analysis['max_batch_size']}")
            print(f"Single-entity batches: {analysis['single_entity_batches']}")
            print(f"Multi-entity batches: {analysis['multi_entity_batches']}")
            print(f"No-entity batches: {analysis['no_entity_batches']}")
            
            print("\nTOP 5 LARGEST BATCHES:")
            for entity_key, size in analysis['largest_batches']:
                display_key = entity_key.replace('single__', '').replace('multi__', 'multi:')
                print(f"  {display_key}: {size} titles")
                
            print("\nSAMPLE BATCH DETAILS:")
            for i, batch in enumerate(batches[:3]):
                context = batch['entity_context']
                print(f"Batch {i+1}: {batch['entity_key']} ({batch['size']} titles)")
                print(f"  Top actors: {context['top_actors'][:3]}")
                if batch['titles']:
                    sample = batch['titles'][0]['title_display'][:60] + "..."
                    print(f"  Sample: {sample}")
                
    except Exception as e:
        print(f"Database test failed: {e}")
        print("Falling back to mock data test...")
        
        # Fallback to mock data
        test_titles = [
            {'id': '1', 'entities': {'actors': ['CN'], 'is_strategic': True}},
            {'id': '2', 'entities': {'actors': ['CN'], 'is_strategic': True}},
            {'id': '3', 'entities': {'actors': ['CN', 'US'], 'is_strategic': True}},
            {'id': '4', 'entities': {'actors': ['RU', 'UA'], 'is_strategic': True}},
            {'id': '5', 'entities': None},
        ]
        
        batches = group_titles_by_entities(test_titles, target_batch_size=2)
        analysis = analyze_batch_distribution(batches)
        
        print(f"Mock test: Created {len(batches)} batches from {len(test_titles)} titles")