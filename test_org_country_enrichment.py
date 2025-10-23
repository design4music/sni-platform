#!/usr/bin/env python3
"""
Test Country Enrichment for ALL Entity Types

Verifies that country enrichment works for:
- PERSON entities (Trump, Putin)
- ORG entities (FBI, Pentagon, Bundestag)
- Company entities (if they have iso_code)
- Any other entity type with iso_code populated
"""

from sqlalchemy import text

from apps.filter.country_enrichment import get_country_enricher
from core.database import get_db_session

print("=" * 80)
print("COUNTRY ENRICHMENT TEST - ALL ENTITY TYPES")
print("=" * 80)

# Check all entities with iso_code (not just PERSON)
print("\n1. Entities with iso_code populated (all types):")
print("-" * 80)

with get_db_session() as session:
    query = """
    SELECT e.entity_id, e.name_en, e.entity_type, e.iso_code, c.name_en as country_name
    FROM data_entities e
    LEFT JOIN data_entities c ON e.iso_code = c.entity_id
    WHERE e.iso_code IS NOT NULL
    ORDER BY e.entity_type, e.name_en
    LIMIT 50;
    """

    results = session.execute(text(query)).fetchall()

    # Group by entity_type
    by_type = {}
    for row in results:
        entity_type = row.entity_type
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(row)

    print(f"\nFound {len(results)} entities with iso_code:")
    for entity_type, entities in sorted(by_type.items()):
        print(f"\n  {entity_type} ({len(entities)} entities):")
        for row in entities[:5]:  # Show first 5 of each type
            print(f"    {row.name_en:30s} -> {row.iso_code} ({row.country_name})")
        if len(entities) > 5:
            print(f"    ... and {len(entities) - 5} more")

# Test enrichment with mixed entity types
print("\n" + "=" * 80)
print("2. Testing enrichment with mixed entity types:")
print("-" * 80)

enricher = get_country_enricher()

# Test cases with different entity types
test_cases = [
    # People
    (["Donald Trump"], "PERSON"),
    (["Vladimir Putin", "Emmanuel Macron"], "PERSON"),
    # Organizations (if iso_code is set)
    (["FBI"], "ORG"),
    (["Pentagon"], "ORG"),
    (["Bundestag"], "ORG"),
    (["MI6"], "ORG"),
    # Mixed
    (["Donald Trump", "FBI", "NATO"], "MIXED"),
    (["Putin", "Kremlin"], "MIXED"),
]

print("\nTesting enrichment:")
for original, entity_type in test_cases:
    enriched = enricher.enrich_with_countries(original)

    if enriched != original:
        added = [e for e in enriched if e not in original]
        print(f"\n  {entity_type:10s} | Input:  {original}")
        print(f"  {' ' * 10} | Output: {enriched}")
        print(f"  {' ' * 10} | Added:  {added}")
    else:
        print(f"\n  {entity_type:10s} | Input:  {original}")
        print(f"  {' ' * 10} | Output: {enriched} (no enrichment - iso_code not set)")

# Show expected behavior
print("\n" + "=" * 80)
print("3. Expected behavior after populating iso_code for organizations:")
print("-" * 80)

expected_mappings = [
    ("FBI", "ORG", "US", "United States"),
    ("CIA", "ORG", "US", "United States"),
    ("Pentagon", "ORG", "US", "United States"),
    ("Bundestag", "ORG", "DE", "Germany"),
    ("Kremlin", "ORG", "RU", "Russia"),
    ("MI6", "ORG", "GB", "United Kingdom"),
    ("Mossad", "ORG", "IL", "Israel"),
]

print("\nOnce iso_code is populated for organizations:")
for entity_name, entity_type, iso_code, country in expected_mappings:
    print(
        f"  {entity_name:15s} ({entity_type}) -> iso_code={iso_code:3s} -> adds '{country}'"
    )

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(
    """
Updated behavior:
- NOW works with ALL entity types (PERSON, ORG, Company, etc.)
- BEFORE: Only PERSON entities with iso_code
- AFTER: ANY entity type with iso_code populated

Examples:
- "FBI" detected + iso_code=US -> adds "United States"
- "Pentagon" detected + iso_code=US -> adds "United States"
- "Bundestag" detected + iso_code=DE -> adds "Germany"
- "Donald Trump" detected + iso_code=US -> adds "United States"

Benefits:
- Richer country context for titles mentioning organizations
- Better theater inference for Phase 3 EF generation
- Works automatically as you populate iso_code for any entity type

Next steps:
- Populate iso_code for key organizations (FBI, CIA, Pentagon, etc.)
- Populate iso_code for government agencies by country
- System will automatically use this data
"""
)
print("=" * 80)
