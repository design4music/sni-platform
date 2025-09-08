"""
Base classes for clustering pipeline stages
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import structlog
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = structlog.get_logger(__name__)


class ClusteringStage(str, Enum):
    CLUST_1_THEMATIC = "clust_1_thematic"
    CLUST_2_INTERPRETIVE = "clust_2_interpretive"
    CLUST_3_TEMPORAL_ANOMALY = "clust_3_temporal_anomaly"
    CLUST_4_CONSOLIDATION = "clust_4_consolidation"


@dataclass
class ClusteringResult:
    """Result of a clustering operation"""

    stage: ClusteringStage
    clusters: List["ClusterInfo"]
    processing_time_seconds: float
    items_processed: int
    items_clustered: int
    items_failed: int
    metadata: Dict[str, Any]


@dataclass
class ClusterInfo:
    """Information about a cluster"""

    cluster_id: str
    stage: ClusteringStage
    articles: List[str]  # Article IDs
    centroid: Optional[np.ndarray]
    coherence_score: float
    dominant_topics: List[str]
    key_entities: Dict[str, Any]
    sentiment_distribution: Dict[str, float]
    language_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    temporal_span_hours: float
    metadata: Dict[str, Any]


class BaseClusteringStage(ABC):
    """Base class for clustering stages"""

    def __init__(self, stage: ClusteringStage, config: Dict[str, Any]):
        self.stage = stage
        self.config = config
        self.logger = structlog.get_logger(__name__).bind(stage=stage.value)

        # Initialize embedding model if needed
        self.embedding_model = None
        if config.get("use_embeddings", True):
            model_name = config.get("embedding_model", "all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)

    @abstractmethod
    async def cluster_articles(
        self, articles: List[Dict[str, Any]]
    ) -> ClusteringResult:
        """Main clustering method to implement"""
        pass

    @abstractmethod
    async def get_cluster_features(self, articles: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features for clustering"""
        pass

    def calculate_coherence_score(
        self, articles: List[Dict[str, Any]], features: np.ndarray
    ) -> float:
        """Calculate cluster coherence score"""
        try:
            if len(articles) < 2:
                return 1.0

            # Calculate average pairwise similarity
            similarities = cosine_similarity(features)
            n = len(similarities)

            # Get upper triangle (excluding diagonal)
            upper_triangle = similarities[np.triu_indices(n, k=1)]

            return float(np.mean(upper_triangle))

        except Exception as e:
            self.logger.error("Coherence calculation failed", error=str(e))
            return 0.0

    def extract_dominant_topics(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract dominant topics from articles"""
        try:
            topic_counts = {}

            for article in articles:
                topics = article.get("topics", [])
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Sort by frequency and return top topics
            sorted_topics = sorted(
                topic_counts.items(), key=lambda x: x[1], reverse=True
            )

            return [topic for topic, count in sorted_topics[:5]]

        except Exception as e:
            self.logger.error("Topic extraction failed", error=str(e))
            return []

    def extract_key_entities(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract key entities from articles"""
        try:
            entity_counts = {}

            for article in articles:
                entities = article.get("entities", {})

                for entity_type, entity_list in entities.items():
                    if entity_type not in entity_counts:
                        entity_counts[entity_type] = {}

                    for entity in entity_list:
                        entity_name = (
                            entity.get("text", entity)
                            if isinstance(entity, dict)
                            else entity
                        )
                        entity_counts[entity_type][entity_name] = (
                            entity_counts[entity_type].get(entity_name, 0) + 1
                        )

            # Get top entities for each type
            key_entities = {}
            for entity_type, entities in entity_counts.items():
                sorted_entities = sorted(
                    entities.items(), key=lambda x: x[1], reverse=True
                )
                key_entities[entity_type] = [
                    {"entity": entity, "count": count}
                    for entity, count in sorted_entities[:5]
                ]

            return key_entities

        except Exception as e:
            self.logger.error("Entity extraction failed", error=str(e))
            return {}

    def calculate_sentiment_distribution(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate sentiment distribution for articles"""
        try:
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            total = 0

            for article in articles:
                sentiment = article.get("sentiment", {})
                if isinstance(sentiment, dict):
                    label = sentiment.get("label", "neutral").lower()
                    if label in sentiment_counts:
                        sentiment_counts[label] += 1
                        total += 1

            if total == 0:
                return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}

            return {
                sentiment: count / total
                for sentiment, count in sentiment_counts.items()
            }

        except Exception as e:
            self.logger.error("Sentiment distribution calculation failed", error=str(e))
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}

    def calculate_language_distribution(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate language distribution for articles"""
        try:
            language_counts = {}

            for article in articles:
                language = article.get("language", "unknown")
                language_counts[language] = language_counts.get(language, 0) + 1

            return language_counts

        except Exception as e:
            self.logger.error("Language distribution calculation failed", error=str(e))
            return {"unknown": len(articles)}

    def calculate_source_distribution(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate source distribution for articles"""
        try:
            source_counts = {}

            for article in articles:
                source = article.get("source_name", "unknown")
                source_counts[source] = source_counts.get(source, 0) + 1

            return source_counts

        except Exception as e:
            self.logger.error("Source distribution calculation failed", error=str(e))
            return {"unknown": len(articles)}

    def calculate_temporal_span(self, articles: List[Dict[str, Any]]) -> float:
        """Calculate temporal span of articles in hours"""
        try:
            timestamps = []

            for article in articles:
                published_at = article.get("published_at")
                if published_at:
                    if isinstance(published_at, str):
                        from dateutil import parser

                        published_at = parser.parse(published_at)
                    timestamps.append(published_at)

            if len(timestamps) < 2:
                return 0.0

            min_time = min(timestamps)
            max_time = max(timestamps)

            return (max_time - min_time).total_seconds() / 3600

        except Exception as e:
            self.logger.error("Temporal span calculation failed", error=str(e))
            return 0.0

    async def create_cluster_info(
        self,
        cluster_id: str,
        articles: List[Dict[str, Any]],
        features: Optional[np.ndarray] = None,
    ) -> ClusterInfo:
        """Create comprehensive cluster information"""

        # Calculate centroid if features provided
        centroid = None
        if features is not None and len(features) > 0:
            centroid = np.mean(features, axis=0)

        # Calculate coherence score
        coherence_score = 0.0
        if features is not None:
            coherence_score = self.calculate_coherence_score(articles, features)

        return ClusterInfo(
            cluster_id=cluster_id,
            stage=self.stage,
            articles=[article.get("id", str(i)) for i, article in enumerate(articles)],
            centroid=centroid,
            coherence_score=coherence_score,
            dominant_topics=self.extract_dominant_topics(articles),
            key_entities=self.extract_key_entities(articles),
            sentiment_distribution=self.calculate_sentiment_distribution(articles),
            language_distribution=self.calculate_language_distribution(articles),
            source_distribution=self.calculate_source_distribution(articles),
            temporal_span_hours=self.calculate_temporal_span(articles),
            metadata={
                "article_count": len(articles),
                "stage": self.stage.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )


class ClusteringPipeline:
    """Main clustering pipeline coordinator"""

    def __init__(self, stages: List[BaseClusteringStage]):
        self.stages = stages
        self.logger = structlog.get_logger(__name__)

    async def run_clustering_pipeline(
        self, articles: List[Dict[str, Any]]
    ) -> List[ClusteringResult]:
        """Run the complete clustering pipeline"""
        results = []
        current_articles = articles.copy()

        self.logger.info(
            "Starting clustering pipeline",
            stages=len(self.stages),
            articles=len(articles),
        )

        for stage in self.stages:
            try:
                self.logger.info(
                    "Starting clustering stage",
                    stage=stage.stage.value,
                    articles=len(current_articles),
                )

                result = await stage.cluster_articles(current_articles)
                results.append(result)

                # Update articles with cluster assignments for next stage
                current_articles = await self._prepare_articles_for_next_stage(
                    current_articles, result
                )

                self.logger.info(
                    "Clustering stage completed",
                    stage=stage.stage.value,
                    clusters=len(result.clusters),
                    processing_time=result.processing_time_seconds,
                )

            except Exception as e:
                self.logger.error(
                    "Clustering stage failed", stage=stage.stage.value, error=str(e)
                )
                # Continue with next stage even if one fails
                continue

        self.logger.info("Clustering pipeline completed", total_stages=len(results))

        return results

    async def _prepare_articles_for_next_stage(
        self, articles: List[Dict[str, Any]], clustering_result: ClusteringResult
    ) -> List[Dict[str, Any]]:
        """Prepare articles for the next clustering stage"""

        # Create a mapping of article IDs to cluster assignments
        article_to_cluster = {}
        for cluster in clustering_result.clusters:
            for article_id in cluster.articles:
                article_to_cluster[article_id] = cluster.cluster_id

        # Update articles with cluster information
        updated_articles = []
        for article in articles:
            article_id = article.get("id", str(hash(article.get("url", ""))))

            # Add cluster assignment to article metadata
            cluster_assignments = article.get("cluster_assignments", {})
            cluster_assignments[clustering_result.stage.value] = article_to_cluster.get(
                article_id
            )

            updated_article = article.copy()
            updated_article["cluster_assignments"] = cluster_assignments

            updated_articles.append(updated_article)

        return updated_articles


class ClusterMerger:
    """Utility class for merging similar clusters"""

    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.logger = structlog.get_logger(__name__)

    async def merge_similar_clusters(
        self, clusters: List[ClusterInfo], merge_threshold: Optional[float] = None
    ) -> List[ClusterInfo]:
        """Merge clusters that are too similar"""

        threshold = merge_threshold or self.similarity_threshold

        if len(clusters) < 2:
            return clusters

        self.logger.info(
            "Starting cluster merging", clusters=len(clusters), threshold=threshold
        )

        # Calculate cluster similarities
        merged_clusters = []
        processed_indices = set()

        for i, cluster_a in enumerate(clusters):
            if i in processed_indices:
                continue

            # Start with current cluster
            merged_cluster = cluster_a
            articles_to_merge = list(cluster_a.articles)

            # Find similar clusters to merge
            for j, cluster_b in enumerate(clusters[i + 1 :], i + 1):
                if j in processed_indices:
                    continue

                similarity = await self._calculate_cluster_similarity(
                    cluster_a, cluster_b
                )

                if similarity >= threshold:
                    self.logger.debug(
                        "Merging clusters",
                        cluster_a=cluster_a.cluster_id,
                        cluster_b=cluster_b.cluster_id,
                        similarity=similarity,
                    )

                    articles_to_merge.extend(cluster_b.articles)
                    processed_indices.add(j)

            # Create merged cluster if necessary
            if len(articles_to_merge) > len(cluster_a.articles):
                merged_cluster = await self._create_merged_cluster(
                    [cluster_a] + [clusters[j] for j in processed_indices if j > i],
                    articles_to_merge,
                )

            merged_clusters.append(merged_cluster)
            processed_indices.add(i)

        self.logger.info(
            "Cluster merging completed",
            original_clusters=len(clusters),
            merged_clusters=len(merged_clusters),
        )

        return merged_clusters

    async def _calculate_cluster_similarity(
        self, cluster_a: ClusterInfo, cluster_b: ClusterInfo
    ) -> float:
        """Calculate similarity between two clusters"""

        similarities = []

        # Centroid similarity (if available)
        if cluster_a.centroid is not None and cluster_b.centroid is not None:
            centroid_sim = cosine_similarity(
                cluster_a.centroid.reshape(1, -1), cluster_b.centroid.reshape(1, -1)
            )[0][0]
            similarities.append(centroid_sim * 0.4)  # 40% weight

        # Topic similarity
        topics_a = set(cluster_a.dominant_topics)
        topics_b = set(cluster_b.dominant_topics)

        if topics_a and topics_b:
            topic_similarity = len(topics_a & topics_b) / len(topics_a | topics_b)
            similarities.append(topic_similarity * 0.3)  # 30% weight

        # Entity similarity
        entities_a = self._extract_entity_names(cluster_a.key_entities)
        entities_b = self._extract_entity_names(cluster_b.key_entities)

        if entities_a and entities_b:
            entity_similarity = len(entities_a & entities_b) / len(
                entities_a | entities_b
            )
            similarities.append(entity_similarity * 0.2)  # 20% weight

        # Temporal similarity
        time_diff = abs(cluster_a.temporal_span_hours - cluster_b.temporal_span_hours)
        temporal_similarity = max(0, 1 - (time_diff / 24))  # Similar if within 24h
        similarities.append(temporal_similarity * 0.1)  # 10% weight

        return sum(similarities) if similarities else 0.0

    def _extract_entity_names(self, key_entities: Dict[str, Any]) -> Set[str]:
        """Extract entity names from key entities structure"""
        entity_names = set()

        for entity_type, entities in key_entities.items():
            for entity_info in entities:
                if isinstance(entity_info, dict):
                    name = entity_info.get("entity", "")
                else:
                    name = str(entity_info)

                if name:
                    entity_names.add(name.lower())

        return entity_names

    async def _create_merged_cluster(
        self, original_clusters: List[ClusterInfo], all_articles: List[str]
    ) -> ClusterInfo:
        """Create a new cluster by merging existing clusters"""

        # Use the first cluster as base
        base_cluster = original_clusters[0]

        # Merge centroids (average)
        centroids = [c.centroid for c in original_clusters if c.centroid is not None]
        merged_centroid = np.mean(centroids, axis=0) if centroids else None

        # Merge topics
        all_topics = []
        for cluster in original_clusters:
            all_topics.extend(cluster.dominant_topics)

        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        merged_topics = [
            topic
            for topic, count in sorted(
                topic_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        # Merge entities
        merged_entities = {}
        for cluster in original_clusters:
            for entity_type, entities in cluster.key_entities.items():
                if entity_type not in merged_entities:
                    merged_entities[entity_type] = {}

                for entity_info in entities:
                    entity_name = entity_info.get("entity", "")
                    count = entity_info.get("count", 1)

                    merged_entities[entity_type][entity_name] = (
                        merged_entities[entity_type].get(entity_name, 0) + count
                    )

        # Convert back to list format
        final_entities = {}
        for entity_type, entities in merged_entities.items():
            sorted_entities = sorted(entities.items(), key=lambda x: x[1], reverse=True)
            final_entities[entity_type] = [
                {"entity": entity, "count": count}
                for entity, count in sorted_entities[:5]
            ]

        return ClusterInfo(
            cluster_id=f"merged_{base_cluster.cluster_id}",
            stage=base_cluster.stage,
            articles=all_articles,
            centroid=merged_centroid,
            coherence_score=np.mean([c.coherence_score for c in original_clusters]),
            dominant_topics=merged_topics,
            key_entities=final_entities,
            sentiment_distribution=base_cluster.sentiment_distribution,  # Use base for now
            language_distribution=base_cluster.language_distribution,
            source_distribution=base_cluster.source_distribution,
            temporal_span_hours=max(c.temporal_span_hours for c in original_clusters),
            metadata={
                "article_count": len(all_articles),
                "merged_from": [c.cluster_id for c in original_clusters],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
