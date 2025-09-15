#!/usr/bin/env python3
"""
Analyze existing Event Families in detail
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from collections import Counter

from sqlalchemy import text

from core.database import get_db_session


def analyze_event_families():
    """Analyze existing Event Families"""
    with get_db_session() as session:
        # Get detailed Event Family information
        query = '''
        SELECT id, title, event_type, geography, confidence_score, 
               source_title_ids, key_actors, summary, coherence_reason,
               event_start, event_end, created_at
        FROM event_families 
        ORDER BY created_at DESC
        '''
        results = session.execute(text(query)).fetchall()
        
        print(f"=== DETAILED ANALYSIS OF {len(results)} EVENT FAMILIES ===\n")
        
        # Statistics
        confidences = [ef.confidence_score for ef in results]
        title_counts = [len(ef.source_title_ids) if ef.source_title_ids else 0 for ef in results]
        event_types = [ef.event_type for ef in results]
        geographies = [ef.geography for ef in results if ef.geography]
        
        print("=== SUMMARY STATISTICS ===")
        print(f"Total Event Families: {len(results)}")
        print(f"Average Confidence: {sum(confidences)/len(confidences):.2f}")
        print(f"High Confidence (>=0.8): {len([c for c in confidences if c >= 0.8])}")
        print(f"Medium Confidence (0.6-0.8): {len([c for c in confidences if 0.6 <= c < 0.8])}")
        print(f"Average Titles per EF: {sum(title_counts)/len(title_counts):.1f}")
        print(f"Single-title EFs: {len([c for c in title_counts if c == 1])}")
        print(f"Multi-title EFs: {len([c for c in title_counts if c > 1])}")
        
        print("\n=== EVENT TYPE DISTRIBUTION ===")
        type_counter = Counter(event_types)
        for event_type, count in type_counter.most_common():
            print(f"{event_type}: {count}")
            
        print("\n=== GEOGRAPHY DISTRIBUTION ===")
        geo_counter = Counter(geographies)
        for geography, count in geo_counter.most_common():
            print(f"{geography}: {count}")
        
        print("\n=== DETAILED EVENT FAMILY ANALYSIS ===\n")
        
        for i, ef in enumerate(results, 1):
            title_count = len(ef.source_title_ids) if ef.source_title_ids else 0
            
            print(f"--- EVENT FAMILY {i} ---")
            print(f"TITLE: {ef.title}")
            print(f"TYPE: {ef.event_type}")
            print(f"GEOGRAPHY: {ef.geography}")
            confidence_level = "HIGH" if ef.confidence_score >= 0.8 else "MEDIUM" if ef.confidence_score >= 0.6 else "LOW"
            print(f"CONFIDENCE: {ef.confidence_score:.2f} ({confidence_level})")
            print(f"SOURCE TITLES: {title_count}")
            print(f"KEY ACTORS: {', '.join(ef.key_actors) if ef.key_actors else 'None'}")
            print(f"TIME SPAN: {ef.event_start} to {ef.event_end}")
            print()
            print("SUMMARY:")
            print(f"{ef.summary}")
            print()
            print("COHERENCE REASON:")
            print(f"{ef.coherence_reason}")
            print()
            print(f"SOURCE TITLE IDs: {ef.source_title_ids}")
            print(f"CREATED: {ef.created_at}")
            print("=" * 80)
            print()

if __name__ == "__main__":
    analyze_event_families()