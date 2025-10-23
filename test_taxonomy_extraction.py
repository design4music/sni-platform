#!/usr/bin/env python3
"""
Quick test to verify taxonomy extraction with database-backed GO_LIST and STOP_LIST
"""

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor

# Create extractor with all database-backed vocabularies
extractor = create_multi_vocab_taxonomy_extractor()

# Test cases with GO_LIST terms (should be strategic)
go_test_cases = [
    "China imposes new tariffs on US imports",
    "NATO summit discusses military cooperation",
    "New legislation passed on climate change",
    "Election results show voter turnout increased",
    "Cybersecurity breach affects government systems",
]

# Test cases with STOP_LIST terms (should be blocked)
stop_test_cases = [
    "Film festival announces award winners",
    "Box office records broken this weekend",
    "Celebrity biopic premieres at Cannes",
    "New astrology predictions for 2025",
    "Fashion show features latest trends",
]

# Test cases with actors (should be strategic)
actor_test_cases = [
    "Germany and France announce joint initiative",
    "President Biden meets with NATO allies",
    "United Nations votes on new resolution",
]

print("=" * 60)
print("Database-Backed Taxonomy Extraction Test")
print("=" * 60)

print("\n1. GO_LIST Taxonomy Terms (should match):")
print("-" * 60)
for title in go_test_cases:
    hit = extractor.strategic_first_hit(title)
    entities = extractor.all_strategic_hits(title)
    status = "STRATEGIC" if hit else "NOT STRATEGIC"
    print(f"{status:15} | {title}")
    if entities:
        print(f"                | Entities: {entities}")
    print()

print("\n2. STOP_LIST Taxonomy Terms (should be blocked):")
print("-" * 60)
for title in stop_test_cases:
    hit = extractor.strategic_first_hit(title)
    entities = extractor.all_strategic_hits(title)
    status = "BLOCKED" if hit is None else "STRATEGIC"
    print(f"{status:15} | {title}")
    if entities:
        print(f"                | Entities: {entities}")
    print()

print("\n3. Actor/People Entities (should match):")
print("-" * 60)
for title in actor_test_cases:
    hit = extractor.strategic_first_hit(title)
    entities = extractor.all_strategic_hits(title)
    status = "STRATEGIC" if hit else "NOT STRATEGIC"
    print(f"{status:15} | {title}")
    if entities:
        print(f"                | Entities: {entities}")
    print()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
