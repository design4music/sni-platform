#!/usr/bin/env python3
"""
Test entity enrichment with database-backed taxonomy
Re-processes a few recent titles to populate them with taxonomy terms
"""

import asyncio

from sqlalchemy import text

from apps.filter.entity_enrichment import get_entity_enrichment_service
from core.database import get_db_session


async def test_enrichment():
    # Get some recent title IDs
    with get_db_session() as session:
        query = text(
            """
            SELECT id, title_display
            FROM titles
            WHERE created_at >= NOW() - INTERVAL '7 DAY'
            ORDER BY created_at DESC
            LIMIT 5
        """
        )
        results = session.execute(query).fetchall()
        title_ids = [str(row.id) for row in results]

    print("=" * 80)
    print("Testing Entity Enrichment with Database-Backed Taxonomy")
    print("=" * 80)
    print(f"\nProcessing {len(title_ids)} titles...\n")

    # Show titles before enrichment
    with get_db_session() as session:
        for title_id in title_ids:
            query = text("SELECT title_display, entities FROM titles WHERE id = :id")
            result = session.execute(query, {"id": title_id}).fetchone()
            print(f"BEFORE: {result.title_display[:70]}")
            print(f"        Entities: {result.entities}\n")

    # Run enrichment
    service = get_entity_enrichment_service()
    stats = await service.enrich_titles_batch(title_ids=title_ids)

    print("\n" + "=" * 80)
    print("Enrichment Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 80)

    # Show titles after enrichment
    print("\nTitles After Enrichment:")
    print("-" * 80)
    with get_db_session() as session:
        for title_id in title_ids:
            query = text(
                "SELECT title_display, entities, gate_keep FROM titles WHERE id = :id"
            )
            result = session.execute(query, {"id": title_id}).fetchone()
            print(f"\nTitle: {result.title_display}")
            print(f"Entities: {result.entities}")
            print(f"Gate Keep: {result.gate_keep}")


if __name__ == "__main__":
    asyncio.run(test_enrichment())
