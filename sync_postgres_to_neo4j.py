#!/usr/bin/env python3
"""
Full sync from PostgreSQL to Neo4j
Reads all titles and syncs them to Neo4j graph database
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger  # noqa: E402
from sqlalchemy import text  # noqa: E402

from core.database import get_db_session  # noqa: E402
from core.neo4j_sync import get_neo4j_sync  # noqa: E402


async def clear_neo4j():
    """Clear all data from Neo4j"""
    logger.info("Clearing Neo4j database...")
    neo4j_sync = get_neo4j_sync()

    async with neo4j_sync.driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")

    logger.info("Neo4j cleared")


async def sync_all_titles():
    """Sync all titles from PostgreSQL to Neo4j"""

    # Clear Neo4j first
    await clear_neo4j()

    # Read all titles from PostgreSQL
    with get_db_session() as db_session:
        result = db_session.execute(text("""
            SELECT id, title_display, pubdate_utc, gate_keep,
                   detected_language, entities
            FROM titles
            ORDER BY ingested_at DESC
        """))

        titles = result.fetchall()
        total = len(titles)
        logger.info(f"Found {total} titles to sync")

    # Sync to Neo4j
    neo4j_sync = get_neo4j_sync()
    synced = 0
    failed = 0

    for i, title_row in enumerate(titles, 1):
        # Convert entities array of strings to Neo4j format
        entities_array = title_row[5] or []
        entity_list = [{"text": actor, "type": "ACTOR"} for actor in entities_array]

        title_data = {
            "id": str(title_row[0]),
            "title_display": title_row[1],
            "pubdate_utc": title_row[2],
            "gate_keep": title_row[3] or False,
            "detected_language": title_row[4],
            "entities": entity_list,
        }

        try:
            await neo4j_sync.sync_title(title_data)
            synced += 1

            if i % 1000 == 0:
                logger.info(f"Progress: {i}/{total} ({synced} synced, {failed} failed)")
        except Exception as e:
            failed += 1
            logger.warning(f"Failed to sync title {title_data['id']}: {e}")

    logger.info(f"Sync complete: {synced} synced, {failed} failed out of {total} total")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("FULL POSTGRESQL -> NEO4J SYNC")
    logger.info("=" * 60)

    asyncio.run(sync_all_titles())

    logger.info("=" * 60)
    logger.info("SYNC COMPLETE")
    logger.info("=" * 60)
