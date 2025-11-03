#!/usr/bin/env python3
"""Debug what's being loaded in STOP_LIST vocabulary"""

from apps.filter.vocab_loader_db import load_stop_culture_phrases

stop_vocab = load_stop_culture_phrases()

print("=" * 70)
print(f"STOP_LIST Vocabulary: {len(stop_vocab)} terms loaded")
print("=" * 70)

# Show all terms
print("\nAll STOP_LIST terms:")
for i, (name_en, aliases) in enumerate(sorted(stop_vocab.items()), 1):
    aliases_preview = aliases[:3] if len(aliases) > 3 else aliases
    print(f"{i:2}. {name_en:20} - {len(aliases)} aliases - {aliases_preview}")

# Check for sport-related terms
print("\n" + "=" * 70)
print("Sport-related terms:")
print("=" * 70)
sport_terms = [
    name
    for name in stop_vocab.keys()
    if "sport" in name.lower() or "football" in name.lower() or "soccer" in name.lower()
]
for term in sport_terms:
    print(f"  - {term}: {stop_vocab[term][:5]}")
