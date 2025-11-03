#!/usr/bin/env python3
"""Insert international organizations with ON CONFLICT handling"""

from pathlib import Path

from sqlalchemy import text

from core.database import get_db_session

sql_file = Path("data/insert_data_entities_orgs_international_impact_v2.sql")
sql_content = sql_file.read_text(encoding="utf-8")

# Add ON CONFLICT DO NOTHING to handle duplicates
sql_content_safe = sql_content.replace("VALUES", "VALUES", 1).replace(
    ";", "\nON CONFLICT (entity_id) DO NOTHING;", 1
)

print("=" * 70)
print("Inserting International Organizations (with conflict handling)")
print("=" * 70)

with get_db_session() as session:
    # Count before
    result = session.execute(text("SELECT COUNT(*) FROM data_entities")).scalar()
    print(f"\nBefore: {result} total entities")

    # Insert with ON CONFLICT
    session.execute(text(sql_content_safe))
    session.commit()

    # Count after
    result = session.execute(text("SELECT COUNT(*) FROM data_entities")).scalar()
    print(f"After: {result} total entities")

    # Show new entity types
    print("\nAll entity types in database:")
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
        print(f"  {row.entity_type:35}: {row.count:4}")

print("\n" + "=" * 70)
print("Insert complete!")
print("=" * 70)
