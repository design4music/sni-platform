#!/usr/bin/env python3
"""
Test Country Enrichment - Auto-add countries for detected people

Demonstrates how the system will auto-add countries to titles.entities
when PERSON entities with iso_code are detected.
"""

from sqlalchemy import text

from apps.filter.country_enrichment import get_country_enricher
from core.database import get_db_session

print("=" * 80)
print("COUNTRY ENRICHMENT TEST")
print("=" * 80)

# Check current state of iso_code in data_entities
print("\n1. Checking PERSON entities with iso_code populated:")
print("-" * 80)

with get_db_session() as session:
    query = """
    SELECT p.entity_id, p.name_en, p.iso_code, c.name_en as country_name
    FROM data_entities p
    LEFT JOIN data_entities c ON p.iso_code = c.entity_id
    WHERE p.entity_type = 'PERSON' AND p.iso_code IS NOT NULL
    ORDER BY p.name_en
    LIMIT 20;
    """

    results = session.execute(text(query)).fetchall()

    if results:
        print(f"\nFound {len(results)} people with iso_code:")
        for row in results:
            print(f"  {row.name_en:30s} -> {row.iso_code} ({row.country_name})")
    else:
        print("\n  No PERSON entities have iso_code populated yet.")
        print("  User will manually update iso_code column for key political figures.")

# Test enrichment logic with sample data
print("\n" + "=" * 80)
print("2. Testing enrichment logic:")
print("-" * 80)

enricher = get_country_enricher()

# Test cases
test_cases = [
    ["Donald Trump"],  # If iso_code=US, should add "United States"
    ["Vladimir Putin"],  # If iso_code=RU, should add "Russia"
    [
        "Emmanuel Macron",
        "Germany",
    ],  # If iso_code=FR, should add "France" (Germany already there)
    ["NATO", "Joe Biden"],  # If iso_code=US, should add "United States"
    ["China", "Xi Jinping"],  # If iso_code=CN, China already there (no duplicate)
]

print("\nTest cases (will only enrich if iso_code is populated):")
for original in test_cases:
    enriched = enricher.enrich_with_countries(original)

    if enriched != original:
        print(f"\n  Input:  {original}")
        print(f"  Output: {enriched}")
        print(f"  Added:  {[e for e in enriched if e not in original]}")
    else:
        print(f"\n  Input:  {original}")
        print(f"  Output: {enriched} (no enrichment - iso_code not set)")

# Show how it works in production
print("\n" + "=" * 80)
print("3. Expected behavior after iso_code is populated:")
print("-" * 80)

expected_examples = [
    (
        "Trump says new tariffs coming",
        ["Donald Trump"],
        ["Donald Trump", "United States"],
    ),
    (
        "Putin meets with Chinese leader",
        ["Vladimir Putin", "China"],
        ["Vladimir Putin", "China", "Russia"],
    ),
    (
        "Macron and Scholz discuss EU policy",
        ["Emmanuel Macron", "Olaf Scholz", "EU"],
        ["Emmanuel Macron", "Olaf Scholz", "EU", "France", "Germany"],
    ),
]

print("\nOnce iso_code is populated:")
for title, detected, expected_entities in expected_examples:
    print(f"\n  Title: {title}")
    print(f"  Detected: {detected}")
    print(f"  Expected entities: {expected_entities}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(
    """
How it works:
1. When a PERSON entity is detected (via taxonomy or LLM)
2. System looks up that person's iso_code in data_entities table
3. If iso_code exists (e.g., "US" for Trump), look up country name
4. Auto-add country to entities array if not already present

Benefits:
- Titles about Trump automatically get "United States" added
- Titles about Putin automatically get "Russia" added
- Enables better theater inference for Phase 3 EF generation

Next steps:
- User will manually populate iso_code for ~50-100 key political figures
- System is ready to use this data immediately
"""
)
print("=" * 80)
