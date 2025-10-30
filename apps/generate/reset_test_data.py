"""
Reset Test Data for Clean P2 + P3 Pipeline Run

Clears:
1. Events table
2. Title event assignments (event_id → NULL)
3. Title processing status → pending
4. Title gate_keep → NULL
5. Title entities → NULL (for P2 re-extraction)
6. Title action_triple → NULL (for P2 re-extraction)
7. Neo4j Title nodes and relationships
8. Connectivity cache
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402
from core.neo4j_sync import get_neo4j_sync  # noqa: E402


def reset_postgres(limit: int = None):
    """Reset Postgres tables for clean test run"""

    logger.info("=== RESETTING POSTGRES DATA ===")

    with get_db_session() as session:
        # 1. Delete all Events
        logger.info("Deleting all Events...")
        delete_events = "DELETE FROM events"
        result = session.execute(text(delete_events))
        logger.info(f"  Deleted {result.rowcount} events")

        # 2. Clear connectivity cache
        logger.info("Clearing connectivity cache...")
        delete_cache = "DELETE FROM title_connectivity_cache"
        result = session.execute(text(delete_cache))
        logger.info(f"  Deleted {result.rowcount} cache entries")

        # 3. Reset titles (select subset if limit specified)
        if limit:
            logger.info(f"Resetting {limit} most recent titles...")
            reset_query = f"""
            UPDATE titles
            SET event_id = NULL,
                processing_status = 'pending',
                gate_keep = false,
                entities = NULL,
                action_triple = NULL
            WHERE id IN (
                SELECT id FROM titles
                ORDER BY pubdate_utc DESC
                LIMIT {limit}
            )
            """
        else:
            logger.info("Resetting ALL titles...")
            reset_query = """
            UPDATE titles
            SET event_id = NULL,
                processing_status = 'pending',
                gate_keep = false,
                entities = NULL,
                action_triple = NULL
            """

        result = session.execute(text(reset_query))
        logger.info(f"  Reset {result.rowcount} titles")

        session.commit()

    logger.info("SUCCESS: Postgres reset complete\n")


async def reset_neo4j():
    """Clear Neo4j graph for clean test run"""

    logger.info("=== RESETTING NEO4J DATA ===")

    neo4j = get_neo4j_sync()

    # Test connection
    connected = await neo4j.test_connection()
    if not connected:
        logger.error("Neo4j connection failed - skipping Neo4j reset")
        return

    # Delete all relationships first
    logger.info("Deleting Neo4j relationships...")
    delete_rels_query = """
    MATCH ()-[r]->()
    DELETE r
    """

    async with neo4j.driver.session() as session:
        result = await session.run(delete_rels_query)
        summary = await result.consume()
        logger.info(f"  Deleted relationships")

    # Delete all Title nodes
    logger.info("Deleting Neo4j Title nodes...")
    delete_titles_query = """
    MATCH (t:Title)
    DELETE t
    """

    async with neo4j.driver.session() as session:
        result = await session.run(delete_titles_query)
        summary = await result.consume()
        logger.info(f"  Deleted Title nodes")

    # Delete all Entity nodes
    logger.info("Deleting Neo4j Entity nodes...")
    delete_entities_query = """
    MATCH (e:Entity)
    DELETE e
    """

    async with neo4j.driver.session() as session:
        result = await session.run(delete_entities_query)
        summary = await result.consume()
        logger.info(f"  Deleted Entity nodes")

    logger.info("SUCCESS: Neo4j reset complete\n")


async def verify_reset(expected_titles: int = None):
    """Verify reset completed successfully"""

    logger.info("=== VERIFYING RESET ===")

    with get_db_session() as session:
        # Check events
        event_count = session.execute(text("SELECT COUNT(*) FROM events")).scalar()
        logger.info(f"Events: {event_count} (expected: 0)")

        # Check pending titles
        pending_count = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE processing_status = 'pending'")
        ).scalar()
        logger.info(f"Pending titles: {pending_count}")

        # Check titles with event_id
        assigned_count = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE event_id IS NOT NULL")
        ).scalar()
        logger.info(f"Titles with event_id: {assigned_count} (expected: 0)")

        # Check titles with entities
        entities_count = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE entities IS NOT NULL")
        ).scalar()
        logger.info(f"Titles with entities: {entities_count} (expected: 0)")

        # Check connectivity cache
        cache_count = session.execute(
            text("SELECT COUNT(*) FROM title_connectivity_cache")
        ).scalar()
        logger.info(f"Connectivity cache: {cache_count} (expected: 0)")

    # Check Neo4j
    neo4j = get_neo4j_sync()
    async with neo4j.driver.session() as session:
        # Count Title nodes
        result = await session.run("MATCH (t:Title) RETURN count(t) as count")
        record = await result.single()
        title_count = record["count"] if record else 0
        logger.info(f"Neo4j Title nodes: {title_count} (expected: 0)")

        # Count relationships
        result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
        record = await result.single()
        rel_count = record["count"] if record else 0
        logger.info(f"Neo4j relationships: {rel_count} (expected: 0)")

    logger.info("\nSUCCESS: Verification complete")


async def main():
    """Run complete reset"""
    import argparse

    parser = argparse.ArgumentParser(description="Reset test data for P2+P3 pipeline")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of most recent titles to reset (default: all)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify reset, don't delete anything",
    )

    args = parser.parse_args()

    if args.verify_only:
        await verify_reset(args.limit)
        return

    # Confirm destructive operation
    if args.limit:
        print(f"\nWARNING: This will reset {args.limit} most recent titles and delete ALL events.")
    else:
        print("\nWARNING: This will reset ALL titles and delete ALL events.")

    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return

    # Execute reset
    reset_postgres(args.limit)
    await reset_neo4j()
    await verify_reset(args.limit)

    logger.info("\n" + "="*50)
    logger.info("SUCCESS: RESET COMPLETE - Ready for P2+P3 pipeline")
    logger.info("="*50)
    logger.info("\nNext steps:")
    logger.info(f"1. Run P2: python run_phase2.py {args.limit or 'all'}")
    logger.info(f"2. Run P3: python run_p3_v1.py {args.limit or 'all'}")


if __name__ == "__main__":
    asyncio.run(main())
