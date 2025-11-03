#!/usr/bin/env python3
"""Insert international organizations from SQL file"""

from pathlib import Path

from sqlalchemy import text

from core.database import get_db_session

sql_file = Path("data/insert_data_entities_orgs_international_impact_v2.sql")
sql_content = sql_file.read_text(encoding="utf-8")

print("=" * 70)
print("Inserting International Organizations")
print("=" * 70)

with get_db_session() as session:
    # Count before
    result = session.execute(
        text(
            "SELECT COUNT(*) FROM data_entities WHERE entity_type NOT IN ('COUNTRY', 'CAPITAL', 'PERSON')"
        )
    ).scalar()
    print(f"\nBefore: {result} non-country/capital/person entities")

    # Insert
    session.execute(text(sql_content))
    session.commit()

    # Count after
    result = session.execute(
        text(
            "SELECT COUNT(*) FROM data_entities WHERE entity_type NOT IN ('COUNTRY', 'CAPITAL', 'PERSON')"
        )
    ).scalar()
    print(f"After: {result} non-country/capital/person entities")

    # Show entity type distribution
    print("\nEntity type distribution:")
    result = session.execute(
        text(
            """
        SELECT entity_type, COUNT(*) as count
        FROM data_entities
        GROUP BY entity_type
        ORDER BY count DESC
    """
        )
    ).fetchall()

    for row in result:
        print(f"  {row.entity_type:30}: {row.count:4}")

print("\n" + "=" * 70)
print("Insert complete!")
print("=" * 70)
