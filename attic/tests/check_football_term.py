#!/usr/bin/env python3
"""Check if football is in STOP_LIST taxonomy"""

from sqlalchemy import text

from core.database import get_db_session

with get_db_session() as session:
    # Check for football term
    result = session.execute(
        text(
            """
        SELECT t.name_en, c.category_id, c.is_positive, t.terms
        FROM taxonomy_terms t
        JOIN taxonomy_categories c ON t.category_id = c.category_id
        WHERE t.name_en ILIKE '%football%'
    """
        )
    ).fetchall()

    print("Football in taxonomy:")
    for row in result:
        print(
            f"  {row.name_en} - Category: {row.category_id} - GO_LIST: {row.is_positive}"
        )
        print(f"  Terms: {row.terms}")

    # Check all STOP_LIST sport terms
    print("\nAll sport-related STOP_LIST terms:")
    result = session.execute(
        text(
            """
        SELECT t.name_en
        FROM taxonomy_terms t
        JOIN taxonomy_categories c ON t.category_id = c.category_id
        WHERE c.is_positive = FALSE
        AND (c.category_id LIKE '%sport%' OR t.name_en ILIKE '%sport%' OR t.name_en ILIKE '%football%' OR t.name_en ILIKE '%soccer%')
        ORDER BY t.name_en
    """
        )
    ).fetchall()

    for row in result:
        print(f"  - {row.name_en}")
