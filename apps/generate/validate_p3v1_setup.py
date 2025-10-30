"""
P3_v1 Setup Validation Script

Checks prerequisites before running P3_v1:
1. Connectivity cache table exists
2. Neo4j relationships exist
3. Cache is populated
4. Titles have AAT data
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


async def validate_setup():
    """Run all validation checks"""
    logger.info("=== P3_v1 Setup Validation ===\n")

    all_passed = True

    # Check 1: Connectivity cache table
    logger.info("Check 1: Connectivity cache table exists")
    with get_db_session() as session:
        try:
            result = session.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'title_connectivity_cache'
                )
            """
                )
            ).scalar()

            if result:
                logger.info("✓ Connectivity cache table exists")

                # Check cache population
                count = session.execute(
                    text("SELECT COUNT(*) FROM title_connectivity_cache")
                ).scalar()
                logger.info(f"  Cache entries: {count}")

                if count == 0:
                    logger.warning(
                        "  ⚠ Cache is empty - run connectivity_cache.py to populate"
                    )
                    all_passed = False
                else:
                    logger.info(f"  ✓ Cache populated with {count} entries")

            else:
                logger.error(
                    "✗ Connectivity cache table missing - run migration first"
                )
                logger.error(
                    "  Run: psql -f db/migrations/20251029_add_title_connectivity_cache.sql"
                )
                all_passed = False

        except Exception as e:
            logger.error(f"✗ Failed to check cache table: {e}")
            all_passed = False

    # Check 2: Neo4j connectivity
    logger.info("\nCheck 2: Neo4j relationships")
    try:
        neo4j = get_neo4j_sync()

        # Check CO_OCCURS relationships
        query_co_occurs = """
        MATCH ()-[r:CO_OCCURS]->()
        WHERE r.updated_at >= datetime() - duration({days: 7})
        RETURN count(r) as count
        """
        result = await neo4j.execute_query(query_co_occurs)
        co_occurs_count = result[0]["count"] if result else 0

        # Check SAME_ACTOR relationships
        query_same_actor = """
        MATCH ()-[r:SAME_ACTOR]->()
        WHERE r.updated_at >= datetime() - duration({days: 7})
        RETURN count(r) as count
        """
        result = await neo4j.execute_query(query_same_actor)
        same_actor_count = result[0]["count"] if result else 0

        logger.info(f"  CO_OCCURS edges (last 7d): {co_occurs_count}")
        logger.info(f"  SAME_ACTOR edges (last 7d): {same_actor_count}")

        if co_occurs_count == 0 and same_actor_count == 0:
            logger.warning(
                "  ⚠ No recent Neo4j relationships - run neo4j_cluster_prep.py"
            )
            all_passed = False
        else:
            logger.info("  ✓ Neo4j relationships exist")

    except Exception as e:
        logger.error(f"✗ Failed to check Neo4j: {e}")
        all_passed = False

    # Check 3: Titles with AAT data
    logger.info("\nCheck 3: Titles with AAT data")
    with get_db_session() as session:
        try:
            # Count total unassigned strategic titles
            total_query = """
            SELECT COUNT(*)
            FROM titles
            WHERE gate_keep = true AND event_id IS NULL
            """
            total_count = session.execute(text(total_query)).scalar()

            # Count titles with AAT data
            aat_query = """
            SELECT COUNT(*)
            FROM titles
            WHERE gate_keep = true
              AND event_id IS NULL
              AND action_triple IS NOT NULL
            """
            aat_count = session.execute(text(aat_query)).scalar()

            # Count titles with entities
            entities_query = """
            SELECT COUNT(*)
            FROM titles
            WHERE gate_keep = true
              AND event_id IS NULL
              AND entities IS NOT NULL
              AND array_length(entities, 1) > 0
            """
            entities_count = session.execute(text(entities_query)).scalar()

            logger.info(f"  Total unassigned strategic titles: {total_count}")
            logger.info(f"  Titles with AAT data: {aat_count} ({aat_count/total_count*100:.1f}%)")
            logger.info(
                f"  Titles with entities: {entities_count} ({entities_count/total_count*100:.1f}%)"
            )

            if total_count == 0:
                logger.warning("  ⚠ No unassigned strategic titles found")
                all_passed = False
            elif aat_count == 0:
                logger.warning(
                    "  ⚠ No AAT data found - Phase 2 may not have run with AAT extraction"
                )
            else:
                logger.info("  ✓ Titles ready for clustering")

        except Exception as e:
            logger.error(f"✗ Failed to check titles: {e}")
            all_passed = False

    # Summary
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("✓ All checks passed - P3_v1 is ready to run!")
        logger.info("\nRun: python run_p3_v1.py 50")
    else:
        logger.warning("⚠ Some checks failed - see messages above")
        logger.info("\nSetup steps:")
        logger.info("1. Run migration: psql -f db/migrations/20251029_add_title_connectivity_cache.sql")
        logger.info("2. Build Neo4j relationships: python neo4j_cluster_prep.py")
        logger.info("3. Sync cache: python connectivity_cache.py")
        logger.info("4. Validate again: python validate_p3v1_setup.py")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(validate_setup())
    sys.exit(0 if result else 1)
