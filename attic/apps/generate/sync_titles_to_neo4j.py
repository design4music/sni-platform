"""
Batch sync titles from Postgres to Neo4j

Syncs all strategic titles with their entities and AAT triples to Neo4j.
Run this before neo4j_cluster_prep.py to populate the graph.
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


async def batch_sync_titles_to_neo4j(limit: int = None):
    """
    Batch sync strategic titles from Postgres to Neo4j

    Args:
        limit: Maximum number of titles to sync (None for all)
    """
    logger.info("=== BATCH SYNC: Postgres → Neo4j ===")

    neo4j = get_neo4j_sync()

    # Test connection
    connected = await neo4j.test_connection()
    if not connected:
        logger.error("Neo4j connection failed - cannot proceed")
        return

    # Fetch titles from Postgres
    logger.info("Fetching strategic titles from Postgres...")
    with get_db_session() as session:
        query = """
        SELECT
            id,
            title_display,
            pubdate_utc,
            gate_keep,
            detected_language,
            entities,
            action_triple,
            event_id
        FROM titles
        WHERE gate_keep = true
        ORDER BY pubdate_utc DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        results = session.execute(text(query)).fetchall()

        logger.info(f"Found {len(results)} strategic titles to sync")

        # Sync titles to Neo4j
        success_count = 0
        aat_count = 0
        errors = 0

        for i, row in enumerate(results):
            try:
                # Prepare title data
                title_data = {
                    "id": str(row.id),
                    "title_display": row.title_display,
                    "pubdate_utc": row.pubdate_utc,
                    "gate_keep": row.gate_keep,
                    "detected_language": row.detected_language or "en",
                    "entities": [
                        {"text": entity, "type": "UNKNOWN"} for entity in (row.entities or [])
                    ],
                }

                # Sync title + entities
                success = await neo4j.sync_title(title_data)
                if success:
                    success_count += 1
                else:
                    errors += 1

                # Sync AAT triple if present
                if row.action_triple:
                    aat_success = await neo4j.sync_aat_triple(
                        str(row.id), row.action_triple
                    )
                    if aat_success:
                        aat_count += 1

                # Sync event_id property (for neo4j_cluster_prep queries)
                if row.event_id:
                    await _set_event_id(neo4j, str(row.id), str(row.event_id))

                # Progress logging
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i + 1}/{len(results)} titles synced")

            except Exception as e:
                logger.error(f"Failed to sync title {row.id}: {e}")
                errors += 1

    logger.info("\n=== Batch Sync Complete ===")
    logger.info(f"Titles synced: {success_count}/{len(results)}")
    logger.info(f"AAT triples synced: {aat_count}")
    logger.info(f"Errors: {errors}")


async def _set_event_id(neo4j, title_id: str, event_id: str):
    """Set event_id property on Title node"""
    try:
        async with neo4j.driver.session() as session:
            query = """
            MATCH (t:Title {id: $title_id})
            SET t.event_id = $event_id
            """
            await session.run(query, title_id=title_id, event_id=event_id)
    except Exception as e:
        logger.debug(f"Failed to set event_id for {title_id}: {e}")


async def main():
    """Run batch sync"""
    import argparse

    parser = argparse.ArgumentParser(description="Sync titles from Postgres to Neo4j")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of titles to sync (default: all)",
    )

    args = parser.parse_args()

    await batch_sync_titles_to_neo4j(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
