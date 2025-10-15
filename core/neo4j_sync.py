"""
Neo4j sync service for Strategic Narrative Intelligence

Provides async sync of titles and entities from PostgreSQL to Neo4j graph database.
Used to enhance clustering and strategic filtering through relationship analysis.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from loguru import logger
from neo4j import AsyncGraphDatabase


class Neo4jSync:
    """
    Async service for syncing title and entity data to Neo4j graph database.

    Used to build a graph of titles connected by shared entities, enabling:
    - P2: Strategic filtering enhancement (borderline cases)
    - P3: Cluster expansion (find related titles via shared entities)
    - P4: Enrichment context (understand entity relationships)
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: Optional[str] = None,
    ):
        """
        Initialize Neo4j sync service.

        Args:
            uri: Neo4j Bolt URI
            user: Neo4j username
            password: Neo4j password (defaults to env var NEO4J_PASSWORD)
        """
        self.uri = uri
        self.user = user
        self.password = password or os.getenv("NEO4J_PASSWORD", "sni_password_2024")
        self.driver = AsyncGraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )
        logger.info(f"Neo4j sync service initialized: {self.uri}")

    async def close(self):
        """Close Neo4j driver connection"""
        await self.driver.close()
        logger.info("Neo4j sync service closed")

    async def test_connection(self) -> bool:
        """
        Test Neo4j connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 'Neo4j is connected!' AS message")
                record = await result.single()
                logger.info(f"Neo4j connection test: {record['message']}")
                return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False

    async def sync_title(self, title_data: Dict[str, Any]) -> bool:
        """
        Sync a single title to Neo4j.

        Creates/updates a Title node and connects it to Entity nodes based on
        the entities detected in the title.

        Args:
            title_data: Dictionary with title information:
                - id: Title UUID
                - title_display: Display title text
                - pubdate_utc: Publication datetime
                - gate_keep: Boolean, passed strategic filter
                - detected_language: Language code
                - entities: List of dicts with 'text' and 'type' keys

        Returns:
            True if sync successful, False otherwise
        """
        query = """
        MERGE (t:Title {id: $id})
        SET t.title = $title,
            t.pubdate = datetime($pubdate),
            t.gate_keep = $gate_keep,
            t.detected_language = $language

        WITH t
        UNWIND $entities AS entity
        MERGE (e:Entity {id: entity.text + "|" + entity.type})
        SET e.name = entity.text,
            e.type = entity.type
        MERGE (t)-[:HAS_ENTITY]->(e)
        """

        try:
            async with self.driver.session() as session:
                await session.run(
                    query,
                    id=str(title_data["id"]),
                    title=title_data.get("title_display", ""),
                    pubdate=(
                        title_data["pubdate_utc"].isoformat()
                        if title_data.get("pubdate_utc")
                        else None
                    ),
                    gate_keep=title_data.get("gate_keep", False),
                    language=title_data.get("detected_language", "en"),
                    entities=title_data.get("entities", []),
                )
                logger.debug(
                    f"Synced title to Neo4j: {title_data.get('id')} with {len(title_data.get('entities', []))} entities"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to sync title {title_data.get('id')} to Neo4j: {e}")
            return False

    async def find_strategic_neighbors(
        self, title_id: str, threshold: int = 2, days_lookback: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find strategic titles that share entities with the given title.

        Used for P2 strategic filtering enhancement - if a borderline title
        shares multiple entities with recent strategic content, it may be
        strategic itself.

        Args:
            title_id: Title UUID to find neighbors for
            threshold: Minimum number of shared entities
            days_lookback: How many days back to look for strategic titles

        Returns:
            List of neighbor dicts with:
                - neighbor_id: Strategic title UUID
                - neighbor_title: Title text
                - shared_entities: Count of shared entities
                - shared_entity_names: List of shared entity names
        """
        query = """
        MATCH (target:Title {id: $title_id})-[:HAS_ENTITY]->(e:Entity)
        MATCH (strategic:Title {gate_keep: true})-[:HAS_ENTITY]->(e)
        WHERE strategic.id <> $title_id
          AND strategic.pubdate >= datetime() - duration({days: $days_lookback})

        WITH target, strategic, COUNT(e) AS shared_entities, COLLECT(e.name) AS shared_names
        WHERE shared_entities >= $threshold

        RETURN strategic.id AS neighbor_id,
               strategic.title AS neighbor_title,
               shared_entities,
               shared_names AS shared_entity_names
        ORDER BY shared_entities DESC
        LIMIT 3
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    title_id=title_id,
                    threshold=threshold,
                    days_lookback=days_lookback,
                )
                neighbors = await result.data()
                logger.debug(
                    f"Found {len(neighbors)} strategic neighbors for title {title_id}"
                )
                return neighbors

        except Exception as e:
            logger.error(f"Failed to find strategic neighbors for {title_id}: {e}")
            return []

    async def expand_cluster(
        self,
        title_ids: List[str],
        min_shared_entities: int = 2,
        days_lookback: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Find additional titles that belong to the same cluster.

        Used for P3 clustering - expands clusters by finding titles that share
        multiple entities with the cluster members but weren't initially included.

        Args:
            title_ids: List of title UUIDs in the cluster
            min_shared_entities: Minimum shared entities to be considered
            days_lookback: How many days back to look for candidates

        Returns:
            List of candidate dicts with:
                - title_id: Candidate title UUID
                - title: Title text
                - shared_count: Number of shared entities with cluster
        """
        query = """
        MATCH (cluster:Title)-[:HAS_ENTITY]->(e:Entity)
        WHERE cluster.id IN $title_ids
        WITH COLLECT(DISTINCT e) AS cluster_entities

        MATCH (candidate:Title)-[:HAS_ENTITY]->(e:Entity)
        WHERE NOT candidate.id IN $title_ids
          AND e IN cluster_entities
          AND candidate.gate_keep = true
          AND candidate.pubdate >= datetime() - duration({days: $days_lookback})

        WITH candidate, COUNT(e) AS shared_count
        WHERE shared_count >= $min_shared_entities

        RETURN candidate.id AS title_id,
               candidate.title AS title,
               shared_count
        ORDER BY shared_count DESC
        """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    title_ids=title_ids,
                    min_shared_entities=min_shared_entities,
                    days_lookback=days_lookback,
                )
                candidates = await result.data()
                logger.debug(
                    f"Found {len(candidates)} cluster expansion candidates for {len(title_ids)} titles"
                )
                return candidates

        except Exception as e:
            logger.error(f"Failed to expand cluster: {e}")
            return []


# Singleton instance for use across the application
neo4j_sync: Optional[Neo4jSync] = None


def get_neo4j_sync() -> Neo4jSync:
    """
    Get singleton Neo4j sync instance.

    Lazily initializes the service on first call.

    Returns:
        Neo4jSync instance
    """
    global neo4j_sync
    if neo4j_sync is None:
        neo4j_sync = Neo4jSync()
    return neo4j_sync


async def close_neo4j_sync():
    """Close the singleton Neo4j sync instance if it exists"""
    global neo4j_sync
    if neo4j_sync is not None:
        await neo4j_sync.close()
        neo4j_sync = None


def sync_title_to_neo4j(title_data: Dict[str, Any]) -> bool:
    """
    Synchronous wrapper for syncing a title to Neo4j.

    This is a best-effort sync - failures are logged but don't raise exceptions.
    Designed to be called from synchronous P1 ingestion code without blocking.

    Args:
        title_data: Dictionary with title information (same as async sync_title)

    Returns:
        True if sync successful, False if failed or Neo4j unavailable
    """
    try:
        sync_service = get_neo4j_sync()
        # Run async function in sync context
        result = asyncio.run(sync_service.sync_title(title_data))
        return result
    except Exception as e:
        # Log but don't propagate - Neo4j sync is optional enhancement
        logger.warning(f"Neo4j sync failed for title {title_data.get('id')}: {e}")
        return False
