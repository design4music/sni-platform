"""
Neo4j Cluster Preparation
Precomputes CO_OCCURS and SAME_ACTOR relationships for mechanical clustering

Run: Nightly/hourly to keep relationships fresh
Output: Neo4j edges that power hybrid clustering
"""

import asyncio
from typing import Dict, List, Tuple

from loguru import logger

from core.neo4j_sync import get_neo4j_sync


class Neo4jClusterPrep:
    """Builds Neo4j relationships for incident clustering"""

    def __init__(self):
        self.neo4j = get_neo4j_sync()

    async def _execute_query(self, query: str, params: dict = None):
        """Execute Neo4j query and return results"""
        async with self.neo4j.driver.session() as session:
            result = await session.run(query, **(params or {}))
            records = await result.data()
            return records

    async def build_co_occurs_relationships(self) -> Dict[str, int]:
        """
        Build CO_OCCURS edges between titles sharing entities

        Creates edges with similarity score based on entity overlap
        """
        logger.info("Building CO_OCCURS relationships in Neo4j...")

        query = """
        // Find titles sharing 2+ entities
        MATCH (t1:Title)-[:HAS_ENTITY]->(e:Entity)<-[:HAS_ENTITY]-(t2:Title)
        WHERE t1.gate_keep = true
          AND t2.gate_keep = true
          AND t1.event_id IS NULL
          AND t2.event_id IS NULL
          AND t1.id < t2.id
        WITH t1, t2,
             count(DISTINCT e) as shared_count,
             collect(DISTINCT e.name) as shared_entities
        WHERE shared_count >= 2

        // Calculate Jaccard similarity
        MATCH (t1)-[:HAS_ENTITY]->(e1:Entity)
        WITH t1, t2, shared_count, shared_entities, collect(DISTINCT e1.name) as t1_entities
        MATCH (t2)-[:HAS_ENTITY]->(e2:Entity)
        WITH t1, t2, shared_count, shared_entities, t1_entities, collect(DISTINCT e2.name) as t2_entities
        WITH t1, t2, shared_count, shared_entities,
             CASE WHEN (size(t1_entities) + size(t2_entities) - shared_count) > 0
                  THEN shared_count * 1.0 / (size(t1_entities) + size(t2_entities) - shared_count)
                  ELSE 0.0
             END as jaccard_sim

        // Create/update CO_OCCURS relationship
        MERGE (t1)-[r:CO_OCCURS]-(t2)
        SET r.shared_count = shared_count,
            r.shared_entities = shared_entities,
            r.jaccard_similarity = jaccard_sim,
            r.updated_at = datetime()

        RETURN count(r) as edges_created
        """

        result = await self._execute_query(query)
        edges_created = result[0]["edges_created"] if result else 0

        logger.info(f"Created {edges_created} CO_OCCURS edges")
        return {"co_occurs_edges": edges_created}

    async def build_same_actor_relationships(self) -> Dict[str, int]:
        """
        Build SAME_ACTOR edges between titles with matching AAT actors

        Uses fuzzy matching to handle variations (Russia vs Russian Federation)
        """
        logger.info("Building SAME_ACTOR relationships in Neo4j...")

        # First, get all titles with AAT actors (via HAS_ACTION relationships)
        get_actors_query = """
        MATCH (t:Title)-[r:HAS_ACTION]->(actor:Entity)
        WHERE t.gate_keep = true
          AND t.event_id IS NULL
          AND r.actor_role = 'actor'
        RETURN t.id as title_id,
               toLower(actor.name) as actor
        """

        titles_with_actors = await self._execute_query(get_actors_query)

        if not titles_with_actors:
            logger.warning("No titles with AAT actors found")
            return {"same_actor_edges": 0}

        # Group by actor (case-insensitive)
        from collections import defaultdict

        actor_groups = defaultdict(list)
        for record in titles_with_actors:
            actor = record["actor"]
            title_id = record["title_id"]
            actor_groups[actor].append(title_id)

        # Create edges for titles sharing same actor
        edges_created = 0
        for actor, title_ids in actor_groups.items():
            if len(title_ids) < 2:
                continue

            # Create pairwise edges
            for i, t1_id in enumerate(title_ids):
                for t2_id in title_ids[i + 1 :]:
                    edge_query = """
                    MATCH (t1:Title {id: $t1_id})
                    MATCH (t2:Title {id: $t2_id})
                    MERGE (t1)-[r:SAME_ACTOR]-(t2)
                    SET r.actor = $actor,
                        r.updated_at = datetime()
                    RETURN count(r) as created
                    """

                    result = await self._execute_query(
                        edge_query, {"t1_id": t1_id, "t2_id": t2_id, "actor": actor}
                    )
                    edges_created += result[0]["created"] if result else 0

        logger.info(f"Created {edges_created} SAME_ACTOR edges")
        return {"same_actor_edges": edges_created}

    async def cleanup_old_relationships(self, days_old: int = 7) -> Dict[str, int]:
        """
        Remove stale relationships for titles already assigned to events

        Args:
            days_old: Remove relationships older than this many days
        """
        logger.info(f"Cleaning up relationships older than {days_old} days...")

        cleanup_query = """
        MATCH (t1:Title)-[r:CO_OCCURS|SAME_ACTOR]-(t2:Title)
        WHERE t1.event_id IS NOT NULL
           OR t2.event_id IS NOT NULL
           OR duration.between(r.updated_at, datetime()).days > $days_old
        DELETE r
        RETURN count(r) as deleted
        """

        result = await self._execute_query(cleanup_query, {"days_old": days_old})
        deleted = result[0]["deleted"] if result else 0

        logger.info(f"Deleted {deleted} stale relationships")
        return {"deleted": deleted}

    async def get_connectivity_statistics(self) -> Dict[str, any]:
        """Get statistics about cluster relationships"""

        stats_query = """
        MATCH (t:Title)
        WHERE t.gate_keep = true AND t.event_id IS NULL
        WITH count(t) as total_unassigned

        MATCH (t1:Title)-[r:CO_OCCURS]-(t2:Title)
        WHERE t1.event_id IS NULL
        WITH total_unassigned, count(DISTINCT r) as co_occurs_count

        MATCH (t1:Title)-[r:SAME_ACTOR]-(t2:Title)
        WHERE t1.event_id IS NULL
        WITH total_unassigned, co_occurs_count, count(DISTINCT r) as same_actor_count

        RETURN total_unassigned,
               co_occurs_count,
               same_actor_count
        """

        result = await self._execute_query(stats_query)
        if result:
            return {
                "unassigned_titles": result[0]["total_unassigned"],
                "co_occurs_edges": result[0]["co_occurs_count"],
                "same_actor_edges": result[0]["same_actor_count"],
            }
        return {}

    async def run_full_prep(self) -> Dict[str, any]:
        """
        Run complete Neo4j preparation pipeline

        1. Cleanup old relationships
        2. Build CO_OCCURS edges
        3. Build SAME_ACTOR edges
        4. Return statistics
        """
        logger.info("=== STARTING NEO4J CLUSTER PREP ===")

        results = {}

        # Step 1: Cleanup
        results["cleanup"] = await self.cleanup_old_relationships()

        # Step 2: Build CO_OCCURS
        results["co_occurs"] = await self.build_co_occurs_relationships()

        # Step 3: Build SAME_ACTOR
        results["same_actor"] = await self.build_same_actor_relationships()

        # Step 4: Statistics
        results["stats"] = await self.get_connectivity_statistics()

        logger.info("=== NEO4J CLUSTER PREP COMPLETE ===")
        logger.info(f"Statistics: {results['stats']}")

        return results


async def main():
    """Run Neo4j cluster preparation"""
    prep = Neo4jClusterPrep()
    results = await prep.run_full_prep()

    # Print summary
    print("\n=== Neo4j Cluster Prep Results ===")
    print(f"Unassigned titles: {results['stats'].get('unassigned_titles', 0)}")
    print(f"CO_OCCURS edges: {results['stats'].get('co_occurs_edges', 0)}")
    print(f"SAME_ACTOR edges: {results['stats'].get('same_actor_edges', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
