#!/usr/bin/env python3
"""Test entity extraction on specific titles"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor

test_cases = [
    "China's rare-earths power move jolted Trump but was years in the making",
    "Why American Palestinians are nervous about what comes next",
    "arab states expanded cooperation with israeli military during gaza war, files show",
    "column i used an ai tool to resurrect my grandmother, and it was awful",
    "u.s. revoked at least six visas over kirk comments, state department says",
    "opinion is it americas fate to decline and fall? heres what history says.",
    "opinion as a professor, ive seen woke and maga censorship. which is worse?",
    "ev owners are using their trucks giant batteries to prevent blackouts",
]

extractor = create_multi_vocab_taxonomy_extractor()

print("Testing entity extraction:\n")

for title in test_cases:
    print(f"Title: {title}")
    print(f"Normalized: {extractor.normalize(title)}")

    strategic_hit = extractor.strategic_first_hit(title)
    all_hits = extractor.all_strategic_hits(title)

    print(f"Strategic first hit: {strategic_hit}")
    print(f"All strategic hits: {all_hits}")
    print("-" * 80)
