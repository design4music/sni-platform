"""
Narrative Matching Bridge System
Strategic Narrative Intelligence ETL Pipeline

Bridge module between CLUST-1 thematic grouping and NSF-1 narrative generation.
Compares new topic clusters to existing narratives using similarity thresholds
and entity overlap to decide whether to attach articles to existing narratives
or create new ones.

Key Features:
- Cosine similarity matching between cluster/narrative centroids
- Multi-threshold decision logic (0.80+ attach, 0.65-0.80 borderline, <0.65 new)
- Entity overlap analysis for borderline cases
- Timeline recency checks
- Automatic narrative updates and creation
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import structlog
from sklearn.metrics.pairwise import cosine_similarity

from ..core.database import get_db_session
from ..core.database.models import (Article, ArticleCluster, EntityMention,
                                    NarrativeArticleAssociation,
                                    NarrativeMetrics, NarrativeNSF1)

# from .clust1_thematic_grouping import ClusteringResult  # ARCHIVED

logger = structlog.get_logger(__name__)


@dataclass
class MatchingDecision:
    """Decision result from narrative matching"""

    action: str  # 'attach', 'create_new', 'skip'
    cluster_id: str
    narrative_id: Optional[str] = None  # For attach actions
    similarity_score: float = 0.0
    entity_overlap_score: float = 0.0
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class NarrativeCentroid:
    """Narrative centroid data for similarity matching"""

    narrative_id: str
    narrative_uuid: str
    centroid_vector: np.ndarray
    last_updated: datetime
    article_count: int
    entities: Set[str]


class NarrativeMatcher:
    """
    Bridge system that matches CLUST-1 clusters to existing narratives
    or creates new narratives when no good match exists.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)

        # Similarity thresholds
        self.attach_threshold = self.config.get("attach_threshold", 0.80)
        self.borderline_lower = self.config.get("borderline_lower", 0.65)
        self.borderline_upper = self.config.get("borderline_upper", 0.80)

        # Entity overlap settings
        self.entity_overlap_boost = self.config.get("entity_overlap_boost", 0.15)
        self.min_entity_overlap = self.config.get("min_entity_overlap", 2)

        # Timeline settings
        self.max_narrative_age_days = self.config.get("max_narrative_age_days", 30)
        self.recent_activity_days = self.config.get("recent_activity_days", 7)

        self.logger.info(
            "Narrative Matcher initialized",
            attach_threshold=self.attach_threshold,
            borderline_range=f"{self.borderline_lower}-{self.borderline_upper}",
            max_narrative_age_days=self.max_narrative_age_days,
        )

    async def process_clusters(
        self, clusters: List[ClusteringResult]
    ) -> List[MatchingDecision]:
        """
        Main entry point: Process CLUST-1 results and match to narratives

        Args:
            clusters: List of clustering results from CLUST-1

        Returns:
            List of matching decisions made
        """
        try:
            self.logger.info("Starting narrative matching", cluster_count=len(clusters))

            if not clusters:
                return []

            # Load active narrative centroids
            narrative_centroids = await self._load_narrative_centroids()
            self.logger.info(
                "Loaded narrative centroids", count=len(narrative_centroids)
            )

            # Process each cluster
            decisions = []
            for cluster in clusters:
                decision = await self._match_cluster_to_narratives(
                    cluster, narrative_centroids
                )
                decisions.append(decision)

                # Execute the decision
                await self._execute_decision(decision, cluster)

            self.logger.info(
                "Narrative matching completed",
                total_decisions=len(decisions),
                attached=len([d for d in decisions if d.action == "attach"]),
                new_narratives=len([d for d in decisions if d.action == "create_new"]),
                skipped=len([d for d in decisions if d.action == "skip"]),
            )

            return decisions

        except Exception as exc:
            self.logger.error(
                "Narrative matching failed", error=str(exc), exc_info=True
            )
            raise

    async def _load_narrative_centroids(self) -> List[NarrativeCentroid]:
        """Load active narratives with their centroid vectors"""
        async with get_db_session() as session:
            # Get active narratives with embeddings from last 30 days
            cutoff_date = datetime.utcnow() - timedelta(
                days=self.max_narrative_age_days
            )

            query = """
            SELECT 
                n.id as narrative_uuid,
                n.narrative_id,
                n.narrative_embedding,
                n.updated_at,
                nm.last_spike,
                COUNT(naa.article_id) as article_count
            FROM narratives n
            LEFT JOIN narrative_metrics nm ON n.id = nm.narrative_uuid
            LEFT JOIN narrative_article_associations naa ON n.id = naa.narrative_uuid
            WHERE n.narrative_embedding IS NOT NULL
                AND n.updated_at >= %s
                AND (nm.narrative_status IS NULL OR nm.narrative_status = 'active')
            GROUP BY n.id, n.narrative_id, n.narrative_embedding, n.updated_at, nm.last_spike
            ORDER BY n.updated_at DESC
            """

            result = await session.execute(query, (cutoff_date,))
            rows = result.fetchall()

            centroids = []
            for row in rows:
                # Load entity information for this narrative
                entities = await self._get_narrative_entities(
                    session, row["narrative_uuid"]
                )

                centroid = NarrativeCentroid(
                    narrative_id=row["narrative_id"],
                    narrative_uuid=str(row["narrative_uuid"]),
                    centroid_vector=np.array(row["narrative_embedding"]),
                    last_updated=row["updated_at"],
                    article_count=row["article_count"] or 0,
                    entities=entities,
                )
                centroids.append(centroid)

            return centroids

    async def _get_narrative_entities(self, session, narrative_uuid: str) -> Set[str]:
        """Get entities associated with a narrative's articles"""
        query = """
        SELECT DISTINCT LOWER(em.entity_text) as entity
        FROM entity_mentions em
        JOIN articles a ON em.article_id = a.id
        JOIN narrative_article_associations naa ON a.id = naa.article_id
        WHERE naa.narrative_uuid = %s
            AND em.entity_type IN ('PERSON', 'ORG', 'GPE', 'EVENT')
            AND LENGTH(em.entity_text) > 2
        LIMIT 50
        """

        result = await session.execute(query, (narrative_uuid,))
        rows = result.fetchall()

        return {row["entity"] for row in rows}

    async def _match_cluster_to_narratives(
        self, cluster: ClusteringResult, narrative_centroids: List[NarrativeCentroid]
    ) -> MatchingDecision:
        """Match a single cluster against existing narratives"""
        if not narrative_centroids or cluster.centroid_vector is None:
            return MatchingDecision(
                action="create_new",
                cluster_id=cluster.cluster_id,
                reasoning="No existing narratives or no cluster centroid",
            )

        # Calculate similarities with all narratives
        best_match = None
        best_similarity = 0.0

        cluster_vector = cluster.centroid_vector.reshape(1, -1)

        for narrative in narrative_centroids:
            narrative_vector = narrative.centroid_vector.reshape(1, -1)

            # Ensure vector dimensions match
            if cluster_vector.shape[1] != narrative_vector.shape[1]:
                self.logger.warning(
                    "Vector dimension mismatch",
                    cluster_dim=cluster_vector.shape[1],
                    narrative_dim=narrative_vector.shape[1],
                    narrative_id=narrative.narrative_id,
                )
                continue

            similarity = cosine_similarity(cluster_vector, narrative_vector)[0, 0]

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = narrative

        if not best_match:
            return MatchingDecision(
                action="create_new",
                cluster_id=cluster.cluster_id,
                reasoning="No compatible narratives found",
            )

        # Apply decision logic based on similarity thresholds
        return await self._apply_decision_logic(cluster, best_match, best_similarity)

    async def _apply_decision_logic(
        self,
        cluster: ClusteringResult,
        best_narrative: NarrativeCentroid,
        similarity: float,
    ) -> MatchingDecision:
        """Apply threshold-based decision logic"""

        # High similarity: Direct attach
        if similarity >= self.attach_threshold:
            return MatchingDecision(
                action="attach",
                cluster_id=cluster.cluster_id,
                narrative_id=best_narrative.narrative_id,
                similarity_score=similarity,
                confidence=0.9,
                reasoning=f"High similarity ({similarity:.3f} >= {self.attach_threshold})",
            )

        # Low similarity: Create new
        if similarity < self.borderline_lower:
            return MatchingDecision(
                action="create_new",
                cluster_id=cluster.cluster_id,
                similarity_score=similarity,
                confidence=0.8,
                reasoning=f"Low similarity ({similarity:.3f} < {self.borderline_lower})",
            )

        # Borderline: Check entity overlap and timeline
        decision = await self._evaluate_borderline_case(
            cluster, best_narrative, similarity
        )

        # Log borderline matches for manual review
        self.logger.warning(
            "BORDERLINE MATCH - Manual review recommended",
            cluster_id=cluster.cluster_id,
            cluster_label=cluster.label,
            narrative_id=best_narrative.narrative_id,
            similarity=similarity,
            decision=decision.action,
            reasoning=decision.reasoning,
        )

        return decision

    async def _evaluate_borderline_case(
        self, cluster: ClusteringResult, narrative: NarrativeCentroid, similarity: float
    ) -> MatchingDecision:
        """Evaluate borderline cases using entity overlap and timeline"""

        # Get cluster entities
        cluster_entities = await self._get_cluster_entities(cluster)

        # Calculate entity overlap
        entity_overlap = len(cluster_entities.intersection(narrative.entities))
        entity_overlap_score = entity_overlap / max(len(cluster_entities), 1)

        # Check timeline recency
        days_since_update = (datetime.utcnow() - narrative.last_updated).days
        is_recent = days_since_update <= self.recent_activity_days

        # Boosted similarity with entity overlap
        boosted_similarity = similarity + (
            entity_overlap_score * self.entity_overlap_boost
        )

        # Decision logic for borderline cases
        if (
            boosted_similarity >= self.attach_threshold
            and entity_overlap >= self.min_entity_overlap
            and is_recent
        ):

            return MatchingDecision(
                action="attach",
                cluster_id=cluster.cluster_id,
                narrative_id=narrative.narrative_id,
                similarity_score=similarity,
                entity_overlap_score=entity_overlap_score,
                confidence=0.7,
                reasoning=f"Borderline with entity boost ({boosted_similarity:.3f}, {entity_overlap} entities, recent)",
            )

        elif entity_overlap >= self.min_entity_overlap * 2:  # Strong entity overlap
            return MatchingDecision(
                action="attach",
                cluster_id=cluster.cluster_id,
                narrative_id=narrative.narrative_id,
                similarity_score=similarity,
                entity_overlap_score=entity_overlap_score,
                confidence=0.6,
                reasoning=f"Strong entity overlap ({entity_overlap} entities)",
            )

        else:
            return MatchingDecision(
                action="create_new",
                cluster_id=cluster.cluster_id,
                similarity_score=similarity,
                entity_overlap_score=entity_overlap_score,
                confidence=0.7,
                reasoning=f"Borderline case insufficient ({boosted_similarity:.3f}, {entity_overlap} entities)",
            )

    async def _get_cluster_entities(self, cluster: ClusteringResult) -> Set[str]:
        """Extract entities from cluster articles"""
        async with get_db_session() as session:
            if not cluster.articles:
                return set()

            # Get entities from cluster articles
            article_ids = "','".join(cluster.articles)
            query = f"""
            SELECT DISTINCT LOWER(em.entity_text) as entity
            FROM entity_mentions em
            WHERE em.article_id IN ('{article_ids}')
                AND em.entity_type IN ('PERSON', 'ORG', 'GPE', 'EVENT')
                AND LENGTH(em.entity_text) > 2
            LIMIT 20
            """

            result = await session.execute(query)
            rows = result.fetchall()

            return {row["entity"] for row in rows}

    async def _execute_decision(
        self, decision: MatchingDecision, cluster: ClusteringResult
    ):
        """Execute the matching decision"""
        try:
            if decision.action == "attach":
                await self._attach_cluster_to_narrative(decision, cluster)
            elif decision.action == "create_new":
                await self._create_new_narrative(decision, cluster)
            # 'skip' action requires no execution

            self.logger.info(
                "Decision executed",
                action=decision.action,
                cluster_id=decision.cluster_id,
                narrative_id=decision.narrative_id,
                confidence=decision.confidence,
            )

        except Exception as exc:
            self.logger.error(
                "Failed to execute decision",
                action=decision.action,
                cluster_id=decision.cluster_id,
                error=str(exc),
            )
            raise

    async def _attach_cluster_to_narrative(
        self, decision: MatchingDecision, cluster: ClusteringResult
    ):
        """Attach cluster articles to existing narrative"""
        async with get_db_session() as session:
            try:
                # Get narrative UUID
                narrative_query = "SELECT id FROM narratives WHERE narrative_id = %s"
                result = await session.execute(
                    narrative_query, (decision.narrative_id,)
                )
                narrative_row = result.fetchone()

                if not narrative_row:
                    self.logger.error(
                        "Narrative not found", narrative_id=decision.narrative_id
                    )
                    return

                narrative_uuid = narrative_row["id"]

                # Create article associations
                association_count = 0
                for article_id in cluster.articles:
                    # Check if association already exists
                    check_query = """
                    SELECT 1 FROM narrative_article_associations 
                    WHERE narrative_uuid = %s AND article_id = %s
                    """
                    existing = await session.execute(
                        check_query, (narrative_uuid, article_id)
                    )

                    if not existing.fetchone():
                        association = NarrativeArticleAssociation(
                            narrative_uuid=narrative_uuid,
                            article_id=article_id,
                            association_strength=decision.similarity_score,
                            association_type="clust1_match",
                            association_metadata={
                                "cluster_id": cluster.cluster_id,
                                "similarity_score": decision.similarity_score,
                                "entity_overlap_score": decision.entity_overlap_score,
                                "matched_at": datetime.utcnow().isoformat(),
                            },
                        )
                        session.add(association)
                        association_count += 1

                # Update narrative metrics
                await self._update_narrative_metrics(session, narrative_uuid, cluster)

                # Update narrative centroid (recalculate with new articles)
                await self._update_narrative_centroid(session, narrative_uuid)

                await session.commit()

                self.logger.info(
                    "Cluster attached to narrative",
                    cluster_id=cluster.cluster_id,
                    narrative_id=decision.narrative_id,
                    new_associations=association_count,
                )

            except Exception as exc:
                await session.rollback()
                self.logger.error(
                    "Failed to attach cluster",
                    cluster_id=cluster.cluster_id,
                    narrative_id=decision.narrative_id,
                    error=str(exc),
                )
                raise

    async def _create_new_narrative(
        self, decision: MatchingDecision, cluster: ClusteringResult
    ):
        """Create new narrative from cluster"""
        # This will trigger NSF-1 narrative generation
        # For now, we'll create a placeholder and mark for NSF-1 processing

        async with get_db_session() as session:
            try:
                # Generate narrative ID
                narrative_id = await self._generate_narrative_id(session, cluster)

                # Create placeholder narrative (NSF-1 will fill in details)
                narrative = NarrativeNSF1(
                    narrative_id=narrative_id,
                    title=f"Narrative: {cluster.label}",
                    summary=f"Narrative emerging from cluster {cluster.cluster_id}",
                    origin_language="en",  # Default, NSF-1 will determine actual
                    dominant_source_languages=["en"],
                    alignment=[],  # NSF-1 will populate
                    actor_origin=[],
                    conflict_alignment=[],
                    frame_logic=[],
                    confidence_rating="medium",
                    narrative_embedding=(
                        cluster.centroid_vector.tolist()
                        if cluster.centroid_vector is not None
                        else None
                    ),
                    update_status={
                        "last_updated": datetime.utcnow().isoformat(),
                        "update_trigger": "clust1_new_cluster",
                        "needs_nsf1_processing": True,
                    },
                )

                session.add(narrative)
                await session.flush()  # Get the UUID

                # Create narrative metrics
                metrics = NarrativeMetrics(
                    narrative_uuid=narrative.id,
                    narrative_start_date=cluster.time_window[0],
                    trending_score=float(
                        cluster.confidence_score * 10
                    ),  # Scale to 0-10
                    credibility_score=5.0,  # Default medium
                    narrative_priority=3,  # Medium priority
                    narrative_status="active",
                )
                session.add(metrics)

                # Create article associations
                for article_id in cluster.articles:
                    association = NarrativeArticleAssociation(
                        narrative_uuid=narrative.id,
                        article_id=article_id,
                        association_strength=0.9,  # High for founding articles
                        association_type="clust1_founder",
                        association_metadata={
                            "cluster_id": cluster.cluster_id,
                            "created_at": datetime.utcnow().isoformat(),
                        },
                    )
                    session.add(association)

                await session.commit()

                self.logger.info(
                    "New narrative created from cluster",
                    cluster_id=cluster.cluster_id,
                    narrative_id=narrative_id,
                    article_count=len(cluster.articles),
                )

            except Exception as exc:
                await session.rollback()
                self.logger.error(
                    "Failed to create new narrative",
                    cluster_id=cluster.cluster_id,
                    error=str(exc),
                )
                raise

    async def _generate_narrative_id(self, session, cluster: ClusteringResult) -> str:
        """Generate unique narrative ID"""
        # Use timestamp and cluster info for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        base_id = f"EN-{timestamp}-{cluster.cluster_id.split('_')[-1]}"

        # Ensure uniqueness
        counter = 1
        narrative_id = base_id

        while True:
            check_query = "SELECT 1 FROM narratives WHERE narrative_id = %s"
            result = await session.execute(check_query, (narrative_id,))

            if not result.fetchone():
                break

            narrative_id = f"{base_id}-{counter:02d}"
            counter += 1

        return narrative_id

    async def _update_narrative_metrics(
        self, session, narrative_uuid: str, cluster: ClusteringResult
    ):
        """Update narrative metrics with new cluster information"""
        # Update trending score and last spike
        update_query = """
        UPDATE narrative_metrics 
        SET trending_score = GREATEST(trending_score, %s),
            last_spike = %s,
            narrative_end_date = %s
        WHERE narrative_uuid = %s
        """

        trending_boost = cluster.confidence_score * 5.0  # Scale appropriately
        current_time = datetime.utcnow()

        await session.execute(
            update_query,
            (trending_boost, current_time, cluster.time_window[1], narrative_uuid),
        )

    async def _update_narrative_centroid(self, session, narrative_uuid: str):
        """Recalculate narrative centroid with new articles"""
        # This is a placeholder - would need to recalculate from all articles
        # For now, we'll leave the existing centroid as-is
        # In a full implementation, we'd:
        # 1. Get all article embeddings for this narrative
        # 2. Calculate new centroid
        # 3. Update narrative_embedding
        pass


# Convenience function for external usage
async def run_narrative_matching(
    clusters: List[ClusteringResult],
) -> List[MatchingDecision]:
    """Run narrative matching on CLUST-1 results"""
    from ..core.config import get_config

    config = get_config()
    matcher_config = getattr(config, "narrative_matching", {})

    matcher = NarrativeMatcher(matcher_config)
    return await matcher.process_clusters(clusters)
