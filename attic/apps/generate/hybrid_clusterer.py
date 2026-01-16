"""
Hybrid Clustering Engine - P3_v1 Core Logic

Combines multiple signals for mechanical incident clustering:
- Entity overlap (50% weight)
- AAT actor match (20% weight)
- Neo4j connectivity (20% weight)
- Temporal proximity (10% weight)

Strategy: Build similarity graph → find connected components → validate with LLM
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session


class HybridClusterer:
    """
    Mechanical clustering using hybrid similarity scoring

    Threshold: 0.4 (tune based on results)
    Output: Incident clusters + orphans
    """

    def __init__(self, similarity_threshold: float = 0.4):
        self.threshold = similarity_threshold
        self.connectivity_cache = {}  # title_pair -> score

    async def load_connectivity_cache(self, title_ids: List[str]) -> None:
        """
        Load Neo4j connectivity scores from Postgres cache

        Pre-loads all connectivity for given titles into memory for fast lookup
        """
        if not title_ids:
            return

        logger.info(f"Loading connectivity cache for {len(title_ids)} titles...")

        with get_db_session() as session:
            # Get all connectivity between any pair of input titles
            # Build UUID array literal for PostgreSQL
            uuid_list_str = "ARRAY[" + ",".join([f"'{tid}'::uuid" for tid in title_ids]) + "]"

            query = f"""
            SELECT title_id_1, title_id_2, total_score
            FROM title_connectivity_cache
            WHERE title_id_1 = ANY({uuid_list_str})
               OR title_id_2 = ANY({uuid_list_str})
            """

            results = session.execute(text(query)).fetchall()

            # Build lookup dict
            for row in results:
                t1, t2 = sorted([str(row.title_id_1), str(row.title_id_2)])
                self.connectivity_cache[(t1, t2)] = float(row.total_score)

            logger.info(
                f"Loaded {len(self.connectivity_cache)} connectivity scores from cache"
            )

    def get_neo4j_connectivity(self, title1_id: str, title2_id: str) -> float:
        """
        Get connectivity score from cache

        Returns: 0.0-1.0 (0.0 if not found)
        """
        t1, t2 = sorted([title1_id, title2_id])
        return self.connectivity_cache.get((t1, t2), 0.0)

    def calculate_entity_overlap(
        self, entities1: List[str], entities2: List[str]
    ) -> float:
        """
        Calculate weighted entity overlap (Jaccard with importance weighting)

        For now: Simple Jaccard (intersection / union)
        TODO: Weight by entity importance (Trump > minor actor)
        """
        if not entities1 or not entities2:
            return 0.0

        set1 = set(e.lower() for e in entities1)
        set2 = set(e.lower() for e in entities2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        jaccard = intersection / union
        return jaccard

    def calculate_actor_overlap(self, aat1: Dict, aat2: Dict) -> float:
        """
        Calculate AAT actor similarity

        Returns: 1.0 if actors match (fuzzy), 0.0 otherwise
        """
        actor1 = aat1.get("actor") if aat1 else None
        actor2 = aat2.get("actor") if aat2 else None

        if not actor1 or not actor2:
            return 0.0

        # Fuzzy matching (handles "Russia" vs "Russian Federation")
        actor1_norm = actor1.lower().strip()
        actor2_norm = actor2.lower().strip()

        # Exact match
        if actor1_norm == actor2_norm:
            return 1.0

        # Substring match (crude but effective)
        if actor1_norm in actor2_norm or actor2_norm in actor1_norm:
            return 0.8  # Partial match

        return 0.0

    def calculate_temporal_proximity(self, date1: datetime, date2: datetime) -> float:
        """
        Calculate temporal proximity score

        Returns:
        - 1.0: Same day
        - 0.5: Within 2 days
        - 0.2: Within 7 days
        - 0.0: More than 7 days apart
        """
        if not date1 or not date2:
            return 0.0

        # Handle datetime or string
        if isinstance(date1, str):
            date1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
        if isinstance(date2, str):
            date2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))

        delta = abs((date2 - date1).days)

        if delta == 0:
            return 1.0
        elif delta <= 2:
            return 0.5
        elif delta <= 7:
            return 0.2
        else:
            return 0.0

    def calculate_similarity_score(self, title1: Dict, title2: Dict) -> float:
        """
        Hybrid similarity score combining all signals

        Weights:
        - Entity overlap: 50%
        - Actor match: 20%
        - Neo4j connectivity: 20%
        - Temporal proximity: 10%

        Returns: 0.0-1.0 score
        """
        score = 0.0

        # Signal 1: Entity overlap (50%)
        entities1 = title1.get("entities", [])
        entities2 = title2.get("entities", [])
        entity_score = self.calculate_entity_overlap(entities1, entities2)
        score += entity_score * 0.5

        # Signal 2: Actor overlap from AAT (20%)
        aat1 = title1.get("action_triple", {})
        aat2 = title2.get("action_triple", {})
        actor_score = self.calculate_actor_overlap(aat1, aat2)
        score += actor_score * 0.2

        # Signal 3: Neo4j connectivity (20%)
        neo4j_score = self.get_neo4j_connectivity(title1["id"], title2["id"])
        score += neo4j_score * 0.2

        # Signal 4: Temporal proximity (10%)
        time_score = self.calculate_temporal_proximity(
            title1.get("pubdate_utc"), title2.get("pubdate_utc")
        )
        score += time_score * 0.1

        return score

    def find_connected_components(
        self, edges: List[Tuple[str, str, float]]
    ) -> List[Set[str]]:
        """
        Find connected components in similarity graph

        Uses Union-Find algorithm for efficient clustering

        Args:
            edges: List of (title_id_1, title_id_2, similarity_score)

        Returns:
            List of clusters (each cluster = set of title IDs)
        """
        if not edges:
            return []

        # Union-Find data structure
        parent = {}
        rank = {}

        def find(x):
            if x not in parent:
                parent[x] = x
                rank[x] = 0
            if parent[x] != x:
                parent[x] = find(parent[x])  # Path compression
            return parent[x]

        def union(x, y):
            root_x = find(x)
            root_y = find(y)

            if root_x == root_y:
                return

            # Union by rank
            if rank[root_x] < rank[root_y]:
                parent[root_x] = root_y
            elif rank[root_x] > rank[root_y]:
                parent[root_y] = root_x
            else:
                parent[root_y] = root_x
                rank[root_x] += 1

        # Build connected components
        for t1, t2, score in edges:
            union(t1, t2)

        # Group titles by component
        components = defaultdict(set)
        all_title_ids = set()
        for t1, t2, score in edges:
            all_title_ids.add(t1)
            all_title_ids.add(t2)

        for title_id in all_title_ids:
            root = find(title_id)
            components[root].add(title_id)

        return list(components.values())

    async def cluster_titles(self, titles: List[Dict]) -> Dict[str, List]:
        """
        Main clustering pipeline

        Args:
            titles: List of title dicts with entities, action_triple, pubdate_utc

        Returns:
            {
                "tight_clusters": [...],      # score >= 0.7, no LLM needed
                "moderate_clusters": [...],   # 0.4 <= score < 0.7, LLM validation
                "weak_connections": [...],    # score < 0.4, treat as orphans
                "orphans": [...],             # no connections at all
                "statistics": {...}
            }
        """
        if not titles:
            return {
                "tight_clusters": [],
                "moderate_clusters": [],
                "weak_connections": [],
                "orphans": [],
                "statistics": {},
            }

        logger.info(f"Clustering {len(titles)} titles with hybrid scoring...")

        # Step 1: Load connectivity cache
        title_ids = [t["id"] for t in titles]
        await self.load_connectivity_cache(title_ids)

        # Step 2: Calculate pairwise similarities
        edges_tight = []  # >= 0.7
        edges_moderate = []  # 0.4 <= score < 0.7
        edges_weak = []  # 0.3 <= score < 0.4

        for i, t1 in enumerate(titles):
            for t2 in titles[i + 1 :]:
                score = self.calculate_similarity_score(t1, t2)

                if score >= 0.7:
                    edges_tight.append((t1["id"], t2["id"], score))
                elif score >= self.threshold:
                    edges_moderate.append((t1["id"], t2["id"], score))
                elif score >= 0.3:
                    edges_weak.append((t1["id"], t2["id"], score))

        logger.info(
            f"Found {len(edges_tight)} tight edges, "
            f"{len(edges_moderate)} moderate edges, "
            f"{len(edges_weak)} weak edges"
        )

        # Step 3: Find connected components
        tight_components = self.find_connected_components(edges_tight)
        moderate_components = self.find_connected_components(edges_moderate)

        # Step 4: Identify orphans (no connections >= threshold)
        all_clustered_ids = set()
        for cluster in tight_components + moderate_components:
            all_clustered_ids.update(cluster)

        orphan_ids = [t["id"] for t in titles if t["id"] not in all_clustered_ids]

        # Step 5: Convert clusters to title lists
        title_lookup = {t["id"]: t for t in titles}

        tight_clusters = [[title_lookup[tid] for tid in cluster] for cluster in tight_components]
        moderate_clusters = [[title_lookup[tid] for tid in cluster] for cluster in moderate_components]
        orphans = [title_lookup[tid] for tid in orphan_ids]

        # Statistics
        stats = {
            "total_titles": len(titles),
            "tight_clusters": len(tight_clusters),
            "tight_titles": sum(len(c) for c in tight_clusters),
            "moderate_clusters": len(moderate_clusters),
            "moderate_titles": sum(len(c) for c in moderate_clusters),
            "orphans": len(orphans),
            "clustering_rate": len(all_clustered_ids) / len(titles) if titles else 0.0,
        }

        logger.info(f"Clustering complete: {stats}")

        return {
            "tight_clusters": tight_clusters,
            "moderate_clusters": moderate_clusters,
            "orphans": orphans,
            "statistics": stats,
        }
