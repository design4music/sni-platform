#!/usr/bin/env python3
"""
Test Phase 2 Entity Enrichment with new database-backed taxonomy
Process ~300 recent titles and evaluate results
"""

import asyncio

from sqlalchemy import text

from apps.filter.entity_enrichment import get_entity_enrichment_service
from core.database import get_db_session


async def run_phase2_test():
    """Run Phase 2 enrichment on ~300 recent titles"""

    print("=" * 80)
    print("Phase 2 Entity Enrichment Test - Database-Backed Taxonomy")
    print("=" * 80)

    # Get sample of ~300 titles
    with get_db_session() as session:
        query = text(
            """
            SELECT COUNT(*) as pending_titles
            FROM titles
            WHERE entities IS NULL
            AND created_at >= NOW() - INTERVAL '7 DAY'
        """
        )
        result = session.execute(query).fetchone()
        print(f"\nPending titles (last 7 days): {result.pending_titles}")

    # Run enrichment on 300 titles
    print(f"\nProcessing 300 titles with new taxonomy system...")
    print("-" * 80)

    service = get_entity_enrichment_service()
    stats = await service.enrich_titles_batch(limit=300, since_hours=7 * 24)

    print("\n" + "=" * 80)
    print("Enrichment Statistics:")
    print("=" * 80)
    for key, value in stats.items():
        print(f"  {key:20}: {value}")

    # Show sample results
    print("\n" + "=" * 80)
    print("Sample Results:")
    print("=" * 80)

    with get_db_session() as session:
        # Get strategic titles with entities
        query = text(
            """
            SELECT title_display, entities, gate_keep
            FROM titles
            WHERE entities IS NOT NULL
            AND jsonb_array_length(entities) > 0
            ORDER BY created_at DESC
            LIMIT 10
        """
        )
        results = session.execute(query).fetchall()

        for i, row in enumerate(results, 1):
            entities_str = str(row.entities).encode("ascii", "ignore").decode("ascii")
            print(f"\n{i}. [{row.gate_keep and 'STRATEGIC' or 'NON-STRATEGIC'}]")
            print(f"   Title: {row.title_display[:70]}")
            print(f"   Entities: {entities_str}")

    # Show breakdown by entity count
    print("\n" + "=" * 80)
    print("Entity Count Distribution:")
    print("=" * 80)

    with get_db_session() as session:
        query = text(
            """
            SELECT
                jsonb_array_length(entities) as entity_count,
                COUNT(*) as title_count
            FROM titles
            WHERE entities IS NOT NULL
            GROUP BY jsonb_array_length(entities)
            ORDER BY entity_count
        """
        )
        results = session.execute(query).fetchall()

        for row in results:
            print(f"  {row.entity_count} entities: {row.title_count} titles")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_phase2_test())
