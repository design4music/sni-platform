#!/usr/bin/env python3
"""
Verify migration - check that no entity_ids remain in titles.entities
"""

from sqlalchemy import text

from core.database import get_db_session

print("=" * 80)
print("VERIFICATION: Check for remaining entity_ids in titles.entities")
print("=" * 80)

with get_db_session() as session:
    # Check for common entity_ids that should be converted
    problematic_ids = [
        "US",
        "IL",
        "PS",
        "IN",
        "AG",
        "GB",
        "FR",
        "DE",
        "BR",
        "NG",
        "AR",
        "KE",
    ]

    print("\n1. Checking for entity_ids that should have been converted:")
    print("-" * 80)

    found_any = False
    for entity_id in problematic_ids:
        query = """
        SELECT COUNT(*) as cnt
        FROM titles
        WHERE entities::text LIKE :pattern;
        """
        pattern = f'%"{entity_id}"%'
        result = session.execute(text(query), {"pattern": pattern}).fetchone()

        if result.cnt > 0:
            print(f"  WARNING: Found {result.cnt} titles with '{entity_id}'")
            found_any = True

    if not found_any:
        print("  SUCCESS: No entity_ids found (all converted to name_en)")

    # Sample some titles to show the result
    print("\n2. Sample titles.entities after migration:")
    print("-" * 80)

    query = """
    SELECT title_display, entities
    FROM titles
    WHERE entities IS NOT NULL AND entities != '[]'
    ORDER BY created_at DESC
    LIMIT 10;
    """

    results = session.execute(text(query)).fetchall()
    for row in results:
        try:
            print(f"\n  Title: {row.title_display[:60]}")
        except UnicodeEncodeError:
            safe_title = (
                row.title_display[:60].encode("ascii", "ignore").decode("ascii")
            )
            print(f"\n  Title: {safe_title}")
        print(f"  Entities: {row.entities}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
