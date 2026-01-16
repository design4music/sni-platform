#!/usr/bin/env python3
"""
Test entity naming fix - verify _match_llm_entities returns name_en not entity_id
"""

from apps.filter.entity_enrichment import EntityEnrichmentService

print("=" * 80)
print("TESTING ENTITY NAMING FIX")
print("=" * 80)

service = EntityEnrichmentService()

# Test cases: LLM might extract these raw strings
test_cases = [
    ["United States", "Germany"],  # Full names
    ["US", "Germany"],  # Mix of code + name
    ["India", "China"],  # Full names
    ["Israel", "Palestine"],  # Full names
    ["Donald Trump", "Joe Biden"],  # People
    ["NATO", "UN", "EU"],  # Organizations
]

print("\nTesting _match_llm_entities() method:")
print("-" * 80)

for llm_entities in test_cases:
    matched = service._match_llm_entities(llm_entities)

    print(f"\nInput:  {llm_entities}")
    print(f"Output: {matched}")

    # Verify all outputs are full names (not short codes like "US", "IL", "PS")
    for entity in matched:
        if len(entity) <= 3 and entity.isupper() and entity.isalpha():
            print(f"  WARNING: Short code detected: '{entity}' (should be full name)")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("\nExpected behavior:")
print("  - All outputs should be full entity names (name_en)")
print("  - No short codes like 'US', 'IL', 'PS', 'IN', 'AG'")
print("  - Should see: 'United States', 'Israel', 'State of Palestine', 'India'")
print("=" * 80)
