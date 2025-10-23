#!/usr/bin/env python3
"""Test why football title wasn't blocked"""

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor

# Create extractor
extractor = create_multi_vocab_taxonomy_extractor()

# Test the problematic title
test_title = "Football regulator could force club owners to sell"

print("=" * 70)
print("Testing STOP_LIST blocking for:")
print(f"  '{test_title}'")
print("=" * 70)

# Check if it hits strategic filter
strategic_hit = extractor.strategic_first_hit(test_title)
entities = extractor.all_strategic_hits(test_title)

print(f"\nStrategic hit: {strategic_hit}")
print(f"Entities: {entities}")
print(f"Result: {'BLOCKED' if strategic_hit is None else 'STRATEGIC (NOT BLOCKED!)'}")

# Manually check stop_culture vocabulary
from apps.filter.vocab_loader_db import load_stop_culture_phrases

stop_vocab = load_stop_culture_phrases()
print(f"\n'football' in stop vocabulary: {'football' in stop_vocab}")

if "football" in stop_vocab:
    print(f"Football aliases: {stop_vocab['football'][:5]}")

# Test normalization
normalized = extractor.normalize(test_title)
print(f"\nNormalized title: '{normalized}'")

# Check if 'football' matches in normalized text
if "football" in normalized.lower():
    print("'football' IS in normalized text - should be blocked!")
else:
    print("'football' NOT in normalized text")
