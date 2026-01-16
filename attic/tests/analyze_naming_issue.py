#!/usr/bin/env python3
"""
Analyze the entity naming issue - where are entity_ids leaking through?
"""

from sqlalchemy import text

from core.database import get_db_session

print("=" * 80)
print("ENTITY NAMING ISSUE ANALYSIS")
print("=" * 80)

with get_db_session() as session:
    # Check problematic entities mentioned by user
    print(
        "\n1. Entities mentioned by user (IL, PS, US, Israel, State of Palestine, United States):"
    )
    print("-" * 80)

    problematic_names = [
        "IL",
        "PS",
        "US",
        "IN",
        "AG",
        "Israel",
        "State of Palestine",
        "United States",
        "India",
        "UN",
        "United Nations",
        "EU",
    ]

    for name in problematic_names:
        query = """
        SELECT entity_id, name_en, entity_type
        FROM data_entities
        WHERE entity_id = :name OR name_en = :name
        LIMIT 1;
        """

        result = session.execute(text(query), {"name": name}).fetchone()

        if result:
            # Count usage in titles separately
            count_query = """
            SELECT COUNT(*) as cnt
            FROM titles
            WHERE entities::text LIKE :pattern;
            """
            pattern = f'%"{name}"%'
            usage = session.execute(text(count_query), {"pattern": pattern}).fetchone()

            print(f"\n  '{name}' FOUND:")
            print(f"    entity_id: {result.entity_id}")
            print(f"    name_en: {result.name_en}")
            print(f"    entity_type: {result.entity_type}")
            print(f"    Used in {usage.cnt if usage else 0} titles")
        else:
            # Check if it appears in titles but not in data_entities
            count_query = """
            SELECT COUNT(*) as cnt
            FROM titles
            WHERE entities::text LIKE :pattern;
            """
            pattern = f'%"{name}"%'
            usage = session.execute(text(count_query), {"pattern": pattern}).fetchone()
            print(
                f"\n  '{name}' NOT IN data_entities but used in {usage.cnt if usage else 0} titles"
            )

    # Check UN separately - is it United Nations?
    print("\n" + "=" * 80)
    print("2. Checking UN vs United Nations:")
    print("-" * 80)

    query = """
    SELECT entity_id, name_en, entity_type
    FROM data_entities
    WHERE entity_id LIKE 'UN%' OR name_en LIKE '%United Nations%'
    ORDER BY entity_id;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        print(f"  {row.entity_id:20s} | {row.name_en:40s} | {row.entity_type}")

    # Categorize entities in titles by whether they match entity_id or name_en
    print("\n" + "=" * 80)
    print("3. Categorizing all entities in titles.entities:")
    print("-" * 80)

    query = """
    SELECT DISTINCT jsonb_array_elements_text(entities) as entity_name
    FROM titles
    WHERE entities IS NOT NULL AND entities != '[]';
    """

    entity_names = [row.entity_name for row in session.execute(text(query)).fetchall()]

    entity_ids_used = []
    name_ens_used = []
    unmatched = []

    for entity_name in entity_names:
        query = """
        SELECT entity_id, name_en, entity_type
        FROM data_entities
        WHERE entity_id = :search OR name_en = :search;
        """

        result = session.execute(text(query), {"search": entity_name}).fetchone()

        if result:
            if result.entity_id == entity_name:
                # Matched as entity_id
                if result.name_en != entity_name:
                    entity_ids_used.append(
                        (entity_name, result.name_en, result.entity_type)
                    )
            else:
                # Matched as name_en
                name_ens_used.append(entity_name)
        else:
            unmatched.append(entity_name)

    print(f"\n  ENTITY_IDs being used (should be name_en): {len(entity_ids_used)}")
    for entity_id, name_en, entity_type in entity_ids_used:
        print(f"    {entity_id:15s} → should be '{name_en}' ({entity_type})")

    print(f"\n  NAME_ENs being used correctly: {len(name_ens_used)}")
    print(f"  Unmatched (not in data_entities): {len(unmatched)}")
    if unmatched:
        print("    Examples:", unmatched[:10])

print("\n" + "=" * 80)
