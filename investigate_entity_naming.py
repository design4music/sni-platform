#!/usr/bin/env python3
"""
Investigate entity naming inconsistency in titles.entities
"""

from sqlalchemy import text

from core.database import get_db_session

print("=" * 80)
print("INVESTIGATING ENTITY NAMING INCONSISTENCY")
print("=" * 80)

with get_db_session() as session:
    # Check data_entities table for naming patterns
    print("\n1. Checking data_entities table for key countries:")
    print("-" * 80)

    query = """
    SELECT entity_id, name_en, entity_type
    FROM data_entities
    WHERE entity_id IN ('US', 'IL', 'PS', 'UNITED_STATES', 'ISRAEL', 'STATE_OF_PALESTINE')
       OR name_en IN ('United States', 'Israel', 'State of Palestine')
    ORDER BY entity_id;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        print(
            f"  entity_id: {row.entity_id:20s} | name_en: {row.name_en:30s} | type: {row.entity_type}"
        )

    # Check what's actually stored in titles.entities
    print("\n2. Sample titles.entities content (first 30):")
    print("-" * 80)

    query = """
    SELECT title_display, entities
    FROM titles
    WHERE entities IS NOT NULL AND entities != '[]'
    LIMIT 30;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        print(f"  Title: {row.title_display[:60]}")
        print(f"  Entities: {row.entities}")
        print()

    # Get unique entity names from all titles
    print("\n3. Unique entity names found in titles.entities (first 50):")
    print("-" * 80)

    query = """
    SELECT DISTINCT jsonb_array_elements_text(entities) as entity_name
    FROM titles
    WHERE entities IS NOT NULL AND entities != '[]'
    ORDER BY entity_name
    LIMIT 50;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        print(f"  - {row.entity_name}")

    # Count entity name patterns
    print("\n4. Entity naming patterns analysis:")
    print("-" * 80)

    query = """
    SELECT
        entity_name,
        COUNT(*) as occurrence_count
    FROM (
        SELECT jsonb_array_elements_text(entities) as entity_name
        FROM titles
        WHERE entities IS NOT NULL AND entities != '[]'
    ) subquery
    GROUP BY entity_name
    ORDER BY occurrence_count DESC
    LIMIT 30;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        print(f"  {row.entity_name:30s}: {row.occurrence_count:4d} occurrences")

print("\n" + "=" * 80)
