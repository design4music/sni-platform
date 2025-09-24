#!/usr/bin/env python3
"""
Debug why Biden-Ukraine title is not being flagged as strategic
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.filter.taxonomy_extractor import create_multi_vocab_taxonomy_extractor

def debug_title_processing():
    """Debug the Biden-Ukraine title step by step"""

    # Create taxonomy extractor
    extractor = create_multi_vocab_taxonomy_extractor()

    title = "Biden meets with Ukrainian president to discuss aid"

    print(f"=== DEBUGGING TITLE: {title} ===")
    print()

    # Test strategic_first_hit
    strategic_hit = extractor.strategic_first_hit(title)
    print(f"strategic_first_hit result: {strategic_hit}")
    print()

    # Test all_strategic_hits
    all_hits = extractor.all_strategic_hits(title)
    print(f"all_strategic_hits result: {all_hits}")
    print()

    # Check individual vocabularies
    print("=== VOCABULARY BREAKDOWN ===")

    # Check go_actors (countries)
    go_actors_hits = []
    for vocab in extractor.go_vocabs:
        if hasattr(vocab, 'vocabulary_id') and 'actors' in vocab.vocabulary_id:
            matches = vocab.search_text(title)
            if matches:
                go_actors_hits.extend(matches)
    print(f"go_actors hits: {go_actors_hits}")

    # Check go_people
    go_people_hits = []
    for vocab in extractor.go_vocabs:
        if hasattr(vocab, 'vocabulary_id') and 'people' in vocab.vocabulary_id:
            matches = vocab.search_text(title)
            if matches:
                go_people_hits.extend(matches)
    print(f"go_people hits: {go_people_hits}")

    # Check stop_culture
    stop_hits = []
    for vocab in extractor.stop_vocabs:
        if hasattr(vocab, 'vocabulary_id') and 'culture' in vocab.vocabulary_id:
            matches = vocab.search_text(title)
            if matches:
                stop_hits.extend(matches)
    print(f"stop_culture hits: {stop_hits}")
    print()

    # Final determination
    is_strategic = strategic_hit is not None
    print(f"=== FINAL RESULT ===")
    print(f"Is Strategic: {is_strategic}")

    if not is_strategic:
        if stop_hits:
            print("REASON: Blocked by stop_culture words")
        elif not go_actors_hits and not go_people_hits:
            print("REASON: No positive signals from go_actors or go_people")
        else:
            print("REASON: Unknown - investigate further")

if __name__ == "__main__":
    debug_title_processing()