#!/usr/bin/env python3
"""
Check entity naming patterns in data_entities table
"""

from sqlalchemy import text

from core.database import get_db_session

print("=" * 80)
print("CHECKING ENTITY NAMING PATTERNS")
print("=" * 80)

with get_db_session() as session:
    # Check organizations with short names
    print("\n1. Organizations that might have short name_en:")
    print("-" * 80)

    query = """
    SELECT entity_id, name_en, entity_type
    FROM data_entities
    WHERE entity_type IN ('ORG', 'RegionalOrganization')
    AND (LENGTH(name_en) <= 4 OR name_en IN ('EU', 'UN', 'NATO', 'WHO', 'IMF', 'UAE'))
    ORDER BY name_en;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        print(f"  {row.entity_id:20s} | {row.name_en:30s} | {row.entity_type}")

    # Check all entities that appear in titles.entities
    print("\n2. Checking entities that appear in titles:")
    print("-" * 80)

    # Get distinct entity names from titles
    query = """
    SELECT DISTINCT jsonb_array_elements_text(entities) as entity_name
    FROM titles
    WHERE entities IS NOT NULL AND entities != '[]'
    ORDER BY entity_name;
    """

    entity_names = [row.entity_name for row in session.execute(text(query)).fetchall()]

    # For each entity name, check if it exists in data_entities
    print(f"\nFound {len(entity_names)} unique entity names in titles.entities")
    print("\nChecking against data_entities table:")
    print("-" * 80)

    for entity_name in entity_names[:30]:  # First 30 for now
        # Check if this is an entity_id
        query = """
        SELECT entity_id, name_en, entity_type
        FROM data_entities
        WHERE entity_id = :search OR name_en = :search
        LIMIT 1;
        """

        result = session.execute(text(query), {"search": entity_name}).fetchone()

        if result:
            status = "MATCHED"
            info = f"entity_id={result.entity_id}, name_en={result.name_en}"
        else:
            status = "UNMATCHED"
            info = "(not in data_entities)"

        print(f"  {status:12s} | {entity_name:30s} | {info}")

print("\n" + "=" * 80)
