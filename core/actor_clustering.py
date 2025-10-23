"""
Actor Clustering Service using Neo4j

Uses entity co-occurrence patterns to normalize actors into clusters
for focused Event Family generation.

Example:
    Israel + Netanyahu + IDF + Gaza → CLUSTER_ISRAEL_PALESTINE
    Putin + Russia + Moscow → CLUSTER_RUSSIA
    Trump + Biden + Washington → CLUSTER_US
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from loguru import logger

from core.neo4j_sync import get_neo4j_sync


class ActorClusteringService:
    """
    Service to detect and normalize actor clusters from Neo4j co-occurrence data.

    Used in Phase 3 (Clustering) to prevent overfragmentation when using
    key_actors in ef_key generation.
    """

    def __init__(self, min_co_occurrence: int = 10, max_cluster_size: int = 5):
        """
        Initialize actor clustering service.

        Args:
            min_co_occurrence: Minimum times entities must appear together
                              to be considered part of same cluster (default: 10)
            max_cluster_size: Maximum entities per cluster to prevent overly broad clusters
        """
        self.neo4j = get_neo4j_sync()
        self.min_co_occurrence = min_co_occurrence
        self.max_cluster_size = max_cluster_size
        self._clusters = None
        self._entity_to_cluster = None

    async def build_clusters(self) -> Dict[str, List[str]]:
        """
        Build actor clusters from Neo4j entity co-occurrence patterns.

        Returns:
            Dict mapping cluster_id to list of member entities
            Example: {
                "CLUSTER_ISRAEL_PALESTINE": ["Israel", "Palestine", "Hamas", "Gaza"],
                "CLUSTER_RUSSIA": ["Russia", "Putin", "Moscow"],
                "CLUSTER_US": ["United States", "Trump", "Biden"]
            }
        """
        logger.info("Building actor clusters from Neo4j co-occurrence data...")

        # Get entity co-occurrence network
        query = """
        MATCH (t:Title {gate_keep: true})-[:HAS_ENTITY]->(e1:Entity)
        MATCH (t)-[:HAS_ENTITY]->(e2:Entity)
        WHERE e1.name < e2.name

        WITH e1, e2, COUNT(DISTINCT t) as co_occurrence
        WHERE co_occurrence >= $min_co_occurrence

        RETURN e1.name as entity1,
               e2.name as entity2,
               co_occurrence
        ORDER BY co_occurrence DESC
        """

        async with self.neo4j.driver.session() as session:
            result = await session.run(query, min_co_occurrence=self.min_co_occurrence)
            edges = await result.data()

        if not edges:
            logger.warning("No strong entity co-occurrences found")
            return {}

        logger.info(f"Found {len(edges)} entity pairs with strong co-occurrence")

        # Build graph and detect communities using simple connected components
        clusters = self._detect_communities(edges)

        # Create cluster names based on most central entities
        named_clusters = await self._name_clusters(clusters)

        self._clusters = named_clusters
        self._build_entity_mapping()

        logger.info(f"Built {len(named_clusters)} actor clusters")
        for cluster_id, members in named_clusters.items():
            logger.info(f"  {cluster_id}: {len(members)} entities")

        return named_clusters

    def _detect_communities(self, edges: List[Dict]) -> List[Set[str]]:
        """
        Detect communities using edge strength threshold.

        Instead of simple connected components (which creates one giant cluster),
        only connect entities with STRONG co-occurrence (top percentile).

        Args:
            edges: List of edge dicts with entity1, entity2, co_occurrence

        Returns:
            List of sets, each set is a cluster of connected entities
        """
        # Sort edges by co-occurrence strength
        sorted_edges = sorted(edges, key=lambda x: x["co_occurrence"], reverse=True)

        # Use very high threshold: only keep STRONG co-occurrences
        # This prevents weak links from connecting everything into one giant cluster
        if len(sorted_edges) > 10:
            strengths = [e["co_occurrence"] for e in sorted_edges]
            # Use 90th percentile - only the strongest 10% of connections
            threshold_index = len(strengths) // 10
            threshold = max(
                strengths[threshold_index], 12
            )  # At least 12 co-occurrences
        else:
            threshold = max(e["co_occurrence"] for e in sorted_edges)

        logger.debug(
            f"Using co-occurrence threshold: {threshold} (keeping top {len([e for e in sorted_edges if e['co_occurrence'] >= threshold])} edges)"
        )

        # Build graph with only strong edges
        graph = {}
        for edge in sorted_edges:
            if edge["co_occurrence"] < threshold:
                break  # Skip weaker edges

            e1, e2 = edge["entity1"], edge["entity2"]

            if e1 not in graph:
                graph[e1] = set()
            if e2 not in graph:
                graph[e2] = set()

            graph[e1].add(e2)
            graph[e2].add(e1)

        # Find connected components using DFS
        visited = set()
        clusters = []

        def dfs(node, cluster):
            visited.add(node)
            cluster.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, cluster)

        for node in graph:
            if node not in visited:
                cluster = set()
                dfs(node, cluster)
                if len(cluster) >= 2:  # Only keep clusters with 2+ entities
                    # If cluster is too large, it's too heterogeneous - skip it
                    if len(cluster) <= self.max_cluster_size:
                        clusters.append(cluster)
                    else:
                        logger.debug(
                            f"Skipping oversized cluster with {len(cluster)} entities (max: {self.max_cluster_size})"
                        )

        return clusters

    async def _name_clusters(self, clusters: List[Set[str]]) -> Dict[str, List[str]]:
        """
        Name clusters based on their most central/important entities.

        Args:
            clusters: List of entity sets

        Returns:
            Dict mapping cluster names to entity lists
        """
        named_clusters = {}

        for i, cluster in enumerate(clusters, 1):
            # Get entity centrality within cluster
            entities = list(cluster)

            # Find the most mentioned entity as cluster representative
            query = """
            MATCH (e:Entity)<-[:HAS_ENTITY]-(t:Title {gate_keep: true})
            WHERE e.name IN $entities
            WITH e, COUNT(t) as mention_count
            RETURN e.name as entity, mention_count
            ORDER BY mention_count DESC
            LIMIT 1
            """

            async with self.neo4j.driver.session() as session:
                result = await session.run(query, entities=entities)
                data = await result.single()

                if data:
                    primary_entity = data["entity"]
                else:
                    primary_entity = entities[0]

            # Create cluster name
            cluster_name = self._generate_cluster_name(primary_entity, entities)
            named_clusters[cluster_name] = sorted(entities)

        return named_clusters

    def _generate_cluster_name(self, primary: str, members: List[str]) -> str:
        """
        Generate a cluster name based on primary entity and members.

        Args:
            primary: Most important entity in cluster
            members: All cluster members

        Returns:
            Cluster name like "CLUSTER_ISRAEL_PALESTINE" or "CLUSTER_RUSSIA"
        """
        # Normalize primary entity name
        primary_normalized = (
            primary.upper()
            .replace(" ", "_")
            .replace("STATE_OF_", "")
            .replace("UNITED_STATES", "US")
        )

        # If cluster is large and involves major geopolitical actors, create descriptive name
        major_actors = {
            "ISRAEL": ["PALESTINE", "HAMAS", "GAZA"],
            "PALESTINE": ["ISRAEL", "HAMAS", "GAZA"],
            "RUSSIA": ["UKRAINE", "PUTIN"],
            "UKRAINE": ["RUSSIA"],
            "CHINA": ["TAIWAN", "BEIJING"],
            "US": ["TRUMP", "BIDEN", "WASHINGTON"],
        }

        for key_actor, related in major_actors.items():
            if (
                primary_normalized.startswith(key_actor)
                or key_actor in primary_normalized
            ):
                # Check if cluster contains related actors
                members_normalized = [
                    m.upper().replace(" ", "_").replace("STATE_OF_", "")
                    for m in members
                ]
                for rel in related:
                    if any(rel in m for m in members_normalized):
                        # Found a major story cluster
                        actors = sorted([key_actor, rel])
                        return f"CLUSTER_{'_'.join(actors)}"

        # Default: single actor cluster
        return f"CLUSTER_{primary_normalized}"

    def _build_entity_mapping(self):
        """Build reverse mapping from entity to cluster_id"""
        self._entity_to_cluster = {}
        if self._clusters:
            for cluster_id, members in self._clusters.items():
                for entity in members:
                    self._entity_to_cluster[entity] = cluster_id

    def normalize_actors(self, actors: List[str]) -> List[str]:
        """
        Normalize a list of actors to their cluster representatives.

        Args:
            actors: List of entity names

        Returns:
            List of normalized cluster IDs

        Example:
            Input: ["Israel", "Hamas", "Donald Trump"]
            Output: ["CLUSTER_ISRAEL_PALESTINE", "CLUSTER_US"]
        """
        if not self._entity_to_cluster:
            logger.warning(
                "Clusters not built yet, returning original actors. Call build_clusters() first."
            )
            return actors

        # Map each actor to its cluster
        clusters = set()
        unmapped = []

        for actor in actors:
            if actor in self._entity_to_cluster:
                clusters.add(self._entity_to_cluster[actor])
            else:
                # Entity not in any cluster, keep as-is
                unmapped.append(actor)

        # Return cluster IDs + unmapped entities
        result = sorted(list(clusters)) + sorted(unmapped)
        return result

    def get_cluster_members(self, cluster_id: str) -> List[str]:
        """
        Get all entities in a cluster.

        Args:
            cluster_id: Cluster ID like "CLUSTER_ISRAEL_PALESTINE"

        Returns:
            List of entity names in cluster
        """
        if not self._clusters:
            return []
        return self._clusters.get(cluster_id, [])

    def get_cluster_for_entity(self, entity: str) -> str | None:
        """
        Get cluster ID for an entity.

        Args:
            entity: Entity name

        Returns:
            Cluster ID or None if entity not in any cluster
        """
        if not self._entity_to_cluster:
            return None
        return self._entity_to_cluster.get(entity)

    def get_all_clusters(self) -> Dict[str, List[str]]:
        """Get all clusters"""
        return self._clusters or {}


# Singleton instance
_actor_clustering_service: ActorClusteringService | None = None


def get_actor_clustering_service() -> ActorClusteringService:
    """Get singleton actor clustering service instance"""
    global _actor_clustering_service
    if _actor_clustering_service is None:
        _actor_clustering_service = ActorClusteringService(
            min_co_occurrence=5,  # Must appear together at least 5 times
            max_cluster_size=5,  # Max 5 entities per cluster
        )
    return _actor_clustering_service
