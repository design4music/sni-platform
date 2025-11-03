#!/usr/bin/env python3
"""
Reset Phase 2 Entity Enrichment - Prepare for clean re-processing
Clears entities in both PostgreSQL and Neo4j while keeping title records
"""

from sqlalchemy import text

from core.database import get_db_session
from core.neo4j_sync import get_neo4j_sync


def reset_phase2_enrichment():
    """
    Reset Phase 2 entity enrichment data:
    1. Clear titles.entities (JSONB array)
    2. Reset titles.gate_keep to FALSE
    3. Clear Neo4j entities and relationships
    """

    print("=" * 60)
    print("Phase 2 Entity Enrichment Reset")
    print("=" * 60)

    # Step 1: Get counts before reset
    with get_db_session() as session:
        stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total_titles,
                COUNT(entities) as enriched_titles,
                COUNT(CASE WHEN gate_keep = TRUE THEN 1 END) as strategic_titles
            FROM titles
        """
            )
        ).fetchone()

        print(f"\nBefore Reset:")
        print(f"  Total titles: {stats.total_titles}")
        print(f"  Enriched titles (entities not null): {stats.enriched_titles}")
        print(f"  Strategic titles (gate_keep=true): {stats.strategic_titles}")

    # Step 2: Reset PostgreSQL titles table
    print(f"\n[1/3] Resetting PostgreSQL titles table...")
    with get_db_session() as session:
        session.execute(
            text(
                """
            UPDATE titles
            SET gate_keep = FALSE,
                entities = NULL
            WHERE entities IS NOT NULL OR gate_keep = TRUE
        """
            )
        )
        session.commit()
        print("  [OK] Cleared entities and reset gate_keep to FALSE")

    # Step 3: Clear Neo4j entities and relationships
    print(f"\n[2/3] Clearing Neo4j entities and relationships...")
    try:
        neo4j = get_neo4j_sync()

        # Count entities before deletion
        with neo4j.driver.session() as neo_session:
            result = neo_session.run(
                """
                MATCH (t:Title)-[r:MENTIONS]->(e:Entity)
                RETURN count(DISTINCT e) as entity_count, count(r) as mention_count
            """
            )
            record = result.single()
            entity_count = record["entity_count"] if record else 0
            mention_count = record["mention_count"] if record else 0

            print(
                f"  Before: {entity_count} entities, {mention_count} mention relationships"
            )

            # Delete all Entity nodes and MENTIONS relationships
            neo_session.run(
                """
                MATCH (e:Entity)
                DETACH DELETE e
            """
            )

            print(f"  [OK] Deleted all Entity nodes and MENTIONS relationships")

    except Exception as e:
        print(f"  [WARNING] Neo4j clear failed: {e}")
        print(f"  Continuing with PostgreSQL reset...")

    # Step 4: Verify reset
    print(f"\n[3/3] Verifying reset...")
    with get_db_session() as session:
        stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total_titles,
                COUNT(entities) as enriched_titles,
                COUNT(CASE WHEN gate_keep = TRUE THEN 1 END) as strategic_titles
            FROM titles
        """
            )
        ).fetchone()

        print(f"\nAfter Reset:")
        print(f"  Total titles: {stats.total_titles}")
        print(f"  Enriched titles: {stats.enriched_titles} (should be 0)")
        print(f"  Strategic titles: {stats.strategic_titles} (should be 0)")

    print("\n" + "=" * 60)
    print("Phase 2 Reset Complete!")
    print("Ready for clean re-processing with new taxonomy system")
    print("=" * 60)


if __name__ == "__main__":
    # Prompt for confirmation
    response = input(
        "\nThis will clear all Phase 2 enrichment data (entities, gate_keep).\nContinue? (yes/no): "
    )

    if response.lower() in ["yes", "y"]:
        reset_phase2_enrichment()
    else:
        print("Reset cancelled.")
