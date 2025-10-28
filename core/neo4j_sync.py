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

    async def sync_aat_triple(self, title_id: str, aat_triple: Dict[str, str]) -> bool:
        """
        Sync Actor-Action-Target triple to Neo4j graph.

        Creates HAS_ACTION relationships between Title and Entity nodes based on
        the AAT triple extracted from the title. Enables graph-pattern clustering
        by action relationships (e.g., "who sanctioned whom").

        Args:
            title_id: Title UUID
            aat_triple: Dict with "actor", "action", "target" keys (values can be None)

        Returns:
            True if sync successful, False otherwise
        """
        if not aat_triple:
            return True

        actor = aat_triple.get("actor")
        action = aat_triple.get("action")
        target = aat_triple.get("target")

        # Only create relationships if we have action + at least one entity
        if not action or (not actor and not target):
            logger.debug(
                f"Skipping AAT sync for {title_id}: insufficient data (action={action}, actor={actor}, target={target})"
            )
            return True

        try:
            async with self.driver.session() as session:
                # Sync actor relationship if present
                if actor:
                    actor_query = """
                    MERGE (actor:Entity {name: $actor})
                    MERGE (t:Title {id: $title_id})
                    MERGE (t)-[:HAS_ACTION {action: $action, actor_role: 'actor'}]->(actor)
                    """
                    await session.run(
                        actor_query, title_id=title_id, actor=actor, action=action
                    )

                # Sync target relationship if present
                if target:
                    target_query = """
                    MERGE (target:Entity {name: $target})
                    MERGE (t:Title {id: $title_id})
                    MERGE (t)-[:HAS_ACTION {action: $action, actor_role: 'target'}]->(target)
                    """
                    await session.run(
                        target_query, title_id=title_id, target=target, action=action
                    )

                logger.debug(
                    f"Synced AAT triple to Neo4j: {title_id} ({actor or 'N/A'}|{action}|{target or 'N/A'})"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to sync AAT triple for {title_id} to Neo4j: {e}")
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

    async def get_entity_centrality(
        self, title_id: str, min_strategic_mentions: int = 2, days_lookback: int = None
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        Find if title contains highly connected entities.

        Entity centrality measures how "hot" an entity is by counting how many
        strategic titles have mentioned it recently. An entity mentioned in many
        strategic stories is more significant than one mentioned only once.

        Args:
            title_id: Title UUID to analyze
            min_strategic_mentions: Minimum strategic mentions for entity to be "central"
            days_lookback: How many days back to count mentions (None = no time limit)

        Returns:
            Tuple of (count, list of high-centrality entity dicts):
                - entity: Entity name
                - type: Entity type
                - strategic_mentions: Count of strategic titles mentioning this entity
        """
        if days_lookback is not None:
            query = """
            MATCH (t:Title {id: $title_id})-[:HAS_ENTITY]->(e:Entity)

            // How many strategic titles mention this entity recently?
            MATCH (e)<-[:HAS_ENTITY]-(strategic:Title {gate_keep: true})
            WHERE strategic.pubdate >= datetime() - duration({days: $days_lookback})

            WITH e, COUNT(strategic) AS strategic_mentions
            WHERE strategic_mentions >= $min_strategic_mentions

            RETURN collect({
                entity: e.name,
                type: e.type,
                strategic_mentions: strategic_mentions
            }) AS high_centrality_entities
            """
        else:
            query = """
            MATCH (t:Title {id: $title_id})-[:HAS_ENTITY]->(e:Entity)

            // How many strategic titles mention this entity (all time)?
            MATCH (e)<-[:HAS_ENTITY]-(strategic:Title {gate_keep: true})

            WITH e, COUNT(strategic) AS strategic_mentions
            WHERE strategic_mentions >= $min_strategic_mentions

            RETURN collect({
                entity: e.name,
                type: e.type,
                strategic_mentions: strategic_mentions
            }) AS high_centrality_entities
            """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    title_id=title_id,
                    min_strategic_mentions=min_strategic_mentions,
                    days_lookback=days_lookback,
                )
                data = await result.single()
                entities = data["high_centrality_entities"] if data else []
                logger.debug(
                    f"Found {len(entities)} high-centrality entities for title {title_id}"
                )
                return len(entities), entities

        except Exception as e:
            logger.error(f"Failed to get entity centrality for {title_id}: {e}")
            return 0, []

    async def get_strategic_neighborhood(
        self, title_id: str, days_lookback: int = None
    ) -> Dict[str, float]:
        """
        Measure how embedded this title is in strategic content networks.

        Strategic neighborhood strength is calculated as the ratio of strategic
        neighbors to the title's entity count. A high ratio means the title is
        densely connected to strategic content even with few entities.

        Args:
            title_id: Title UUID to analyze
            days_lookback: How many days back to look for strategic neighbors (None = no time limit)

        Returns:
            Dict with:
                - strategic_neighbors: Count of strategic titles sharing entities
                - strategic_neighbor_strength: Neighborhood density ratio (0-1+)
        """
        if days_lookback is not None:
            query = """
            MATCH (target:Title {id: $title_id})

            // Find strategic titles connected through ANY shared entity
            MATCH (target)-[:HAS_ENTITY]->(e:Entity)<-[:HAS_ENTITY]-(strategic:Title {gate_keep: true})
            WHERE strategic.pubdate >= datetime() - duration({days: $days_lookback})

            WITH target, COUNT(DISTINCT strategic) AS strategic_neighbors

            // Also check entity overlap strength
            MATCH (target)-[:HAS_ENTITY]->(te:Entity)
            WITH target, strategic_neighbors, COUNT(te) AS target_entity_count

            // Calculate neighborhood density
            RETURN strategic_neighbors,
                   CASE WHEN target_entity_count > 0
                        THEN strategic_neighbors * 1.0 / target_entity_count
                        ELSE 0
                   END AS neighbor_density
            """
        else:
            query = """
            MATCH (target:Title {id: $title_id})

            // Find strategic titles connected through ANY shared entity (all time)
            MATCH (target)-[:HAS_ENTITY]->(e:Entity)<-[:HAS_ENTITY]-(strategic:Title {gate_keep: true})

            WITH target, COUNT(DISTINCT strategic) AS strategic_neighbors

            // Also check entity overlap strength
            MATCH (target)-[:HAS_ENTITY]->(te:Entity)
            WITH target, strategic_neighbors, COUNT(te) AS target_entity_count

            // Calculate neighborhood density
            RETURN strategic_neighbors,
                   CASE WHEN target_entity_count > 0
                        THEN strategic_neighbors * 1.0 / target_entity_count
                        ELSE 0
                   END AS neighbor_density
            """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    query, title_id=title_id, days_lookback=days_lookback
                )
                data = await result.single()
                if data:
                    neighborhood = {
                        "strategic_neighbors": data["strategic_neighbors"],
                        "strategic_neighbor_strength": data["neighbor_density"],
                    }
                    logger.debug(
                        f"Strategic neighborhood for {title_id}: {neighborhood['strategic_neighbors']} neighbors, "
                        f"strength {neighborhood['strategic_neighbor_strength']:.2f}"
                    )
                    return neighborhood
                return {"strategic_neighbors": 0, "strategic_neighbor_strength": 0}

        except Exception as e:
            logger.error(f"Failed to get strategic neighborhood for {title_id}: {e}")
            return {"strategic_neighbors": 0, "strategic_neighbor_strength": 0}

    async def check_ongoing_event(
        self, title_id: str, min_sequence_length: int = 3, days_lookback: int = None
    ) -> bool:
        """
        Check if this title fits into an ongoing event pattern.

        Ongoing events are detected by finding entities that appear in multiple
        strategic titles over a time sequence, forming a temporal story pattern.

        Args:
            title_id: Title UUID to analyze
            min_sequence_length: Minimum number of mentions to form a sequence
            days_lookback: How many days back to look for event patterns (None = no time limit)

        Returns:
            True if title is part of an ongoing event, False otherwise
        """
        if days_lookback is not None:
            query = """
            MATCH (target:Title {id: $title_id})-[:HAS_ENTITY]->(e:Entity)

            // Look for event progression patterns
            MATCH (e)<-[:HAS_ENTITY]-(recent:Title {gate_keep: true})
            WHERE recent.pubdate >= datetime() - duration({days: $days_lookback})
              AND recent.id <> $title_id

            WITH e, COUNT(recent) AS recent_mentions
            WHERE recent_mentions >= 2

            // Check if this forms a temporal sequence
            MATCH (e)<-[:HAS_ENTITY]-(sequence:Title {gate_keep: true})
            WHERE sequence.pubdate >= datetime() - duration({days: $days_lookback})
            WITH e, sequence
            ORDER BY sequence.pubdate
            WITH e, collect(sequence.pubdate) AS dates
            WHERE size(dates) >= $min_sequence_length

            RETURN count(e) AS ongoing_events
            """
        else:
            query = """
            MATCH (target:Title {id: $title_id})-[:HAS_ENTITY]->(e:Entity)

            // Look for event progression patterns (all time)
            MATCH (e)<-[:HAS_ENTITY]-(recent:Title {gate_keep: true})
            WHERE recent.id <> $title_id

            WITH e, COUNT(recent) AS recent_mentions
            WHERE recent_mentions >= 2

            // Check if this forms a temporal sequence
            MATCH (e)<-[:HAS_ENTITY]-(sequence:Title {gate_keep: true})
            WITH e, sequence
            ORDER BY sequence.pubdate
            WITH e, collect(sequence.pubdate) AS dates
            WHERE size(dates) >= $min_sequence_length

            RETURN count(e) AS ongoing_events
            """

        try:
            async with self.driver.session() as session:
                result = await session.run(
                    query,
                    title_id=title_id,
                    min_sequence_length=min_sequence_length,
                    days_lookback=days_lookback,
                )
                data = await result.single()
                is_ongoing = (data["ongoing_events"] > 0) if data else False
                logger.debug(
                    f"Ongoing event check for {title_id}: {'Yes' if is_ongoing else 'No'}"
                )
                return is_ongoing

        except Exception as e:
            logger.error(f"Failed to check ongoing event for {title_id}: {e}")
            return False

    async def analyze_strategic_signals(
        self,
        title_id: str,
        days_lookback_centrality: int = 3,
        days_lookback_neighborhood: int = 2,
        days_lookback_event: int = 7,
    ) -> Dict[str, Any]:
        """
        Combine multiple Neo4j intelligence signals for strategic filtering.

        This method aggregates entity centrality, neighborhood strength, and
        ongoing event detection into a single strategic score. Use this for
        P2 enhancement to catch borderline cases with sparse but significant entities.

        Args:
            title_id: Title UUID to analyze
            days_lookback_centrality: Days to look back for centrality (None = all time)
            days_lookback_neighborhood: Days to look back for neighborhood (None = all time)
            days_lookback_event: Days to look back for events (None = all time)

        Returns:
            Dict with:
                - high_centrality_entities: Count of hot entities
                - centrality_details: List of entity centrality data
                - strategic_neighbors: Count of connected strategic titles
                - strategic_neighbor_strength: Neighborhood density ratio
                - ongoing_event: Boolean, part of temporal event pattern
        """
        # Run all three signal queries in parallel
        centrality_task = self.get_entity_centrality(
            title_id, days_lookback=days_lookback_centrality
        )
        neighborhood_task = self.get_strategic_neighborhood(
            title_id, days_lookback=days_lookback_neighborhood
        )
        ongoing_task = self.check_ongoing_event(
            title_id, days_lookback=days_lookback_event
        )

        centrality_count, centrality_entities = await centrality_task
        neighborhood = await neighborhood_task
        ongoing_event = await ongoing_task

        signals = {
            "high_centrality_entities": centrality_count,
            "centrality_details": centrality_entities,
            "strategic_neighbors": neighborhood["strategic_neighbors"],
            "strategic_neighbor_strength": neighborhood["strategic_neighbor_strength"],
            "ongoing_event": ongoing_event,
        }

        logger.debug(
            f"Strategic signals for {title_id}: "
            f"centrality={centrality_count}, neighbors={neighborhood['strategic_neighbors']}, "
            f"ongoing={ongoing_event}"
        )

        return signals


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
