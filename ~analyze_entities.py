#!/usr/bin/env python3
"""
Analyze entities distribution in titles table
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text

from core.config import get_config


def analyze_entities():
    """Analyze unique entity combinations and their frequencies"""
    config = get_config()
    engine = create_engine(config.database_url)
    
    with engine.connect() as conn:
        # First, check basic counts
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_titles,
                COUNT(*) FILTER (WHERE entities IS NOT NULL) as titles_with_entities,
                COUNT(*) FILTER (WHERE gate_keep = true) as strategic_titles,
                COUNT(*) FILTER (WHERE gate_keep = true AND entities IS NOT NULL) as strategic_with_entities
            FROM titles
        """))
        
        stats = result.fetchone()
        print("=== ENTITY POPULATION OVERVIEW ===")
        print(f"Total titles: {stats.total_titles}")
        print(f"Titles with entities: {stats.titles_with_entities}")
        print(f"Strategic titles: {stats.strategic_titles}")
        print(f"Strategic with entities: {stats.strategic_with_entities}")
        print()
        
        # Get all unique entity combinations
        result = conn.execute(text("""
            SELECT entities, COUNT(*) as frequency
            FROM titles 
            WHERE entities IS NOT NULL
            GROUP BY entities
            ORDER BY frequency DESC
            LIMIT 50
        """))
        
        print("=== TOP 50 UNIQUE ENTITY COMBINATIONS ===")
        entity_combinations = []
        
        for row in result.fetchall():
            entities_json = row.entities
            frequency = row.frequency
            entity_combinations.append((entities_json, frequency))
            
            # Pretty print the entities
            entities_str = json.dumps(entities_json, indent=2) if entities_json else "{}"
            print(f"Frequency: {frequency}")
            print(f"Entities: {entities_str}")
            print("-" * 60)
        
        print("\n=== ENTITY TYPE ANALYSIS ===")
        
        # Analyze individual entity types
        entity_type_stats = defaultdict(Counter)
        all_entities = []
        
        result = conn.execute(text("""
            SELECT entities FROM titles WHERE entities IS NOT NULL
        """))
        
        for row in result.fetchall():
            entities = row.entities
            all_entities.append(entities)
            
            if isinstance(entities, dict):
                for entity_type, entity_list in entities.items():
                    if isinstance(entity_list, list):
                        for entity in entity_list:
                            entity_type_stats[entity_type][entity] += 1
        
        # Print top entities by type
        for entity_type, counter in entity_type_stats.items():
            print(f"\n--- {entity_type.upper()} (Top 20) ---")
            for entity, count in counter.most_common(20):
                print(f"  {entity}: {count}")
        
        # Summary statistics
        print("\n=== SUMMARY STATISTICS ===")
        print(f"Total unique entity combinations: {len(entity_combinations)}")
        
        for entity_type, counter in entity_type_stats.items():
            total_entities = sum(counter.values())
            unique_entities = len(counter)
            print(f"{entity_type}: {unique_entities} unique, {total_entities} total occurrences")
        
        return entity_combinations, entity_type_stats


if __name__ == "__main__":
    try:
        combinations, type_stats = analyze_entities()
        print(f"\nAnalysis complete. Found {len(combinations)} unique entity combinations.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)