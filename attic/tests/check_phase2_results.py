#!/usr/bin/env python3
"""Check Phase 2 enrichment results"""

from sqlalchemy import text

from core.database import get_db_session

with get_db_session() as session:
    # Get overall stats
    stats = session.execute(
        text(
            """
        SELECT
            COUNT(*) as total_titles,
            COUNT(entities) as enriched_titles,
            COUNT(CASE WHEN gate_keep = TRUE THEN 1 END) as strategic_titles,
            COUNT(CASE WHEN gate_keep = FALSE THEN 1 END) as non_strategic_titles
        FROM titles
    """
        )
    ).fetchone()

    print("=" * 80)
    print("Phase 2 Enrichment Results")
    print("=" * 80)
    print(f"\nTotal titles: {stats.total_titles}")
    print(f"Enriched titles: {stats.enriched_titles}")
    print(f"Strategic titles (gate_keep=true): {stats.strategic_titles}")
    print(f"Non-strategic titles (gate_keep=false): {stats.non_strategic_titles}")

    # Entity count distribution
    print("\n" + "=" * 80)
    print("Entity Count Distribution:")
    print("=" * 80)

    query = text(
        """
        SELECT
            CASE
                WHEN jsonb_array_length(entities) = 0 THEN '0 entities'
                WHEN jsonb_array_length(entities) = 1 THEN '1 entity'
                WHEN jsonb_array_length(entities) = 2 THEN '2 entities'
                WHEN jsonb_array_length(entities) >= 3 THEN '3+ entities'
            END as entity_group,
            COUNT(*) as title_count
        FROM titles
        WHERE entities IS NOT NULL
        GROUP BY entity_group
        ORDER BY entity_group
    """
    )
    results = session.execute(query).fetchall()

    for row in results:
        print(f"  {row.entity_group:15}: {row.title_count:5} titles")

    # Sample strategic titles WITH entities (actors + taxonomy)
    print("\n" + "=" * 80)
    print("Sample Strategic Titles WITH Entities:")
    print("=" * 80)

    query = text(
        """
        SELECT title_display, entities
        FROM titles
        WHERE entities IS NOT NULL
        AND jsonb_array_length(entities) > 0
        AND gate_keep = TRUE
        ORDER BY created_at DESC
        LIMIT 15
    """
    )
    results = session.execute(query).fetchall()

    for i, row in enumerate(results, 1):
        entities_str = str(row.entities).encode("ascii", "ignore").decode("ascii")
        print(f"\n{i}. {row.title_display[:65]}")
        print(f"   Entities: {entities_str}")

    # Sample strategic titles WITHOUT entities (LLM strategic decision)
    print("\n" + "=" * 80)
    print("Sample Strategic Titles WITHOUT Entities (LLM Decision):")
    print("=" * 80)

    query = text(
        """
        SELECT title_display, entities
        FROM titles
        WHERE entities IS NOT NULL
        AND (jsonb_array_length(entities) = 0 OR entities = '[]'::jsonb)
        AND gate_keep = TRUE
        ORDER BY created_at DESC
        LIMIT 10
    """
    )
    results = session.execute(query).fetchall()

    for i, row in enumerate(results, 1):
        print(f"\n{i}. {row.title_display}")

    # Sample NON-strategic titles
    print("\n" + "=" * 80)
    print("Sample NON-Strategic Titles:")
    print("=" * 80)

    query = text(
        """
        SELECT title_display
        FROM titles
        WHERE entities IS NOT NULL
        AND gate_keep = FALSE
        ORDER BY created_at DESC
        LIMIT 5
    """
    )
    results = session.execute(query).fetchall()

    for i, row in enumerate(results, 1):
        print(f"\n{i}. {row.title_display}")

print("\n" + "=" * 80)
