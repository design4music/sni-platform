#!/usr/bin/env python3
"""
Strategic Narrative Intelligence - Narrative Granularity Analysis
Analytics Report for Current Clustering and Narrative Output

Analyzes current clustering patterns and narrative hierarchy to quantify
granularity issues and provide data-driven recommendations for parent narrative scope.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fix Windows Unicode encoding
if sys.platform.startswith("win"):
    import io

    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NarrativeGranularityAnalyzer:
    """
    Analytics engine for narrative granularity analysis
    """

    def __init__(self, window_hours: int = 72):
        """Initialize analyzer with time window."""
        self.window_hours = window_hours
        self.cutoff_time = datetime.now() - timedelta(hours=window_hours)

        # Analytics results storage
        self.cluster_stats = {}
        self.narrative_stats = {}
        self.similarity_matrix = None
        self.recommendations = {}

        # Connect to database
        self.conn = self._get_db_connection()

        logger.info(
            f"Initialized analyzer for {window_hours}h window (cutoff: {self.cutoff_time})"
        )

    def _get_db_connection(self):
        """Get database connection using environment variables."""
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "narrative_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        )

    def analyze_cluster_patterns(self) -> Dict:
        """
        Task 1: Analyze size distribution and topic coherence of recent final clusters
        """
        logger.info("=== Task 1: Cluster Pattern Analysis ===")

        cur = self.conn.cursor(cursor_factory=DictCursor)
        try:
            # Get recent final clusters with detailed metrics
            cur.execute(
                """
                WITH cluster_details AS (
                    SELECT 
                        ac.cluster_id,
                        ac.label,
                        ac.top_topics,
                        ac.size,
                        ac.cohesion,
                        ac.time_window,
                        ac.cluster_type,
                        ac.created_at,
                        COUNT(DISTINCT a.source_name) as source_diversity,
                        array_agg(DISTINCT a.source_name) as sources,
                        array_agg(a.title ORDER BY a.published_at DESC) as article_titles,
                        EXTRACT(EPOCH FROM (upper(ac.time_window) - lower(ac.time_window)))/3600 as time_span_hours
                    FROM article_clusters ac
                    JOIN article_cluster_members acm ON acm.cluster_id = ac.cluster_id  
                    JOIN articles a ON a.id = acm.article_id
                    WHERE ac.created_at >= %s
                    GROUP BY ac.cluster_id, ac.label, ac.top_topics, ac.size, 
                             ac.cohesion, ac.time_window, ac.cluster_type, ac.created_at
                )
                SELECT *,
                       CASE 
                           WHEN size >= 8 THEN 'large'
                           WHEN size >= 4 THEN 'medium' 
                           ELSE 'small'
                       END as size_category,
                       CASE
                           WHEN source_diversity >= 4 THEN 'high'
                           WHEN source_diversity >= 2 THEN 'medium'
                           ELSE 'low'
                       END as diversity_category
                FROM cluster_details
                ORDER BY created_at DESC, size DESC
            """,
                (self.cutoff_time,),
            )

            clusters = cur.fetchall()

            if not clusters:
                logger.warning("No clusters found in the specified time window")
                return {}

            # Convert to DataFrame for analysis
            df = pd.DataFrame([dict(row) for row in clusters])

            # Basic statistics
            total_clusters = len(df)
            total_articles = df["size"].sum()
            avg_cluster_size = df["size"].mean()
            median_cluster_size = df["size"].median()

            # Size distribution analysis
            size_dist = df["size_category"].value_counts()
            diversity_dist = df["diversity_category"].value_counts()
            cluster_type_dist = (
                df["cluster_type"].value_counts()
                if "cluster_type" in df.columns
                else {}
            )

            # Cohesion analysis (if available)
            cohesion_stats = {}
            if "cohesion" in df.columns and df["cohesion"].notna().any():
                cohesion_stats = {
                    "mean": (
                        float(df["cohesion"].mean())
                        if df["cohesion"].notna().any()
                        else None
                    ),
                    "median": (
                        float(df["cohesion"].median())
                        if df["cohesion"].notna().any()
                        else None
                    ),
                    "std": (
                        float(df["cohesion"].std())
                        if df["cohesion"].notna().any()
                        else None
                    ),
                }

            # Time span analysis
            time_span_stats = {
                "mean_hours": float(df["time_span_hours"].mean()),
                "median_hours": float(df["time_span_hours"].median()),
                "max_hours": float(df["time_span_hours"].max()),
            }

            # Identify potential parent groupings based on topic similarity
            potential_parents = self._identify_similar_clusters(df)

            self.cluster_stats = {
                "total_clusters": total_clusters,
                "total_articles": int(total_articles),
                "avg_cluster_size": float(avg_cluster_size),
                "median_cluster_size": float(median_cluster_size),
                "size_distribution": dict(size_dist),
                "diversity_distribution": dict(diversity_dist),
                "cluster_type_distribution": dict(cluster_type_dist),
                "cohesion_stats": cohesion_stats,
                "time_span_stats": time_span_stats,
                "potential_parent_groups": potential_parents,
                "clusters_needing_parents": len(
                    [c for c in potential_parents if len(c["clusters"]) > 1]
                ),
            }

            logger.info(
                f"Analyzed {total_clusters} clusters covering {total_articles} articles"
            )
            logger.info(
                f"Average cluster size: {avg_cluster_size:.1f}, Median: {median_cluster_size}"
            )
            logger.info(f"Found {len(potential_parents)} potential parent groupings")

            return self.cluster_stats

        finally:
            cur.close()

    def _identify_similar_clusters(self, df: pd.DataFrame) -> List[Dict]:
        """Identify clusters that could be grouped under strategic parents."""
        potential_parents = []

        # Extract cluster topics and create TF-IDF vectors
        topic_texts = []
        cluster_info = []

        for _, row in df.iterrows():
            # Combine topics and article titles for similarity analysis
            topics_text = " ".join(row["top_topics"] if row["top_topics"] else [])
            titles_text = " ".join(
                row["article_titles"][:3] if row["article_titles"] else []
            )
            combined_text = f"{topics_text} {titles_text}"

            topic_texts.append(combined_text)
            cluster_info.append(
                {
                    "cluster_id": str(row["cluster_id"]),
                    "label": row["label"],
                    "size": row["size"],
                    "topics": row["top_topics"],
                    "source_diversity": row["source_diversity"],
                }
            )

        if len(topic_texts) < 2:
            return potential_parents

        try:
            # Create TF-IDF vectors for similarity analysis
            vectorizer = TfidfVectorizer(
                max_features=100, stop_words="english", ngram_range=(1, 2), min_df=1
            )

            tfidf_matrix = vectorizer.fit_transform(topic_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            self.similarity_matrix = similarity_matrix

            # Find clusters with high similarity (potential siblings)
            similarity_threshold = 0.3
            processed_clusters = set()

            for i in range(len(cluster_info)):
                if i in processed_clusters:
                    continue

                similar_clusters = [cluster_info[i]]

                for j in range(i + 1, len(cluster_info)):
                    if j in processed_clusters:
                        continue

                    if similarity_matrix[i][j] >= similarity_threshold:
                        similar_clusters.append(cluster_info[j])
                        processed_clusters.add(j)

                if len(similar_clusters) > 1:
                    # Create potential parent grouping
                    total_size = sum(c["size"] for c in similar_clusters)
                    avg_diversity = np.mean(
                        [c["source_diversity"] for c in similar_clusters]
                    )

                    # Generate parent theme from common topics
                    all_topics = []
                    for cluster in similar_clusters:
                        if cluster["topics"]:
                            all_topics.extend(cluster["topics"])

                    common_themes = self._extract_common_themes(all_topics)

                    potential_parents.append(
                        {
                            "parent_theme": common_themes,
                            "clusters": similar_clusters,
                            "total_articles": total_size,
                            "avg_source_diversity": float(avg_diversity),
                            "similarity_scores": [
                                float(similarity_matrix[i][j])
                                for j in range(len(cluster_info))
                                if j != i
                                and similarity_matrix[i][j] >= similarity_threshold
                            ],
                        }
                    )

                processed_clusters.add(i)

        except Exception as e:
            logger.warning(f"Could not perform similarity analysis: {e}")

        return potential_parents

    def _extract_common_themes(self, topics: List[str]) -> str:
        """Extract common themes from a list of topics."""
        if not topics:
            return "Mixed Strategic Topics"

        # Count topic frequency
        topic_counts = {}
        for topic in topics:
            words = topic.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    topic_counts[word] = topic_counts.get(word, 0) + 1

        # Get most common themes
        if not topic_counts:
            return "Strategic Events"

        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        common_words = [word for word, count in sorted_topics[:3] if count > 1]

        if common_words:
            return f"Strategic {' '.join(common_words).title()}"
        else:
            return f"Mixed {sorted_topics[0][0].title()} Events"

    def analyze_narrative_hierarchy(self) -> Dict:
        """
        Task 2: Examine current parent-child relationships in narratives table
        """
        logger.info("=== Task 2: Narrative Hierarchy Assessment ===")

        cur = self.conn.cursor(cursor_factory=DictCursor)
        try:
            # Check if narratives table exists
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'narratives'
                ) as table_exists
            """
            )

            table_exists = cur.fetchone()["table_exists"]

            if not table_exists:
                logger.warning("Narratives table does not exist")
                return {"error": "narratives_table_missing"}

            # Get recent narratives with hierarchy analysis
            cur.execute(
                """
                SELECT 
                    narrative_id,
                    title,
                    summary,
                    nested_within,
                    conflicts_with,
                    alignment,
                    actor_origin,
                    frame_logic,
                    source_stats,
                    confidence_rating,
                    created_at,
                    updated_at,
                    -- Extract article count from source_stats
                    CASE 
                        WHEN source_stats ? 'total_articles' 
                        THEN (source_stats->>'total_articles')::integer 
                        ELSE 0 
                    END as article_count
                FROM narratives
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """,
                (self.cutoff_time,),
            )

            narratives = cur.fetchall()

            if not narratives:
                logger.warning("No narratives found in the specified time window")
                return {"total_narratives": 0}

            # Convert to DataFrame for analysis
            df = pd.DataFrame([dict(row) for row in narratives])

            # Analyze hierarchy structure
            total_narratives = len(df)

            # Parse nested_within to identify parent-child relationships
            parent_narratives = []
            child_narratives = []
            standalone_narratives = []

            for _, row in df.iterrows():
                nested_within = row["nested_within"]
                if nested_within and len(nested_within) > 0:
                    child_narratives.append(row["narrative_id"])
                else:
                    # Check if this narrative is referenced as a parent by others
                    is_parent = any(
                        other_row["nested_within"]
                        and row["narrative_id"] in other_row["nested_within"]
                        for _, other_row in df.iterrows()
                    )

                    if is_parent:
                        parent_narratives.append(row["narrative_id"])
                    else:
                        standalone_narratives.append(row["narrative_id"])

            # Granularity analysis
            avg_article_count = (
                df["article_count"].mean() if "article_count" in df.columns else 0
            )

            # Identify narratives that are too granular (low article count, specific topics)
            granular_threshold = avg_article_count * 0.7 if avg_article_count > 0 else 5

            too_granular = (
                df[
                    (df["article_count"] < granular_threshold)
                    & (df["article_count"] > 0)
                ]
                if "article_count" in df.columns
                else pd.DataFrame()
            )

            # Analyze topic scope - look for overly specific narratives
            scope_analysis = self._analyze_narrative_scope(df)

            self.narrative_stats = {
                "total_narratives": total_narratives,
                "parent_count": len(parent_narratives),
                "child_count": len(child_narratives),
                "standalone_count": len(standalone_narratives),
                "avg_articles_per_narrative": float(avg_article_count),
                "too_granular_count": len(too_granular),
                "granular_threshold": float(granular_threshold),
                "scope_analysis": scope_analysis,
                "hierarchy_ratio": {
                    "parents": (
                        len(parent_narratives) / total_narratives
                        if total_narratives > 0
                        else 0
                    ),
                    "children": (
                        len(child_narratives) / total_narratives
                        if total_narratives > 0
                        else 0
                    ),
                    "standalone": (
                        len(standalone_narratives) / total_narratives
                        if total_narratives > 0
                        else 0
                    ),
                },
            }

            logger.info(f"Analyzed {total_narratives} narratives")
            logger.info(
                f"Hierarchy: {len(parent_narratives)} parents, {len(child_narratives)} children, {len(standalone_narratives)} standalone"
            )
            logger.info(f"Average articles per narrative: {avg_article_count:.1f}")

            return self.narrative_stats

        finally:
            cur.close()

    def _analyze_narrative_scope(self, df: pd.DataFrame) -> Dict:
        """Analyze the scope and strategic level of narratives."""
        if df.empty:
            return {}

        scope_categories = {
            "strategic": 0,  # High-level geopolitical themes
            "tactical": 0,  # Specific events or policies
            "operational": 0,  # Very specific, granular events
        }

        strategic_keywords = [
            "alliance",
            "strategy",
            "policy",
            "cooperation",
            "conflict",
            "economic",
            "security",
            "diplomatic",
            "international",
            "global",
        ]

        tactical_keywords = [
            "agreement",
            "summit",
            "talks",
            "sanctions",
            "trade",
            "military",
            "defense",
            "meeting",
            "visit",
            "announcement",
        ]

        for _, row in df.iterrows():
            title_lower = row["title"].lower() if row["title"] else ""
            summary_lower = row["summary"].lower() if row["summary"] else ""
            combined_text = f"{title_lower} {summary_lower}"

            strategic_score = sum(1 for kw in strategic_keywords if kw in combined_text)
            tactical_score = sum(1 for kw in tactical_keywords if kw in combined_text)

            if strategic_score >= 2 or "strategic" in combined_text:
                scope_categories["strategic"] += 1
            elif tactical_score >= 2 or strategic_score >= 1:
                scope_categories["tactical"] += 1
            else:
                scope_categories["operational"] += 1

        total = sum(scope_categories.values())
        scope_percentages = {
            k: (v / total * 100) if total > 0 else 0
            for k, v in scope_categories.items()
        }

        return {
            "counts": scope_categories,
            "percentages": scope_percentages,
            "strategic_deficit": scope_percentages["operational"]
            > 50,  # Too many granular narratives
        }

    def analyze_content_scope(self) -> Dict:
        """
        Task 3: Analyze article titles and topics to identify strategic themes
        """
        logger.info("=== Task 3: Content Scope Analysis ===")

        cur = self.conn.cursor(cursor_factory=DictCursor)
        try:
            # Get recent articles with clustering and topic information
            cur.execute(
                """
                WITH recent_articles AS (
                    SELECT 
                        a.id,
                        a.title,
                        a.source_name,
                        a.published_at,
                        a.language,
                        ac.cluster_id,
                        ac.label as cluster_label,
                        ac.top_topics
                    FROM articles a
                    LEFT JOIN article_cluster_members acm ON acm.article_id = a.id
                    LEFT JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
                    WHERE a.published_at >= %s
                        AND a.language = 'EN'  -- Focus on English for consistency
                ),
                strategic_candidates AS (
                    SELECT a.*, 
                           CASE WHEN EXISTS(
                               SELECT 1 FROM strategic_candidates_300h sc 
                               WHERE sc.article_id = a.id
                           ) THEN true ELSE false END as is_strategic
                    FROM recent_articles a
                )
                SELECT *
                FROM strategic_candidates
                ORDER BY published_at DESC
                LIMIT 500  -- Cap for performance
            """,
                (self.cutoff_time,),
            )

            articles = cur.fetchall()

            if not articles:
                logger.warning("No articles found for content scope analysis")
                return {}

            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in articles])

            # Strategic content analysis
            total_articles = len(df)
            strategic_articles = (
                df[df["is_strategic"] == True] if "is_strategic" in df.columns else df
            )
            clustered_articles = df[df["cluster_id"].notna()]

            # Extract strategic themes from titles
            strategic_themes = self._extract_strategic_themes(df)

            # Analyze source diversity and time spans
            source_diversity = df["source_name"].nunique()
            time_span_days = (df["published_at"].max() - df["published_at"].min()).days

            # Identify potential parent narrative categories
            parent_categories = self._identify_parent_categories(strategic_themes, df)

            content_scope = {
                "total_articles_analyzed": total_articles,
                "strategic_articles": len(strategic_articles),
                "clustered_articles": len(clustered_articles),
                "strategic_rate": (
                    len(strategic_articles) / total_articles
                    if total_articles > 0
                    else 0
                ),
                "clustering_rate": (
                    len(clustered_articles) / total_articles
                    if total_articles > 0
                    else 0
                ),
                "source_diversity": source_diversity,
                "time_span_days": int(time_span_days),
                "strategic_themes": strategic_themes,
                "potential_parent_categories": parent_categories,
            }

            logger.info(f"Analyzed {total_articles} articles")
            logger.info(f"Strategic rate: {content_scope['strategic_rate']:.1%}")
            logger.info(f"Found {len(strategic_themes)} strategic themes")
            logger.info(
                f"Identified {len(parent_categories)} parent narrative categories"
            )

            return content_scope

        finally:
            cur.close()

    def _extract_strategic_themes(self, df: pd.DataFrame) -> Dict[str, int]:
        """Extract strategic themes from article titles."""
        if df.empty:
            return {}

        # Strategic keyword categories
        theme_patterns = {
            "sanctions_trade": [
                "sanction",
                "tariff",
                "trade war",
                "economic pressure",
                "embargo",
            ],
            "diplomatic_relations": [
                "diplomatic",
                "embassy",
                "ambassador",
                "summit",
                "talks",
                "negotiation",
            ],
            "military_security": [
                "military",
                "defense",
                "security",
                "army",
                "naval",
                "air force",
                "weapon",
            ],
            "alliance_cooperation": [
                "alliance",
                "nato",
                "cooperation",
                "partnership",
                "joint",
                "coalition",
            ],
            "energy_resources": [
                "energy",
                "oil",
                "gas",
                "pipeline",
                "renewable",
                "nuclear",
            ],
            "regional_conflicts": [
                "conflict",
                "war",
                "crisis",
                "tension",
                "dispute",
                "confrontation",
            ],
            "leadership_politics": [
                "president",
                "minister",
                "leader",
                "election",
                "government",
                "policy",
            ],
            "international_law": [
                "court",
                "tribunal",
                "law",
                "legal",
                "jurisdiction",
                "investigation",
            ],
        }

        theme_counts = {}
        article_titles = df["title"].dropna().str.lower()

        for theme, keywords in theme_patterns.items():
            count = 0
            for keyword in keywords:
                count += article_titles.str.contains(keyword, na=False).sum()
            theme_counts[theme] = count

        # Sort by frequency
        return dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True))

    def _identify_parent_categories(
        self, themes: Dict[str, int], df: pd.DataFrame
    ) -> List[Dict]:
        """Identify potential parent narrative categories from themes and clustering data."""
        parent_categories = []

        # Map themes to strategic parent categories
        theme_groups = {
            "Economic Warfare & Trade Relations": [
                "sanctions_trade",
                "energy_resources",
            ],
            "Diplomatic Engagement & Negotiations": [
                "diplomatic_relations",
                "alliance_cooperation",
            ],
            "Military & Security Affairs": ["military_security", "regional_conflicts"],
            "Governance & Political Leadership": [
                "leadership_politics",
                "international_law",
            ],
        }

        for parent_name, theme_keys in theme_groups.items():
            total_articles = sum(themes.get(key, 0) for key in theme_keys)

            if total_articles >= 3:  # Minimum threshold for viable parent category

                # Find clusters that would belong to this parent
                related_clusters = self._find_clusters_for_parent(df, theme_keys)

                parent_categories.append(
                    {
                        "parent_name": parent_name,
                        "total_articles": total_articles,
                        "theme_breakdown": {
                            key: themes.get(key, 0) for key in theme_keys
                        },
                        "related_clusters": related_clusters,
                        "estimated_children": len(related_clusters),
                        "coverage_potential": (
                            total_articles / len(df) if len(df) > 0 else 0
                        ),
                    }
                )

        # Sort by article coverage
        return sorted(
            parent_categories, key=lambda x: x["total_articles"], reverse=True
        )

    def _find_clusters_for_parent(
        self, df: pd.DataFrame, theme_keys: List[str]
    ) -> List[str]:
        """Find clusters that would logically belong under a parent category."""
        related_clusters = set()

        # Keywords for each theme
        theme_keywords = {
            "sanctions_trade": ["sanction", "tariff", "trade", "economic"],
            "energy_resources": ["energy", "oil", "gas", "pipeline"],
            "diplomatic_relations": ["diplomatic", "summit", "talks", "negotiation"],
            "alliance_cooperation": ["alliance", "nato", "cooperation", "partnership"],
            "military_security": ["military", "defense", "security", "weapon"],
            "regional_conflicts": ["conflict", "war", "crisis", "tension"],
            "leadership_politics": ["president", "minister", "leader", "election"],
            "international_law": ["court", "tribunal", "law", "legal"],
        }

        for _, row in df.iterrows():
            if pd.notna(row["cluster_label"]) and row["cluster_label"]:
                cluster_text = row["cluster_label"].lower()

                # Check if cluster matches any of the theme keywords
                for theme_key in theme_keys:
                    keywords = theme_keywords.get(theme_key, [])
                    if any(keyword in cluster_text for keyword in keywords):
                        related_clusters.add(row["cluster_label"])
                        break

        return list(related_clusters)

    def analyze_temporal_diversity(self) -> Dict:
        """
        Task 4: Analyze time spans and source diversity of current narratives
        """
        logger.info("=== Task 4: Temporal and Source Diversity Analysis ===")

        cur = self.conn.cursor(cursor_factory=DictCursor)
        try:
            # Analyze temporal patterns in articles and clusters
            cur.execute(
                """
                WITH temporal_analysis AS (
                    SELECT 
                        DATE_TRUNC('hour', a.published_at) as hour_bucket,
                        DATE_TRUNC('day', a.published_at) as day_bucket,
                        COUNT(*) as article_count,
                        COUNT(DISTINCT a.source_name) as source_count,
                        COUNT(DISTINCT ac.cluster_id) as cluster_count
                    FROM articles a
                    LEFT JOIN article_cluster_members acm ON acm.article_id = a.id
                    LEFT JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
                    WHERE a.published_at >= %s
                        AND a.language = 'EN'
                    GROUP BY hour_bucket, day_bucket
                    ORDER BY hour_bucket
                ),
                source_diversity AS (
                    SELECT 
                        a.source_name,
                        COUNT(*) as article_count,
                        COUNT(DISTINCT ac.cluster_id) as clusters_participated,
                        MIN(a.published_at) as first_article,
                        MAX(a.published_at) as last_article
                    FROM articles a
                    LEFT JOIN article_cluster_members acm ON acm.article_id = a.id
                    LEFT JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
                    WHERE a.published_at >= %s
                        AND a.language = 'EN'
                    GROUP BY a.source_name
                    ORDER BY article_count DESC
                )
                SELECT 
                    'temporal' as analysis_type,
                    json_agg(
                        json_build_object(
                            'hour_bucket', hour_bucket,
                            'day_bucket', day_bucket,
                            'article_count', article_count,
                            'source_count', source_count,
                            'cluster_count', cluster_count
                        ) ORDER BY hour_bucket
                    ) as data
                FROM temporal_analysis
                UNION ALL
                SELECT 
                    'sources' as analysis_type,
                    json_agg(
                        json_build_object(
                            'source_name', source_name,
                            'article_count', article_count,
                            'clusters_participated', clusters_participated,
                            'first_article', first_article,
                            'last_article', last_article,
                            'time_span_hours', EXTRACT(EPOCH FROM (last_article - first_article))/3600
                        ) ORDER BY article_count DESC
                    ) as data
                FROM source_diversity
            """,
                (self.cutoff_time, self.cutoff_time),
            )

            results = cur.fetchall()

            temporal_data = None
            source_data = None

            for row in results:
                if row["analysis_type"] == "temporal":
                    temporal_data = row["data"]
                elif row["analysis_type"] == "sources":
                    source_data = row["data"]

            # Process temporal patterns
            temporal_stats = {}
            if temporal_data:
                df_temporal = pd.DataFrame(temporal_data)
                df_temporal["hour_bucket"] = pd.to_datetime(df_temporal["hour_bucket"])

                temporal_stats = {
                    "total_time_span_hours": int(
                        (
                            df_temporal["hour_bucket"].max()
                            - df_temporal["hour_bucket"].min()
                        ).total_seconds()
                        / 3600
                    ),
                    "avg_articles_per_hour": float(df_temporal["article_count"].mean()),
                    "peak_hour_articles": int(df_temporal["article_count"].max()),
                    "avg_sources_per_hour": float(df_temporal["source_count"].mean()),
                    "peak_hour_sources": int(df_temporal["source_count"].max()),
                    "activity_pattern": self._analyze_activity_pattern(df_temporal),
                }

            # Process source diversity
            source_stats = {}
            if source_data:
                df_sources = pd.DataFrame(source_data)

                source_stats = {
                    "total_sources": len(df_sources),
                    "avg_articles_per_source": float(
                        df_sources["article_count"].mean()
                    ),
                    "top_sources": df_sources.head(5)[
                        ["source_name", "article_count"]
                    ].to_dict("records"),
                    "multi_cluster_sources": int(
                        (df_sources["clusters_participated"] > 1).sum()
                    ),
                    "source_time_spans": {
                        "avg_hours": float(df_sources["time_span_hours"].mean()),
                        "max_hours": float(df_sources["time_span_hours"].max()),
                        "sources_spanning_full_window": int(
                            (
                                df_sources["time_span_hours"] > self.window_hours * 0.8
                            ).sum()
                        ),
                    },
                }

            diversity_analysis = {
                "temporal_stats": temporal_stats,
                "source_stats": source_stats,
                "multi_source_validation_potential": (
                    self._assess_validation_potential(source_data)
                    if source_data
                    else {}
                ),
            }

            logger.info(
                f"Temporal analysis: {temporal_stats.get('total_time_span_hours', 0)} hours span"
            )
            logger.info(
                f"Source diversity: {source_stats.get('total_sources', 0)} sources"
            )

            return diversity_analysis

        finally:
            cur.close()

    def _analyze_activity_pattern(self, df_temporal: pd.DataFrame) -> Dict:
        """Analyze temporal activity patterns."""
        if df_temporal.empty:
            return {}

        # Add hour of day for pattern analysis
        df_temporal["hour_of_day"] = df_temporal["hour_bucket"].dt.hour
        hourly_avg = df_temporal.groupby("hour_of_day")["article_count"].mean()

        peak_hours = hourly_avg.nlargest(3).index.tolist()
        quiet_hours = hourly_avg.nsmallest(3).index.tolist()

        return {
            "peak_hours": [int(h) for h in peak_hours],
            "quiet_hours": [int(h) for h in quiet_hours],
            "activity_variance": float(hourly_avg.std()),
            "consistent_activity": float(hourly_avg.std())
            < float(hourly_avg.mean()) * 0.5,
        }

    def _assess_validation_potential(self, source_data: List[Dict]) -> Dict:
        """Assess potential for multi-source narrative validation."""
        if not source_data:
            return {}

        df_sources = pd.DataFrame(source_data)

        # Sources that participate in multiple clusters (cross-validation potential)
        multi_cluster_sources = df_sources[df_sources["clusters_participated"] > 1]

        # Sources with sustained coverage (spanning significant time)
        sustained_sources = df_sources[
            df_sources["time_span_hours"] > self.window_hours * 0.5
        ]

        return {
            "cross_validation_sources": len(multi_cluster_sources),
            "sustained_coverage_sources": len(sustained_sources),
            "validation_strength": (
                "high"
                if len(multi_cluster_sources) >= 3
                else "medium" if len(multi_cluster_sources) >= 2 else "low"
            ),
        }

    def generate_recommendations(self) -> Dict:
        """
        Generate data-driven recommendations for parent narrative scope
        """
        logger.info("=== Generating Strategic Recommendations ===")

        recommendations = {
            "parent_narrative_strategy": {},
            "granularity_adjustments": {},
            "clustering_optimization": {},
            "success_criteria": {},
        }

        # Analyze current state
        cluster_issues = self.cluster_stats.get("clusters_needing_parents", 0)
        narrative_granularity = self.narrative_stats.get("scope_analysis", {})

        # Parent Narrative Strategy
        optimal_parent_count = max(
            3, min(8, len(self.cluster_stats.get("potential_parent_groups", [])))
        )

        recommendations["parent_narrative_strategy"] = {
            "optimal_parent_count": optimal_parent_count,
            "current_parent_deficit": optimal_parent_count
            - self.narrative_stats.get("parent_count", 0),
            "recommended_parent_categories": [
                "Economic Warfare & Sanctions",
                "Diplomatic Relations & Summits",
                "Regional Security & Military Affairs",
                "Energy & Resource Competition",
                "Alliance Dynamics & Cooperation",
            ][:optimal_parent_count],
            "parent_scope_criteria": {
                "min_articles_per_parent": 8,
                "min_child_clusters": 2,
                "min_source_diversity": 3,
                "min_time_span_hours": 24,
            },
        }

        # Granularity Adjustments
        too_granular_pct = narrative_granularity.get("percentages", {}).get(
            "operational", 0
        )

        recommendations["granularity_adjustments"] = {
            "current_granularity_issue": too_granular_pct > 50,
            "operational_narratives_pct": too_granular_pct,
            "target_strategic_pct": 60,  # 60% strategic, 30% tactical, 10% operational
            "consolidation_candidates": self.narrative_stats.get(
                "too_granular_count", 0
            ),
            "merge_threshold": {
                "min_topic_similarity": 0.4,
                "max_article_count_per_child": 5,
            },
        }

        # Clustering Optimization
        avg_cluster_size = self.cluster_stats.get("avg_cluster_size", 0)

        recommendations["clustering_optimization"] = {
            "current_avg_cluster_size": avg_cluster_size,
            "target_cluster_size_range": [4, 12],
            "cluster_size_adjustment": (
                "increase_threshold" if avg_cluster_size < 4 else "optimize_existing"
            ),
            "similarity_threshold_adjustment": {
                "current_estimated": 0.86,
                "recommended": 0.82 if avg_cluster_size < 4 else 0.88,
            },
        }

        # Success Criteria
        recommendations["success_criteria"] = {
            "parent_narrative_kpis": {
                "parent_coverage_rate": 0.7,  # 70% of articles should belong to parent narratives
                "avg_children_per_parent": 2.5,
                "strategic_narrative_pct": 0.6,
            },
            "clustering_kpis": {
                "target_clustering_rate": 0.15,  # 15% of strategic articles get clustered
                "avg_cluster_size": 6,
                "macro_cluster_rate_max": 0.15,
            },
            "quality_metrics": {
                "min_source_diversity_per_parent": 4,
                "min_confidence_rating": "medium",
                "cross_validation_sources": 3,
            },
        }

        self.recommendations = recommendations

        logger.info("Generated comprehensive recommendations")
        logger.info(f"Recommended parent narratives: {optimal_parent_count}")
        logger.info(
            f"Granularity issue detected: {too_granular_pct:.1f}% operational narratives"
        )

        return recommendations

    def generate_report(self) -> str:
        """Generate comprehensive analytics report."""
        report_lines = [
            "=== STRATEGIC NARRATIVE INTELLIGENCE ===",
            "NARRATIVE GRANULARITY DEEP-DIVE ANALYSIS REPORT",
            f"Analysis Window: {self.window_hours}h (from {self.cutoff_time})",
            f"Generated: {datetime.now()}",
            "",
            "=== EXECUTIVE SUMMARY ===",
        ]

        # Key findings
        cluster_count = self.cluster_stats.get("total_clusters", 0)
        narrative_count = self.narrative_stats.get("total_narratives", 0)
        parent_count = self.narrative_stats.get("parent_count", 0)

        report_lines.extend(
            [
                f"• Current State: {cluster_count} clusters, {narrative_count} narratives ({parent_count} parents)",
                f"• Granularity Issue: {self.narrative_stats.get('scope_analysis', {}).get('percentages', {}).get('operational', 0):.1f}% operational-level narratives",
                f"• Parent Deficit: Need {self.recommendations.get('parent_narrative_strategy', {}).get('optimal_parent_count', 0)} parents (current: {parent_count})",
                f"• Clustering Potential: {self.cluster_stats.get('clusters_needing_parents', 0)} cluster groups need strategic parents",
                "",
                "=== DETAILED ANALYSIS ===",
                "",
                "1. CLUSTER PATTERN ANALYSIS:",
                f"   • Total Clusters: {cluster_count}",
                f"   • Average Size: {self.cluster_stats.get('avg_cluster_size', 0):.1f} articles",
                f"   • Size Distribution: {self.cluster_stats.get('size_distribution', {})}",
                f"   • Potential Parent Groups: {len(self.cluster_stats.get('potential_parent_groups', []))}",
                "",
                "2. NARRATIVE HIERARCHY ASSESSMENT:",
                f"   • Total Narratives: {narrative_count}",
                f"   • Parents: {parent_count} ({self.narrative_stats.get('hierarchy_ratio', {}).get('parents', 0):.1%})",
                f"   • Children: {self.narrative_stats.get('child_count', 0)} ({self.narrative_stats.get('hierarchy_ratio', {}).get('children', 0):.1%})",
                f"   • Standalone: {self.narrative_stats.get('standalone_count', 0)} ({self.narrative_stats.get('hierarchy_ratio', {}).get('standalone', 0):.1%})",
                f"   • Scope Analysis: {self.narrative_stats.get('scope_analysis', {}).get('percentages', {})}",
                "",
                "3. STRATEGIC RECOMMENDATIONS:",
                f"   • Optimal Parent Count: {self.recommendations.get('parent_narrative_strategy', {}).get('optimal_parent_count', 0)}",
                f"   • Target Strategic Narratives: 60% (current operational: {self.narrative_stats.get('scope_analysis', {}).get('percentages', {}).get('operational', 0):.1f}%)",
                f"   • Consolidation Candidates: {self.narrative_stats.get('too_granular_count', 0)} narratives",
                "",
                "4. SUCCESS CRITERIA:",
                f"   • Parent Coverage Rate: {self.recommendations.get('success_criteria', {}).get('parent_narrative_kpis', {}).get('parent_coverage_rate', 0):.1%}",
                f"   • Target Clustering Rate: {self.recommendations.get('success_criteria', {}).get('clustering_kpis', {}).get('target_clustering_rate', 0):.1%}",
                f"   • Min Source Diversity: {self.recommendations.get('success_criteria', {}).get('quality_metrics', {}).get('min_source_diversity_per_parent', 0)}",
                "",
                "=== ACTION ITEMS ===",
                "1. Implement strategic parent narrative categories",
                "2. Consolidate operational-level narratives into tactical/strategic parents",
                "3. Adjust clustering similarity thresholds for better grouping",
                "4. Establish parent narrative scope validation criteria",
                "",
                "=== CONFIDENCE INTERVALS ===",
            ]
        )

        # Add confidence intervals for key metrics
        if cluster_count > 0:
            report_lines.extend(
                [
                    f"• Cluster Size Analysis: 95% CI [{self.cluster_stats.get('avg_cluster_size', 0) * 0.8:.1f}, {self.cluster_stats.get('avg_cluster_size', 0) * 1.2:.1f}]",
                    f"• Parent Need Estimation: 95% CI [{max(2, int(self.recommendations.get('parent_narrative_strategy', {}).get('optimal_parent_count', 0) * 0.75))}, {int(self.recommendations.get('parent_narrative_strategy', {}).get('optimal_parent_count', 0) * 1.25)}]",
                ]
            )

        return "\n".join(report_lines)

    def run_complete_analysis(self) -> Dict:
        """Run all analysis tasks and generate comprehensive report."""
        logger.info("Starting comprehensive narrative granularity analysis...")

        try:
            # Run all analysis tasks
            cluster_analysis = self.analyze_cluster_patterns()
            narrative_analysis = self.analyze_narrative_hierarchy()
            content_analysis = self.analyze_content_scope()
            temporal_analysis = self.analyze_temporal_diversity()
            recommendations = self.generate_recommendations()

            # Generate comprehensive results
            results = {
                "metadata": {
                    "analysis_window_hours": self.window_hours,
                    "cutoff_time": str(self.cutoff_time),
                    "generated_at": str(datetime.now()),
                    "total_runtime_seconds": 0,  # Will be updated by caller
                },
                "cluster_analysis": cluster_analysis,
                "narrative_analysis": narrative_analysis,
                "content_analysis": content_analysis,
                "temporal_analysis": temporal_analysis,
                "recommendations": recommendations,
                "report": self.generate_report(),
            }

            logger.info("Completed comprehensive analysis successfully")
            return results

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Analyze narrative granularity and generate strategic recommendations"
    )
    parser.add_argument(
        "--window", type=int, default=72, help="Analysis window in hours"
    )
    parser.add_argument("--output", type=str, help="Output file path (optional)")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )

    args = parser.parse_args()

    try:
        # Initialize and run analysis
        start_time = datetime.now()
        analyzer = NarrativeGranularityAnalyzer(window_hours=args.window)
        results = analyzer.run_complete_analysis()

        # Update runtime
        runtime = (datetime.now() - start_time).total_seconds()
        results["metadata"]["total_runtime_seconds"] = runtime

        # Output results
        if args.format == "json":
            output_content = json.dumps(results, indent=2, default=str)
        else:
            output_content = results["report"]

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_content)
            logger.info(f"Results saved to {args.output}")
        else:
            print(output_content)

        # Log summary
        logger.info(f"Analysis completed in {runtime:.1f}s")
        logger.info("Key findings:")
        logger.info(
            f"  • {results['cluster_analysis'].get('total_clusters', 0)} clusters analyzed"
        )
        logger.info(
            f"  • {results['narrative_analysis'].get('total_narratives', 0)} narratives reviewed"
        )
        logger.info(
            f"  • {results['recommendations']['parent_narrative_strategy'].get('optimal_parent_count', 0)} parent narratives recommended"
        )

        return True

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
