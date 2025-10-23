#!/usr/bin/env python3
"""Find football term directly in database"""

import json

from sqlalchemy import text

from core.database import get_db_session

with get_db_session() as session:
    # Find all sport-related terms in STOP_LIST
    result = session.execute(
        text(
            """
        SELECT t.name_en, t.terms, c.category_id
        FROM taxonomy_terms t
        JOIN taxonomy_categories c ON t.category_id = c.category_id
        WHERE c.is_positive = FALSE
        AND c.category_id LIKE '%sport%'
        ORDER BY t.name_en
    """
        )
    ).fetchall()

    print("=" * 70)
    print(f"Sport-related STOP_LIST terms in database: {len(result)}")
    print("=" * 70)

    for row in result:
        terms_data = json.loads(row.terms) if isinstance(row.terms, str) else row.terms
        head_en = terms_data.get("head_en", "N/A")
        aliases = terms_data.get("aliases", {})
        en_aliases = aliases.get("en", [])

        print(f"\n{row.name_en}")
        print(f"  Category: {row.category_id}")
        print(f"  head_en: {head_en}")
        print(f"  EN aliases: {en_aliases[:5]}")

        # Check if this is football
        if "football" in row.name_en.lower() or any(
            "football" in str(a).lower() for a in en_aliases
        ):
            print(f"  >>> FOUND FOOTBALL TERM!")
