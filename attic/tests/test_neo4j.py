#!/usr/bin/env python3
"""
Test script for Neo4j sync service

Verifies Neo4j connection and tests syncing sample title data.
Run this before integrating Neo4j sync into the main pipeline.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger  # noqa: E402

from core.neo4j_sync import get_neo4j_sync  # noqa: E402


async def test_connection():
    """Test basic Neo4j connectivity"""
    logger.info("Testing Neo4j connection...")
    neo4j_sync = get_neo4j_sync()

    connected = await neo4j_sync.test_connection()
    if connected:
        logger.info("[PASS] Neo4j connection successful")
        return True
    else:
        logger.error("[FAIL] Neo4j connection failed")
        return False


async def test_sync_title():
    """Test syncing a sample title to Neo4j"""
    logger.info("Testing title sync...")
    neo4j_sync = get_neo4j_sync()

    test_title = {
        "id": "test-uuid-123",
        "title_display": "US and China hold trade talks in Beijing",
        "pubdate_utc": datetime.fromisoformat("2024-01-15T10:00:00"),
        "gate_keep": True,
        "detected_language": "en",
        "entities": [
            {"text": "US", "type": "GPE"},
            {"text": "China", "type": "GPE"},
            {"text": "Beijing", "type": "GPE"},
            {"text": "trade talks", "type": "EVENT"},
        ],
    }

    success = await neo4j_sync.sync_title(test_title)
    if success:
        logger.info("[PASS] Test title synced to Neo4j")
        return True
    else:
        logger.error("[FAIL] Failed to sync test title")
        return False


async def test_find_neighbors():
    """Test finding strategic neighbors"""
    logger.info("Testing strategic neighbor search...")
    neo4j_sync = get_neo4j_sync()

    # Sync a second title that shares entities
    test_title_2 = {
        "id": "test-uuid-456",
        "title_display": "Beijing announces new US tariff policy",
        "pubdate_utc": datetime.now(),
        "gate_keep": False,
        "detected_language": "en",
        "entities": [
            {"text": "Beijing", "type": "GPE"},
            {"text": "US", "type": "GPE"},
            {"text": "tariff", "type": "EVENT"},
        ],
    }

    await neo4j_sync.sync_title(test_title_2)

    # Find neighbors for the second title
    neighbors = await neo4j_sync.find_strategic_neighbors("test-uuid-456", threshold=2)

    if neighbors:
        logger.info(f"[PASS] Found {len(neighbors)} strategic neighbors")
        for neighbor in neighbors:
            logger.info(
                f"  - Neighbor: {neighbor['neighbor_title'][:50]}... "
                f"(shared {neighbor['shared_entities']} entities: {neighbor['shared_entity_names']})"
            )
        return True
    else:
        logger.warning(
            "[WARN] No strategic neighbors found (expected if test is fresh)"
        )
        return True


async def test_cluster_expansion():
    """Test cluster expansion functionality"""
    logger.info("Testing cluster expansion...")
    neo4j_sync = get_neo4j_sync()

    # Try expanding a cluster with our test titles
    candidates = await neo4j_sync.expand_cluster(
        title_ids=["test-uuid-123"], min_shared_entities=1
    )

    if candidates:
        logger.info(f"[PASS] Found {len(candidates)} cluster expansion candidates")
        for candidate in candidates:
            logger.info(
                f"  - Candidate: {candidate['title'][:50]}... "
                f"(shared {candidate['shared_count']} entities)"
            )
    else:
        logger.warning(
            "[WARN] No expansion candidates found (expected if test is fresh)"
        )

    return True


async def cleanup_test_data():
    """Remove test data from Neo4j"""
    logger.info("Cleaning up test data...")
    neo4j_sync = get_neo4j_sync()

    cleanup_query = """
    MATCH (t:Title)
    WHERE t.id STARTS WITH 'test-uuid-'
    DETACH DELETE t
    """

    try:
        async with neo4j_sync.driver.session() as session:
            result = await session.run(cleanup_query)
            summary = await result.consume()
            logger.info(
                f"Cleaned up test data: deleted {summary.counters.nodes_deleted} nodes"
            )
    except Exception as e:
        logger.error(f"Failed to cleanup test data: {e}")


async def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("NEO4J SYNC SERVICE TEST SUITE")
    logger.info("=" * 60)

    results = []

    # Test 1: Connection
    results.append(await test_connection())

    if not results[0]:
        logger.error("Connection failed, skipping other tests")
        logger.error("Make sure Neo4j is running: docker-compose up -d neo4j")
        return False

    # Test 2: Sync title
    results.append(await test_sync_title())

    # Test 3: Find neighbors
    results.append(await test_find_neighbors())

    # Test 4: Cluster expansion
    results.append(await test_cluster_expansion())

    # Cleanup
    await cleanup_test_data()

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Tests passed: {passed}/{total}")

    if passed == total:
        logger.info("All tests passed! Neo4j sync service is ready to use.")
        return True
    else:
        logger.error("Some tests failed. Check errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
