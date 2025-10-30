"""
Connectivity Cache Builder
Syncs Neo4j connectivity relationships to Postgres for fast lookup

Run: After neo4j_cluster_prep.py to populate cache
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger
from sqlalchemy import text

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402
from core.neo4j_sync import get_neo4j_sync  # noqa: E402


class ConnectivityCacheBuilder:
    """Syncs Neo4j connectivity to Postgres cache"""

    def __init__(self):
        self.neo4j = get_neo4j_sync()

    async def _execute_query(self, query: str, params: dict = None):
        """Execute Neo4j query and return results"""
        async with self.neo4j.driver.session() as session:
            result = await session.run(query, **(params or {}))
            records = await result.data()
            return records

    async def fetch_neo4j_connectivity(
        self, min_shared_entities: int = 2, limit: int = 50000
    ) -> List[Dict[str, any]]:
        """
        Fetch raw entity/actor overlap from Neo4j (minimal query)

        Just get counts - calculate scores in Python to avoid Neo4j memory issues

        Args:
            min_shared_entities: Minimum shared entities to consider (default 2)
            limit: Max pairs to fetch (default 50k)

        Returns:
            List of connectivity records with computed scores
        """
        logger.info(
            f"Fetching entity overlap from Neo4j (min {min_shared_entities} shared)..."
        )

        # Ultra-lightweight: just count shared entities
        query = """
        MATCH (t1:Title)-[:HAS_ENTITY]->(e:Entity)<-[:HAS_ENTITY]-(t2:Title)
        WHERE t1.gate_keep = true
          AND t2.gate_keep = true
          AND t1.event_id IS NULL
          AND t2.event_id IS NULL
          AND t1.id < t2.id
        WITH t1.id as title1_id, t2.id as title2_id, count(DISTINCT e) as shared_count
        WHERE shared_count >= $min_shared
        RETURN title1_id, title2_id, shared_count
        ORDER BY shared_count DESC
        LIMIT $limit
        """

        results = await self._execute_query(
            query, {"min_shared": min_shared_entities, "limit": limit}
        )

        logger.info(f"Fetched {len(results)} title pairs from Neo4j")

        # Now calculate scores in Python (memory-efficient)
        return await self._compute_scores_in_python(results)

    async def _compute_scores_in_python(
        self, neo4j_results: List[Dict]
    ) -> List[Dict[str, any]]:
        """
        Calculate connectivity scores in Python from Neo4j raw counts

        Fetches entity counts and AAT data from Postgres, computes Jaccard + actor scores
        """
        if not neo4j_results:
            return []

        logger.info("Computing scores in Python from Neo4j counts...")

        # Get unique title IDs
        title_ids = set()
        for record in neo4j_results:
            title_ids.add(record["title1_id"])
            title_ids.add(record["title2_id"])

        logger.info(f"Fetching data for {len(title_ids)} unique titles from Postgres...")

        # Fetch entity counts and AAT actors from Postgres
        with get_db_session() as session:
            # Build UUID array
            uuid_list_str = "ARRAY[" + ",".join([f"'{tid}'::uuid" for tid in title_ids]) + "]"

            query = f"""
            SELECT
                id,
                jsonb_array_length(entities) as entity_count,
                action_triple->>'actor' as actor
            FROM titles
            WHERE id = ANY({uuid_list_str})
            """

            rows = session.execute(text(query)).fetchall()

            # Build lookup dicts
            entity_counts = {}
            actors = {}
            for row in rows:
                tid = str(row.id)
                entity_counts[tid] = row.entity_count or 0
                if row.actor:
                    actors[tid] = row.actor.lower().strip()

        logger.info(f"Computing scores for {len(neo4j_results)} title pairs...")

        # Get valid title IDs (those that exist in Postgres)
        valid_title_ids = set(entity_counts.keys())
        logger.info(f"Valid title IDs from Postgres: {len(valid_title_ids)}")

        # Calculate scores
        scored_results = []
        skipped_count = 0
        for record in neo4j_results:
            t1_id = record["title1_id"]
            t2_id = record["title2_id"]
            shared_count = record["shared_count"]

            # Skip if either title doesn't exist in Postgres (deleted/orphaned)
            if t1_id not in valid_title_ids or t2_id not in valid_title_ids:
                skipped_count += 1
                continue

            t1_count = entity_counts.get(t1_id, 0)
            t2_count = entity_counts.get(t2_id, 0)

            # Jaccard similarity
            union_count = t1_count + t2_count - shared_count
            if union_count <= 0:
                co_occurs_score = 0.0
            else:
                co_occurs_score = min(1.0, shared_count / union_count)  # Cap at 1.0

            # Actor match
            t1_actor = actors.get(t1_id)
            t2_actor = actors.get(t2_id)
            same_actor_score = 0.0
            shared_actor = None

            if t1_actor and t2_actor:
                if t1_actor == t2_actor:
                    same_actor_score = 1.0
                    shared_actor = t1_actor
                elif t1_actor in t2_actor or t2_actor in t1_actor:
                    same_actor_score = 0.8
                    shared_actor = t1_actor  # Use first as representative

            # Total score: 50% entity + 20% actor
            total_score = (co_occurs_score * 0.5) + (same_actor_score * 0.2)

            # Only include if above threshold
            if total_score >= 0.3:
                # Ensure proper ordering (title_id_1 < title_id_2)
                if t1_id > t2_id:
                    t1_id, t2_id = t2_id, t1_id

                scored_results.append(
                    {
                        "title1_id": t1_id,
                        "title2_id": t2_id,
                        "co_occurs_score": co_occurs_score,
                        "same_actor_score": same_actor_score,
                        "total_score": total_score,
                        "shared_actor": shared_actor,
                    }
                )

        logger.info(
            f"Computed scores: {len(scored_results)} pairs above 0.3 threshold "
            f"(skipped {skipped_count} pairs with deleted titles)"
        )
        return scored_results

    async def sync_to_postgres(
        self, connectivity_records: List[Dict[str, any]]
    ) -> Dict[str, int]:
        """
        Sync connectivity records to Postgres cache

        Strategy: Clear cache and rebuild (simple, ensures consistency)
        """
        if not connectivity_records:
            logger.warning("No connectivity records to sync")
            return {"inserted": 0, "deleted": 0}

        logger.info(f"Syncing {len(connectivity_records)} records to Postgres cache...")

        with get_db_session() as session:
            # Step 1: Clear existing cache for unassigned titles
            delete_query = """
            DELETE FROM title_connectivity_cache
            WHERE title_id_1 IN (SELECT id FROM titles WHERE event_id IS NULL)
               OR title_id_2 IN (SELECT id FROM titles WHERE event_id IS NULL)
            """
            delete_result = session.execute(text(delete_query))
            deleted_count = delete_result.rowcount

            logger.info(f"Deleted {deleted_count} old cache entries")

            # Step 2: Bulk insert new records
            insert_query = """
            INSERT INTO title_connectivity_cache
                (title_id_1, title_id_2, co_occurs_score, same_actor_score,
                 total_score, shared_actor, updated_at)
            VALUES
                (:title_id_1, :title_id_2, :co_occurs_score, :same_actor_score,
                 :total_score, :shared_actor, NOW())
            ON CONFLICT (title_id_1, title_id_2)
            DO UPDATE SET
                co_occurs_score = EXCLUDED.co_occurs_score,
                same_actor_score = EXCLUDED.same_actor_score,
                total_score = EXCLUDED.total_score,
                shared_actor = EXCLUDED.shared_actor,
                updated_at = NOW()
            """

            # Batch insert (chunks of 1000)
            batch_size = 1000
            inserted_count = 0

            for i in range(0, len(connectivity_records), batch_size):
                batch = connectivity_records[i : i + batch_size]

                # Prepare batch data
                batch_data = []
                for record in batch:
                    batch_data.append(
                        {
                            "title_id_1": record["title1_id"],
                            "title_id_2": record["title2_id"],
                            "co_occurs_score": record["co_occurs_score"],
                            "same_actor_score": record["same_actor_score"],
                            "total_score": record["total_score"],
                            "shared_actor": record.get("shared_actor"),
                        }
                    )

                try:
                    session.execute(text(insert_query), batch_data)
                    inserted_count += len(batch_data)
                    logger.debug(f"Inserted batch {i//batch_size + 1}, total: {inserted_count}")
                except Exception as e:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: {e}")
                    logger.error(f"Sample from batch: {batch_data[0] if batch_data else 'empty'}")
                    raise

            session.commit()

            logger.info(f"Successfully synced {inserted_count} connectivity records")

            return {"deleted": deleted_count, "inserted": inserted_count}

    async def get_cache_statistics(self) -> Dict[str, any]:
        """Get statistics about connectivity cache"""

        with get_db_session() as session:
            stats_query = """
            SELECT
                COUNT(*) as total_connections,
                AVG(total_score) as avg_score,
                MAX(total_score) as max_score,
                COUNT(CASE WHEN total_score >= 0.7 THEN 1 END) as strong_connections,
                COUNT(CASE WHEN total_score >= 0.4 AND total_score < 0.7 THEN 1 END) as moderate_connections,
                COUNT(CASE WHEN same_actor_score > 0 THEN 1 END) as actor_matches,
                COUNT(CASE WHEN co_occurs_score > 0 THEN 1 END) as entity_matches
            FROM title_connectivity_cache
            """

            result = session.execute(text(stats_query)).fetchone()

            return {
                "total_connections": result.total_connections,
                "avg_score": float(result.avg_score) if result.avg_score else 0.0,
                "max_score": float(result.max_score) if result.max_score else 0.0,
                "strong_connections": result.strong_connections,
                "moderate_connections": result.moderate_connections,
                "actor_matches": result.actor_matches,
                "entity_matches": result.entity_matches,
            }

    async def run_full_sync(self, min_shared_entities: int = 2) -> Dict[str, any]:
        """
        Complete sync pipeline: Neo4j → Postgres

        Computes connectivity scores on-the-fly (no heavy relationship creation)

        Args:
            min_shared_entities: Minimum shared entities to consider (default 2)

        Returns:
            Sync statistics
        """
        logger.info("=== STARTING CONNECTIVITY CACHE SYNC ===")

        # Step 1: Compute connectivity from Neo4j (lightweight)
        connectivity_records = await self.fetch_neo4j_connectivity(min_shared_entities)

        # Step 2: Sync to Postgres
        sync_results = await self.sync_to_postgres(connectivity_records)

        # Step 3: Get statistics
        stats = await self.get_cache_statistics()

        logger.info("=== CONNECTIVITY CACHE SYNC COMPLETE ===")
        logger.info(f"Cache statistics: {stats}")

        return {
            "sync_results": sync_results,
            "cache_stats": stats,
        }


async def main():
    """Run connectivity cache sync"""
    builder = ConnectivityCacheBuilder()
    results = await builder.run_full_sync()

    # Print summary
    print("\n=== Connectivity Cache Sync Results ===")
    print(f"Deleted: {results['sync_results']['deleted']}")
    print(f"Inserted: {results['sync_results']['inserted']}")
    print(f"\nCache Statistics:")
    print(f"  Total connections: {results['cache_stats']['total_connections']}")
    print(f"  Average score: {results['cache_stats']['avg_score']:.3f}")
    print(f"  Strong connections (>=0.7): {results['cache_stats']['strong_connections']}")
    print(
        f"  Moderate connections (0.4-0.7): {results['cache_stats']['moderate_connections']}"
    )
    print(f"  Actor matches: {results['cache_stats']['actor_matches']}")
    print(f"  Entity matches: {results['cache_stats']['entity_matches']}")


if __name__ == "__main__":
    asyncio.run(main())
