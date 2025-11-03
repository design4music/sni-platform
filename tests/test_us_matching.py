#!/usr/bin/env python3
import re

# Simulate what taxonomy_extractor does
test_texts = [
    "u.s. revoked at least six visas",
    "us revoked at least six visas",
    "the u.s. revoked visas",
    "USA revoked visas",
]

aliases = ["U.S.", "USA", "United States", "U.S.A."]

for text in test_texts:
    print(f"\nText: {text}")
    for alias in aliases:
        alias_lower = alias.lower()
        pattern = re.compile(r"\b" + re.escape(alias_lower) + r"\b", re.IGNORECASE)
        match = pattern.search(text)
        print(
            f"  Alias '{alias}' -> pattern '{pattern.pattern}' -> {'MATCH' if match else 'NO MATCH'}"
        )
