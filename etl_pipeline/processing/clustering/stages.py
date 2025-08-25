"""
Implementation of the 4 clustering stages
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import structlog
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .base import (BaseClusteringStage, ClusterInfo, ClusteringResult,
                   ClusteringStage, ClusterMerger)

logger = structlog.get_logger(__name__)


class Stage1ThematicClustering(BaseClusteringStage):
    """CLUST-1: Thematic clustering based on content similarity"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ClusteringStage.CLUST_1_THEMATIC, config)

        # DBSCAN parameters
        self.eps = config.get("eps", 0.3)
        self.min_samples = config.get("min_samples", 3)
        self.metric = config.get("metric", "cosine")

        # Feature extraction settings
        self.use_title_embeddings = config.get("use_title_embeddings", True)
        self.use_content_embeddings = config.get("use_content_embeddings", True)
        self.use_entities = config.get("use_entities", True)

        self.title_weight = config.get("title_weight", 0.4)
        self.content_weight = config.get("content_weight", 0.4)
        self.entity_weight = config.get("entity_weight", 0.2)

    async def cluster_articles(
        self, articles: List[Dict[str, Any]]
    ) -> ClusteringResult:
        """Perform thematic clustering"""
        start_time = datetime.now(timezone.utc)

        self.logger.info(
            "Starting thematic clustering",
            articles=len(articles),
            eps=self.eps,
            min_samples=self.min_samples,
        )

        try:
            # Extract features
            features = await self.get_cluster_features(articles)

            if features is None or len(features) == 0:
                return self._create_empty_result(start_time, len(articles))

            # Perform DBSCAN clustering
            clusterer = DBSCAN(
                eps=self.eps, min_samples=self.min_samples, metric=self.metric
            )

            cluster_labels = clusterer.fit_predict(features)

            # Process clustering results
            clusters = await self._process_cluster_labels(
                articles, features, cluster_labels
            )

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = ClusteringResult(
                stage=self.stage,
                clusters=clusters,
                processing_time_seconds=processing_time,
                items_processed=len(articles),
                items_clustered=sum(len(c.articles) for c in clusters),
                items_failed=len(articles) - sum(len(c.articles) for c in clusters),
                metadata={
                    "algorithm": "dbscan",
                    "eps": self.eps,
                    "min_samples": self.min_samples,
                    "n_clusters": len(clusters),
                    "n_noise": len([l for l in cluster_labels if l == -1]),
                },
            )

            self.logger.info(
                "Thematic clustering completed",
                clusters=len(clusters),
                processing_time=processing_time,
            )

            return result

        except Exception as e:
            self.logger.error("Thematic clustering failed", error=str(e))
            return self._create_empty_result(start_time, len(articles))

    async def get_cluster_features(
        self, articles: List[Dict[str, Any]]
    ) -> Optional[np.ndarray]:
        """Extract features for thematic clustering"""
        try:
            features_list = []

            for article in articles:
                article_features = []

                # Title embeddings
                if self.use_title_embeddings and self.embedding_model:
                    title = article.get("title", "")
                    if title:
                        title_embedding = self.embedding_model.encode([title])[0]
                        article_features.append(title_embedding * self.title_weight)

                # Content embeddings
                if self.use_content_embeddings and self.embedding_model:
                    content = article.get("content", "")
                    if content:
                        # Truncate content if too long
                        content = content[:2000]
                        content_embedding = self.embedding_model.encode([content])[0]
                        article_features.append(content_embedding * self.content_weight)

                # Entity features
                if self.use_entities:
                    entity_features = await self._extract_entity_features(article)
                    if entity_features is not None:
                        article_features.append(entity_features * self.entity_weight)

                # Combine features
                if article_features:
                    combined_features = np.concatenate(article_features)
                    features_list.append(combined_features)
                else:
                    # Use zero vector if no features available
                    embedding_dim = (
                        self.embedding_model.get_sentence_embedding_dimension()
                    )
                    features_list.append(np.zeros(embedding_dim))

            if not features_list:
                return None

            return np.array(features_list)

        except Exception as e:
            self.logger.error("Feature extraction failed", error=str(e))
            return None

    async def _extract_entity_features(
        self, article: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """Extract entity-based features"""
        try:
            entities = article.get("entities", {})
            if not entities:
                return None

            # Create entity text for embedding
            entity_texts = []
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    if isinstance(entity, dict):
                        entity_text = entity.get("text", "")
                    else:
                        entity_text = str(entity)

                    if entity_text:
                        entity_texts.append(f"{entity_type}: {entity_text}")

            if not entity_texts:
                return None

            # Encode entities
            entity_embeddings = self.embedding_model.encode(entity_texts)

            # Average entity embeddings
            return np.mean(entity_embeddings, axis=0)

        except Exception as e:
            self.logger.error("Entity feature extraction failed", error=str(e))
            return None

    async def _process_cluster_labels(
        self, articles: List[Dict[str, Any]], features: np.ndarray, labels: np.ndarray
    ) -> List[ClusterInfo]:
        """Process clustering results into ClusterInfo objects"""

        clusters = []
        unique_labels = set(labels)

        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue

            # Get articles for this cluster
            cluster_indices = np.where(labels == label)[0]
            cluster_articles = [articles[i] for i in cluster_indices]
            cluster_features = features[cluster_indices]

            # Create cluster info
            cluster_info = await self.create_cluster_info(
                cluster_id=f"thematic_{label}",
                articles=cluster_articles,
                features=cluster_features,
            )

            clusters.append(cluster_info)

        return clusters

    def _create_empty_result(
        self, start_time: datetime, item_count: int
    ) -> ClusteringResult:
        """Create empty result for failed clustering"""
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        return ClusteringResult(
            stage=self.stage,
            clusters=[],
            processing_time_seconds=processing_time,
            items_processed=item_count,
            items_clustered=0,
            items_failed=item_count,
            metadata={"error": "clustering_failed"},
        )


class Stage2InterpretiveClustering(BaseClusteringStage):
    """CLUST-2: Interpretive clustering based on narrative elements"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ClusteringStage.CLUST_2_INTERPRETIVE, config)

        # Agglomerative clustering parameters
        self.n_clusters = config.get("n_clusters", None)
        self.distance_threshold = config.get("distance_threshold", 0.4)
        self.linkage = config.get("linkage", "ward")

        # Feature weights
        self.sentiment_weight = config.get("sentiment_weight", 0.3)
        self.topic_weight = config.get("topic_weight", 0.4)
        self.narrative_weight = config.get("narrative_weight", 0.3)

    async def cluster_articles(
        self, articles: List[Dict[str, Any]]
    ) -> ClusteringResult:
        """Perform interpretive clustering"""
        start_time = datetime.now(timezone.utc)

        self.logger.info(
            "Starting interpretive clustering",
            articles=len(articles),
            distance_threshold=self.distance_threshold,
        )

        try:
            # Extract interpretive features
            features = await self.get_cluster_features(articles)

            if features is None or len(features) == 0:
                return self._create_empty_result(start_time, len(articles))

            # Perform agglomerative clustering
            clusterer = AgglomerativeClustering(
                n_clusters=self.n_clusters,
                distance_threshold=self.distance_threshold,
                linkage=self.linkage,
            )

            cluster_labels = clusterer.fit_predict(features)

            # Process results
            clusters = await self._process_cluster_labels(
                articles, features, cluster_labels
            )

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = ClusteringResult(
                stage=self.stage,
                clusters=clusters,
                processing_time_seconds=processing_time,
                items_processed=len(articles),
                items_clustered=sum(len(c.articles) for c in clusters),
                items_failed=len(articles) - sum(len(c.articles) for c in clusters),
                metadata={
                    "algorithm": "agglomerative",
                    "n_clusters": len(clusters),
                    "distance_threshold": self.distance_threshold,
                    "linkage": self.linkage,
                },
            )

            self.logger.info(
                "Interpretive clustering completed",
                clusters=len(clusters),
                processing_time=processing_time,
            )

            return result

        except Exception as e:
            self.logger.error("Interpretive clustering failed", error=str(e))
            return self._create_empty_result(start_time, len(articles))

    async def get_cluster_features(
        self, articles: List[Dict[str, Any]]
    ) -> Optional[np.ndarray]:
        """Extract interpretive features"""
        try:
            features_list = []

            for article in articles:
                article_features = []

                # Sentiment features
                sentiment_features = self._extract_sentiment_features(article)
                article_features.append(sentiment_features * self.sentiment_weight)

                # Topic features
                topic_features = await self._extract_topic_features(article)
                article_features.append(topic_features * self.topic_weight)

                # Narrative element features
                narrative_features = await self._extract_narrative_features(article)
                article_features.append(narrative_features * self.narrative_weight)

                # Combine features
                combined_features = np.concatenate(article_features)
                features_list.append(combined_features)

            if not features_list:
                return None

            return np.array(features_list)

        except Exception as e:
            self.logger.error("Interpretive feature extraction failed", error=str(e))
            return None

    def _extract_sentiment_features(self, article: Dict[str, Any]) -> np.ndarray:
        """Extract sentiment-based features"""
        sentiment = article.get("sentiment", {})

        # Default sentiment values
        features = np.array([0.0, 0.0, 0.0, 0.0])  # pos, neg, neu, confidence

        if isinstance(sentiment, dict):
            label = sentiment.get("label", "neutral").lower()
            confidence = sentiment.get("confidence", 0.5)

            if label == "positive":
                features[0] = confidence
            elif label == "negative":
                features[1] = confidence
            else:
                features[2] = confidence

            features[3] = confidence

        return features

    async def _extract_topic_features(self, article: Dict[str, Any]) -> np.ndarray:
        """Extract topic-based features"""
        topics = article.get("topics", [])

        # Define common topic categories
        topic_categories = [
            "politics",
            "economy",
            "technology",
            "sports",
            "entertainment",
            "health",
            "science",
            "environment",
            "business",
            "international",
        ]

        features = np.zeros(len(topic_categories))

        for i, category in enumerate(topic_categories):
            # Check if any article topics match this category
            for topic in topics:
                if category in topic.lower():
                    features[i] = 1.0
                    break

        return features

    async def _extract_narrative_features(self, article: Dict[str, Any]) -> np.ndarray:
        """Extract narrative element features"""

        # Basic narrative elements to detect
        narrative_elements = [
            "conflict",
            "resolution",
            "cause",
            "effect",
            "temporal",
            "actor",
            "action",
            "consequence",
            "trend",
            "anomaly",
        ]

        features = np.zeros(len(narrative_elements))

        # Simple keyword-based detection (could be enhanced with NLP)
        content = (article.get("title", "") + " " + article.get("content", "")).lower()

        # Conflict indicators
        conflict_words = ["conflict", "war", "fight", "dispute", "tension", "crisis"]
        if any(word in content for word in conflict_words):
            features[0] = 1.0

        # Resolution indicators
        resolution_words = ["resolved", "solution", "agreement", "settled", "peace"]
        if any(word in content for word in resolution_words):
            features[1] = 1.0

        # Cause indicators
        cause_words = ["because", "due to", "caused by", "resulted from", "led to"]
        if any(word in content for word in cause_words):
            features[2] = 1.0

        # Effect indicators
        effect_words = ["therefore", "consequently", "as a result", "impact", "effect"]
        if any(word in content for word in effect_words):
            features[3] = 1.0

        # Temporal indicators
        temporal_words = ["before", "after", "during", "while", "when", "since"]
        if any(word in content for word in temporal_words):
            features[4] = 1.0

        # Actor indicators (entities)
        entities = article.get("entities", {})
        if entities.get("PERSON") or entities.get("ORG"):
            features[5] = 1.0

        # Action indicators
        action_words = ["announced", "declared", "launched", "started", "ended"]
        if any(word in content for word in action_words):
            features[6] = 1.0

        # Consequence indicators
        consequence_words = ["outcome", "result", "consequence", "aftermath"]
        if any(word in content for word in consequence_words):
            features[7] = 1.0

        # Trend indicators
        trend_words = ["increasing", "decreasing", "growing", "declining", "rising"]
        if any(word in content for word in trend_words):
            features[8] = 1.0

        # Anomaly indicators
        anomaly_words = ["unusual", "unexpected", "surprising", "unprecedented", "rare"]
        if any(word in content for word in anomaly_words):
            features[9] = 1.0

        return features

    async def _process_cluster_labels(
        self, articles: List[Dict[str, Any]], features: np.ndarray, labels: np.ndarray
    ) -> List[ClusterInfo]:
        """Process clustering results"""
        clusters = []
        unique_labels = set(labels)

        for label in unique_labels:
            cluster_indices = np.where(labels == label)[0]
            cluster_articles = [articles[i] for i in cluster_indices]
            cluster_features = features[cluster_indices]

            cluster_info = await self.create_cluster_info(
                cluster_id=f"interpretive_{label}",
                articles=cluster_articles,
                features=cluster_features,
            )

            clusters.append(cluster_info)

        return clusters

    def _create_empty_result(
        self, start_time: datetime, item_count: int
    ) -> ClusteringResult:
        """Create empty result for failed clustering"""
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        return ClusteringResult(
            stage=self.stage,
            clusters=[],
            processing_time_seconds=processing_time,
            items_processed=item_count,
            items_clustered=0,
            items_failed=item_count,
            metadata={"error": "clustering_failed"},
        )


class Stage3TemporalAnomalyClustering(BaseClusteringStage):
    """CLUST-3: Temporal anomaly detection clustering"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ClusteringStage.CLUST_3_TEMPORAL_ANOMALY, config)

        # Isolation Forest parameters
        self.contamination = config.get("contamination", 0.1)
        self.time_window_hours = config.get("time_window_hours", 24)

        # Feature weights
        self.temporal_weight = config.get("temporal_weight", 0.4)
        self.engagement_weight = config.get("engagement_weight", 0.3)
        self.source_weight = config.get("source_weight", 0.3)

    async def cluster_articles(
        self, articles: List[Dict[str, Any]]
    ) -> ClusteringResult:
        """Perform temporal anomaly clustering"""
        start_time = datetime.now(timezone.utc)

        self.logger.info(
            "Starting temporal anomaly clustering",
            articles=len(articles),
            contamination=self.contamination,
            time_window_hours=self.time_window_hours,
        )

        try:
            # Extract temporal features
            features = await self.get_cluster_features(articles)

            if features is None or len(features) == 0:
                return self._create_empty_result(start_time, len(articles))

            # Perform anomaly detection
            detector = IsolationForest(
                contamination=self.contamination, random_state=42
            )

            anomaly_labels = detector.fit_predict(features)

            # Process results (1 = normal, -1 = anomaly)
            clusters = await self._process_anomaly_labels(
                articles, features, anomaly_labels
            )

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = ClusteringResult(
                stage=self.stage,
                clusters=clusters,
                processing_time_seconds=processing_time,
                items_processed=len(articles),
                items_clustered=sum(len(c.articles) for c in clusters),
                items_failed=len(articles) - sum(len(c.articles) for c in clusters),
                metadata={
                    "algorithm": "isolation_forest",
                    "contamination": self.contamination,
                    "n_anomalies": len([l for l in anomaly_labels if l == -1]),
                    "n_normal": len([l for l in anomaly_labels if l == 1]),
                },
            )

            self.logger.info(
                "Temporal anomaly clustering completed",
                clusters=len(clusters),
                processing_time=processing_time,
            )

            return result

        except Exception as e:
            self.logger.error("Temporal anomaly clustering failed", error=str(e))
            return self._create_empty_result(start_time, len(articles))

    async def get_cluster_features(
        self, articles: List[Dict[str, Any]]
    ) -> Optional[np.ndarray]:
        """Extract temporal anomaly features"""
        try:
            features_list = []
            current_time = datetime.now(timezone.utc)

            for article in articles:
                article_features = []

                # Temporal features
                temporal_features = self._extract_temporal_features(
                    article, current_time
                )
                article_features.append(temporal_features * self.temporal_weight)

                # Engagement features
                engagement_features = self._extract_engagement_features(article)
                article_features.append(engagement_features * self.engagement_weight)

                # Source reliability features
                source_features = self._extract_source_features(article)
                article_features.append(source_features * self.source_weight)

                # Combine features
                combined_features = np.concatenate(article_features)
                features_list.append(combined_features)

            if not features_list:
                return None

            # Normalize features
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(np.array(features_list))

            return normalized_features

        except Exception as e:
            self.logger.error(
                "Temporal anomaly feature extraction failed", error=str(e)
            )
            return None

    def _extract_temporal_features(
        self, article: Dict[str, Any], current_time: datetime
    ) -> np.ndarray:
        """Extract temporal-based features"""

        # Get publication time
        published_at = article.get("published_at")
        if isinstance(published_at, str):
            from dateutil import parser

            published_at = parser.parse(published_at)

        if not published_at:
            published_at = current_time

        # Time since publication (hours)
        time_since_pub = (current_time - published_at).total_seconds() / 3600

        # Hour of day (0-23)
        hour_of_day = published_at.hour

        # Day of week (0-6)
        day_of_week = published_at.weekday()

        # Is weekend
        is_weekend = 1.0 if day_of_week >= 5 else 0.0

        # Publishing velocity (articles per hour from same source)
        # This would require additional data, using placeholder
        publishing_velocity = 1.0

        return np.array(
            [
                time_since_pub,
                hour_of_day / 24.0,  # Normalize
                day_of_week / 7.0,  # Normalize
                is_weekend,
                publishing_velocity,
            ]
        )

    def _extract_engagement_features(self, article: Dict[str, Any]) -> np.ndarray:
        """Extract engagement-based features"""

        # These features would typically come from external data
        # Using placeholders based on article characteristics

        # Content length as proxy for engagement potential
        content_length = len(article.get("content", ""))
        title_length = len(article.get("title", ""))

        # Sentiment as engagement indicator
        sentiment = article.get("sentiment", {})
        sentiment_score = 0.5  # Neutral default

        if isinstance(sentiment, dict):
            label = sentiment.get("label", "neutral").lower()
            confidence = sentiment.get("confidence", 0.5)

            if label == "positive":
                sentiment_score = 0.5 + (confidence * 0.5)
            elif label == "negative":
                sentiment_score = 0.5 - (confidence * 0.5)

        # Entity count as complexity indicator
        entities = article.get("entities", {})
        entity_count = sum(len(entity_list) for entity_list in entities.values())

        # Has multimedia (placeholder)
        has_image = 1.0 if article.get("metadata", {}).get("url_to_image") else 0.0

        return np.array(
            [
                min(content_length / 5000, 1.0),  # Normalize to 0-1
                min(title_length / 200, 1.0),  # Normalize to 0-1
                sentiment_score,
                min(entity_count / 20, 1.0),  # Normalize to 0-1
                has_image,
            ]
        )

    def _extract_source_features(self, article: Dict[str, Any]) -> np.ndarray:
        """Extract source reliability features"""

        # Source reliability score (would come from source database)
        source_name = article.get("source_name", "unknown")

        # Simple reliability scoring based on known sources
        reliable_sources = {
            "reuters",
            "bbc",
            "ap",
            "guardian",
            "nytimes",
            "wsj",
            "bloomberg",
            "cnn",
            "npr",
        }

        source_reliability = (
            0.8
            if any(reliable in source_name.lower() for reliable in reliable_sources)
            else 0.5
        )

        # Source category
        source_type = article.get("metadata", {}).get("source_type", "unknown")
        is_api_source = 1.0 if source_type in ["newsapi", "guardian_api"] else 0.0

        # Language as reliability indicator
        language = article.get("language", "unknown")
        is_english = 1.0 if language == "en" else 0.0

        # Has author
        has_author = 1.0 if article.get("author") else 0.0

        # Content completeness
        has_content = 1.0 if article.get("content") else 0.0

        return np.array(
            [source_reliability, is_api_source, is_english, has_author, has_content]
        )

    async def _process_anomaly_labels(
        self, articles: List[Dict[str, Any]], features: np.ndarray, labels: np.ndarray
    ) -> List[ClusterInfo]:
        """Process anomaly detection results"""
        clusters = []

        # Separate normal and anomalous articles
        normal_indices = np.where(labels == 1)[0]
        anomaly_indices = np.where(labels == -1)[0]

        # Create normal cluster
        if len(normal_indices) > 0:
            normal_articles = [articles[i] for i in normal_indices]
            normal_features = features[normal_indices]

            normal_cluster = await self.create_cluster_info(
                cluster_id="temporal_normal",
                articles=normal_articles,
                features=normal_features,
            )
            normal_cluster.metadata["cluster_type"] = "normal"
            clusters.append(normal_cluster)

        # Create anomaly cluster
        if len(anomaly_indices) > 0:
            anomaly_articles = [articles[i] for i in anomaly_indices]
            anomaly_features = features[anomaly_indices]

            anomaly_cluster = await self.create_cluster_info(
                cluster_id="temporal_anomaly",
                articles=anomaly_articles,
                features=anomaly_features,
            )
            anomaly_cluster.metadata["cluster_type"] = "anomaly"
            clusters.append(anomaly_cluster)

        return clusters

    def _create_empty_result(
        self, start_time: datetime, item_count: int
    ) -> ClusteringResult:
        """Create empty result for failed clustering"""
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        return ClusteringResult(
            stage=self.stage,
            clusters=[],
            processing_time_seconds=processing_time,
            items_processed=item_count,
            items_clustered=0,
            items_failed=item_count,
            metadata={"error": "clustering_failed"},
        )


class Stage4ConsolidationClustering(BaseClusteringStage):
    """CLUST-4: Consolidation clustering combining all previous stages"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(ClusteringStage.CLUST_4_CONSOLIDATION, config)

        # Hierarchical clustering parameters
        self.merge_threshold = config.get("merge_threshold", 0.6)
        self.max_clusters = config.get("max_clusters", 50)

        # Feature weights from previous stages
        self.thematic_weight = config.get("thematic_weight", 0.3)
        self.interpretive_weight = config.get("interpretive_weight", 0.3)
        self.temporal_weight = config.get("temporal_weight", 0.2)
        self.final_embedding_weight = config.get("final_embedding_weight", 0.2)

        # Initialize cluster merger
        self.cluster_merger = ClusterMerger(self.merge_threshold)

    async def cluster_articles(
        self, articles: List[Dict[str, Any]]
    ) -> ClusteringResult:
        """Perform consolidation clustering"""
        start_time = datetime.now(timezone.utc)

        self.logger.info(
            "Starting consolidation clustering",
            articles=len(articles),
            merge_threshold=self.merge_threshold,
            max_clusters=self.max_clusters,
        )

        try:
            # Group articles by previous cluster assignments
            cluster_groups = await self._group_by_previous_clusters(articles)

            # Create initial clusters from previous stages
            initial_clusters = []
            cluster_id = 0

            for group_key, group_articles in cluster_groups.items():
                if (
                    len(group_articles) >= 1
                ):  # Allow single-article clusters in final stage
                    features = await self.get_cluster_features(group_articles)

                    cluster_info = await self.create_cluster_info(
                        cluster_id=f"consolidated_{cluster_id}",
                        articles=group_articles,
                        features=features,
                    )
                    cluster_info.metadata["group_key"] = group_key
                    initial_clusters.append(cluster_info)
                    cluster_id += 1

            # Merge similar clusters
            final_clusters = await self.cluster_merger.merge_similar_clusters(
                initial_clusters, self.merge_threshold
            )

            # Limit number of clusters if specified
            if self.max_clusters and len(final_clusters) > self.max_clusters:
                final_clusters = await self._reduce_clusters(
                    final_clusters, self.max_clusters
                )

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = ClusteringResult(
                stage=self.stage,
                clusters=final_clusters,
                processing_time_seconds=processing_time,
                items_processed=len(articles),
                items_clustered=sum(len(c.articles) for c in final_clusters),
                items_failed=len(articles)
                - sum(len(c.articles) for c in final_clusters),
                metadata={
                    "algorithm": "hierarchical_consolidation",
                    "initial_clusters": len(initial_clusters),
                    "final_clusters": len(final_clusters),
                    "merge_threshold": self.merge_threshold,
                    "max_clusters": self.max_clusters,
                },
            )

            self.logger.info(
                "Consolidation clustering completed",
                initial_clusters=len(initial_clusters),
                final_clusters=len(final_clusters),
                processing_time=processing_time,
            )

            return result

        except Exception as e:
            self.logger.error("Consolidation clustering failed", error=str(e))
            return self._create_empty_result(start_time, len(articles))

    async def get_cluster_features(
        self, articles: List[Dict[str, Any]]
    ) -> Optional[np.ndarray]:
        """Extract consolidation features combining all previous stages"""
        try:
            if not articles:
                return None

            features_list = []

            for article in articles:
                article_features = []

                # Get cluster assignments from all previous stages
                cluster_assignments = article.get("cluster_assignments", {})

                # Create feature vector from cluster assignments
                assignment_features = self._encode_cluster_assignments(
                    cluster_assignments
                )
                article_features.append(assignment_features)

                # Add final content embedding
                if self.embedding_model:
                    content = (
                        article.get("title", "") + " " + article.get("content", "")
                    )
                    if content.strip():
                        content_embedding = self.embedding_model.encode(
                            [content[:1000]]
                        )[0]
                        article_features.append(
                            content_embedding * self.final_embedding_weight
                        )

                # Combine all features
                if article_features:
                    combined_features = np.concatenate(article_features)
                    features_list.append(combined_features)

            if not features_list:
                return None

            return np.array(features_list)

        except Exception as e:
            self.logger.error("Consolidation feature extraction failed", error=str(e))
            return None

    def _encode_cluster_assignments(
        self, cluster_assignments: Dict[str, Any]
    ) -> np.ndarray:
        """Encode cluster assignments as feature vector"""

        # Create feature vector for cluster assignments
        features = []

        # Thematic clustering assignment
        thematic_cluster = cluster_assignments.get("clust_1_thematic")
        if thematic_cluster:
            # Simple hash-based encoding (could be more sophisticated)
            thematic_feature = hash(str(thematic_cluster)) % 100 / 100.0
        else:
            thematic_feature = 0.0
        features.append(thematic_feature * self.thematic_weight)

        # Interpretive clustering assignment
        interpretive_cluster = cluster_assignments.get("clust_2_interpretive")
        if interpretive_cluster:
            interpretive_feature = hash(str(interpretive_cluster)) % 100 / 100.0
        else:
            interpretive_feature = 0.0
        features.append(interpretive_feature * self.interpretive_weight)

        # Temporal anomaly assignment
        temporal_cluster = cluster_assignments.get("clust_3_temporal_anomaly")
        if temporal_cluster:
            # Encode as anomaly (1) or normal (0)
            temporal_feature = 1.0 if "anomaly" in str(temporal_cluster) else 0.0
        else:
            temporal_feature = 0.5  # Unknown
        features.append(temporal_feature * self.temporal_weight)

        return np.array(features)

    async def _group_by_previous_clusters(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group articles by their previous cluster assignments"""

        groups = defaultdict(list)

        for article in articles:
            cluster_assignments = article.get("cluster_assignments", {})

            # Create grouping key from all cluster assignments
            key_parts = []

            for stage in [
                "clust_1_thematic",
                "clust_2_interpretive",
                "clust_3_temporal_anomaly",
            ]:
                assignment = cluster_assignments.get(stage, "none")
                key_parts.append(f"{stage}:{assignment}")

            group_key = "|".join(key_parts)
            groups[group_key].append(article)

        return dict(groups)

    async def _reduce_clusters(
        self, clusters: List[ClusterInfo], max_clusters: int
    ) -> List[ClusterInfo]:
        """Reduce number of clusters by merging smallest/least coherent ones"""

        if len(clusters) <= max_clusters:
            return clusters

        # Sort clusters by coherence score (descending) and size (descending)
        sorted_clusters = sorted(
            clusters, key=lambda c: (c.coherence_score, len(c.articles)), reverse=True
        )

        # Keep top clusters
        kept_clusters = sorted_clusters[: max_clusters - 1]

        # Merge remaining clusters into a single "miscellaneous" cluster
        remaining_clusters = sorted_clusters[max_clusters - 1 :]

        if remaining_clusters:
            all_articles = []
            for cluster in remaining_clusters:
                all_articles.extend(cluster.articles)

            misc_cluster = await self.create_cluster_info(
                cluster_id="consolidated_miscellaneous", articles=all_articles
            )
            misc_cluster.metadata["cluster_type"] = "miscellaneous"
            misc_cluster.metadata["merged_from"] = [
                c.cluster_id for c in remaining_clusters
            ]

            kept_clusters.append(misc_cluster)

        return kept_clusters

    def _create_empty_result(
        self, start_time: datetime, item_count: int
    ) -> ClusteringResult:
        """Create empty result for failed clustering"""
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        return ClusteringResult(
            stage=self.stage,
            clusters=[],
            processing_time_seconds=processing_time,
            items_processed=item_count,
            items_clustered=0,
            items_failed=item_count,
            metadata={"error": "clustering_failed"},
        )
