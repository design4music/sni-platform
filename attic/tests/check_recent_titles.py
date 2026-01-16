#!/usr/bin/env python3
"""Check recent titles in the database"""

from sqlalchemy import text

from core.database import get_db_session

with get_db_session() as session:
    query = text(
        """
        SELECT
            id,
            title_display,
            entities,
            gate_keep,
            created_at
        FROM titles
        WHERE created_at >= NOW() - INTERVAL '7 DAY'
        ORDER BY created_at DESC
        LIMIT 10
    """
    )

    results = session.execute(query).fetchall()

    print(f"Found {len(results)} recent titles in database")
    print("=" * 80)

    for i, row in enumerate(results, 1):
        print(f"\n{i}. Title: {row.title_display}")
        print(f"   ID: {row.id}")
        print(f"   Created: {row.created_at}")
        print(f"   Entities: {row.entities}")
        print(f"   Gate Keep: {row.gate_keep}")
