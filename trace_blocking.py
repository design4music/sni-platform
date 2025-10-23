#!/usr/bin/env python3
"""Trace what's blocking the football title"""

from apps.filter.taxonomy_extractor import MultiVocabTaxonomyExtractor
from apps.filter.vocab_loader_db import (load_go_taxonomy_aliases,
                                         load_stop_culture_phrases)

# Load vocabularies
stop_vocab = load_stop_culture_phrases()
go_vocab = load_go_taxonomy_aliases()

test_title = "Football regulator could force club owners to sell"
normalized = test_title.lower()

print("=" * 70)
print(f"Title: {test_title}")
print(f"Normalized: {normalized}")
print("=" * 70)

# Check STOP matches
print("\nSTOP_LIST matches:")
stop_matches = []
for term_name, aliases in stop_vocab.items():
    for alias in aliases:
        if alias.lower() in normalized:
            stop_matches.append((term_name, alias))
            print(f"  MATCH: '{alias}' from term '{term_name}'")

if not stop_matches:
    print("  No STOP matches")

# Check GO matches
print("\nGO_LIST matches:")
go_matches = []
for term_name, aliases in go_vocab.items():
    for alias in aliases:
        if alias.lower() in normalized:
            go_matches.append((term_name, alias))
            print(f"  MATCH: '{alias}' from term '{term_name}'")

if not go_matches:
    print("  No GO matches")

# Final determination
print("\n" + "=" * 70)
if stop_matches:
    print(f"RESULT: BLOCKED by STOP_LIST")
    print(f"Blocking term: {stop_matches[0][0]}")
elif go_matches:
    print(f"RESULT: STRATEGIC (GO_LIST matched)")
    print(f"Matching terms: {[m[0] for m in go_matches]}")
else:
    print(f"RESULT: NON-STRATEGIC (no matches)")
