#!/usr/bin/env python3
"""
Curation Trigger Analyzer
Strategic Narrative Intelligence ETL Pipeline

Analyzes CLUST-1 outputs to identify opportunities for manual parent narrative creation.
Provides intelligent suggestions for strategic consolidation based on thematic clustering.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from etl_pipeline.core.database import get_db_session

logger = structlog.get_logger(__name__)


class CurationTriggerAnalyzer:
    """
    Analyzes clustering outputs to identify strategic parent narrative opportunities

    Key Functions:
    1. Thematic density analysis - clusters sharing strategic keywords
    2. Temporal clustering - related themes emerging simultaneously
    3. Strategic keyword monitoring - high-priority terms requiring consolidation
    4. Source diversity validation - cross-source thematic confirmation
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize analyzer with database session"""
        self.session = session or get_db_session()
        self.logger = logger.bind(component="curation_trigger_analyzer")

        # Strategic keywords that indicate consolidation opportunities
        self.strategic_keywords = {
            "geopolitical": [
                "russia",
                "putin",
                "china",
                "ukraine",
                "nato",
                "sanctions",
                "diplomacy",
            ],
            "security": [
                "military",
                "defense",
                "weapons",
                "nuclear",
                "cyber",
                "intelligence",
            ],
            "economic": [
                "energy",
                "oil",
                "gas",
                "trade",
                "tariffs",
                "supply chain",
                "inflation",
            ],
            "technology": [
                "ai",
                "semiconductors",
                "tech",
                "innovation",
                "cyber",
                "space",
            ],
        }

    def analyze_daily_triggers(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Analyze recent clusters for consolidation opportunities

        Args:
            days_back: Number of days to analyze for clustering patterns

        Returns:
            List of trigger recommendations ranked by priority
        """
        self.logger.info("Starting daily trigger analysis", days_back=days_back)

        # Get recent clusters from the specified timeframe
        cutoff_date = datetime.now() - timedelta(days=days_back)
        clusters = self._get_recent_clusters(cutoff_date)

        if not clusters:
            self.logger.warning("No recent clusters found for analysis")
            return []

        triggers = []

        # Analyze different trigger types
        triggers.extend(self._analyze_thematic_density(clusters))
        triggers.extend(self._analyze_temporal_clustering(clusters))
        triggers.extend(self._analyze_strategic_keywords(clusters))
        triggers.extend(self._analyze_source_diversity(clusters))

        # Rank and prioritize triggers
        prioritized_triggers = self._prioritize_triggers(triggers)

        self.logger.info(
            "Trigger analysis completed",
            total_clusters=len(clusters),
            triggers_found=len(prioritized_triggers),
        )

        return prioritized_triggers

    def _get_recent_clusters(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Get clusters created after cutoff date with metadata"""
        try:
            result = self.session.execute(
                text(
                    """
                    SELECT 
                        cluster_id,
                        label,
                        top_topics,
                        size,
                        created_at,
                        strategic_status,
                        -- Get sample articles for source diversity analysis
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'source', a.source_name,
                                    'published_at', a.published_at,
                                    'title', a.title
                                )
                            )
                            FROM articles a
                            JOIN article_cluster_members acm ON a.id = acm.article_id  
                            WHERE acm.cluster_id = ac.cluster_id
                            LIMIT 10
                        ) as sample_articles
                    FROM article_clusters ac
                    WHERE created_at >= :cutoff_date
                    AND strategic_status IN ('pending', 'strategic')
                    AND size >= 3  -- Only consider clusters with meaningful size
                    ORDER BY created_at DESC
                """
                ),
                {"cutoff_date": cutoff_date},
            ).fetchall()

            clusters = []
            for row in result:
                cluster = {
                    "cluster_id": str(row.cluster_id),
                    "label": row.label,
                    "keywords": row.top_topics or [],
                    "size": row.size,
                    "created_at": row.created_at,
                    "strategic_status": row.strategic_status,
                    "sample_articles": (
                        json.loads(row.sample_articles) if row.sample_articles else []
                    ),
                }
                clusters.append(cluster)

            return clusters

        except Exception as e:
            self.logger.error("Failed to get recent clusters", error=str(e))
            return []

    def _analyze_thematic_density(
        self, clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find clusters with significant keyword overlap indicating consolidation opportunity"""
        triggers = []

        # Group clusters by shared keywords
        keyword_groups = {}

        for cluster in clusters:
            keywords = set(cluster["keywords"][:5])  # Use top 5 keywords

            for keyword in keywords:
                if keyword not in keyword_groups:
                    keyword_groups[keyword] = []
                keyword_groups[keyword].append(cluster)

        # Find keyword groups with multiple clusters
        for keyword, cluster_list in keyword_groups.items():
            if len(cluster_list) >= 3:  # At least 3 clusters sharing keyword

                # Calculate thematic coherence score
                coherence_score = self._calculate_thematic_coherence(
                    cluster_list, keyword
                )

                if coherence_score >= 0.6:  # Threshold for consolidation
                    trigger = {
                        "trigger_type": "thematic_density",
                        "primary_keyword": keyword,
                        "cluster_ids": [c["cluster_id"] for c in cluster_list],
                        "cluster_count": len(cluster_list),
                        "total_articles": sum(c["size"] for c in cluster_list),
                        "coherence_score": coherence_score,
                        "strategic_category": self._classify_strategic_category(
                            keyword
                        ),
                        "suggested_title": f"Strategic {keyword.title()} Developments",
                        "rationale": f"{len(cluster_list)} clusters around '{keyword}' suggest strategic narrative consolidation",
                        "priority_score": coherence_score * len(cluster_list) * 0.1,
                    }
                    triggers.append(trigger)

        return triggers

    def _analyze_temporal_clustering(
        self, clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find clusters emerging simultaneously that might represent coordinated themes"""
        triggers = []

        # Group clusters by 48-hour windows
        time_windows = {}

        for cluster in clusters:
            # Create 48-hour time windows
            window_start = cluster["created_at"].replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            window_key = window_start.strftime("%Y-%m-%d")

            if window_key not in time_windows:
                time_windows[window_key] = []
            time_windows[window_key].append(cluster)

        # Analyze each time window for thematic coherence
        for window_key, window_clusters in time_windows.items():
            if len(window_clusters) >= 5:  # Minimum clusters for temporal trigger

                # Find shared themes in the window
                theme_analysis = self._analyze_window_themes(window_clusters)

                for theme, theme_clusters in theme_analysis.items():
                    if len(theme_clusters) >= 3:  # Multiple clusters on same theme

                        # Check source diversity
                        source_diversity = self._calculate_source_diversity(
                            theme_clusters
                        )

                        if source_diversity >= 3:  # At least 3 different sources
                            trigger = {
                                "trigger_type": "temporal_clustering",
                                "time_window": window_key,
                                "theme": theme,
                                "cluster_ids": [
                                    c["cluster_id"] for c in theme_clusters
                                ],
                                "cluster_count": len(theme_clusters),
                                "source_diversity": source_diversity,
                                "strategic_category": self._classify_strategic_category(
                                    theme
                                ),
                                "suggested_title": f"Emerging {theme.title()} Strategic Developments",
                                "rationale": f"Coordinated emergence of {len(theme_clusters)} clusters on '{theme}' across {source_diversity} sources",
                                "priority_score": len(theme_clusters)
                                * source_diversity
                                * 0.15,
                            }
                            triggers.append(trigger)

        return triggers

    def _analyze_strategic_keywords(
        self, clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find clusters containing high-priority strategic keywords"""
        triggers = []

        # Group clusters by strategic keyword categories
        strategic_groups = {}

        for category, keywords in self.strategic_keywords.items():
            strategic_groups[category] = []

            for cluster in clusters:
                cluster_keywords = set(kw.lower() for kw in cluster["keywords"])
                strategic_keywords_found = set(keywords) & cluster_keywords

                if strategic_keywords_found:
                    cluster["matched_strategic_keywords"] = list(
                        strategic_keywords_found
                    )
                    strategic_groups[category].append(cluster)

        # Create triggers for strategic categories with multiple clusters
        for category, category_clusters in strategic_groups.items():
            if len(category_clusters) >= 2:  # At least 2 clusters in strategic category

                # Calculate strategic importance score
                importance_score = self._calculate_strategic_importance(
                    category_clusters, category
                )

                if importance_score >= 0.7:  # High strategic importance threshold
                    trigger = {
                        "trigger_type": "strategic_keywords",
                        "strategic_category": category,
                        "cluster_ids": [c["cluster_id"] for c in category_clusters],
                        "cluster_count": len(category_clusters),
                        "strategic_keywords": list(
                            set().union(
                                *[
                                    c["matched_strategic_keywords"]
                                    for c in category_clusters
                                ]
                            )
                        ),
                        "importance_score": importance_score,
                        "suggested_title": f"Strategic {category.title()} Intelligence Update",
                        "rationale": f"Multiple {category} clusters require strategic consolidation",
                        "priority_score": importance_score
                        * len(category_clusters)
                        * 0.2,
                    }
                    triggers.append(trigger)

        return triggers

    def _analyze_source_diversity(
        self, clusters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find themes validated across multiple news sources"""
        triggers = []

        # Extract themes and their source coverage
        theme_sources = {}

        for cluster in clusters:
            primary_keyword = (
                cluster["keywords"][0] if cluster["keywords"] else "unknown"
            )

            if primary_keyword not in theme_sources:
                theme_sources[primary_keyword] = {"clusters": [], "sources": set()}

            theme_sources[primary_keyword]["clusters"].append(cluster)

            # Add sources from sample articles
            for article in cluster["sample_articles"]:
                if article.get("source"):
                    theme_sources[primary_keyword]["sources"].add(article["source"])

        # Find themes with high source diversity
        for theme, data in theme_sources.items():
            source_count = len(data["sources"])
            cluster_count = len(data["clusters"])

            if source_count >= 4 and cluster_count >= 3:  # High diversity threshold

                credibility_score = min(source_count / 10.0, 1.0)  # Cap at 1.0

                trigger = {
                    "trigger_type": "source_diversity",
                    "theme": theme,
                    "cluster_ids": [c["cluster_id"] for c in data["clusters"]],
                    "cluster_count": cluster_count,
                    "source_count": source_count,
                    "sources": list(data["sources"]),
                    "credibility_score": credibility_score,
                    "strategic_category": self._classify_strategic_category(theme),
                    "suggested_title": f"Cross-Source {theme.title()} Analysis",
                    "rationale": f"Theme '{theme}' validated across {source_count} sources",
                    "priority_score": credibility_score * cluster_count * 0.18,
                }
                triggers.append(trigger)

        return triggers

    def _calculate_thematic_coherence(
        self, clusters: List[Dict[str, Any]], primary_keyword: str
    ) -> float:
        """Calculate how thematically coherent a group of clusters is"""
        if not clusters:
            return 0.0

        # Count keyword overlap across clusters
        all_keywords = []
        for cluster in clusters:
            all_keywords.extend(cluster["keywords"][:3])  # Top 3 keywords per cluster

        # Calculate overlap percentage
        unique_keywords = set(all_keywords)
        total_keywords = len(all_keywords)

        if total_keywords == 0:
            return 0.0

        # Higher coherence = more repeated keywords
        coherence = 1.0 - (len(unique_keywords) / total_keywords)

        # Boost score if primary keyword appears frequently
        primary_count = all_keywords.count(primary_keyword)
        primary_boost = min(primary_count / len(clusters), 1.0)

        return min((coherence + primary_boost) / 2.0, 1.0)

    def _analyze_window_themes(
        self, clusters: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group clusters in time window by shared themes"""
        themes = {}

        for cluster in clusters:
            # Use primary keyword as theme
            if cluster["keywords"]:
                theme = cluster["keywords"][0]
                if theme not in themes:
                    themes[theme] = []
                themes[theme].append(cluster)

        # Only return themes with multiple clusters
        return {
            theme: clusters for theme, clusters in themes.items() if len(clusters) >= 2
        }

    def _calculate_source_diversity(self, clusters: List[Dict[str, Any]]) -> int:
        """Count unique news sources across clusters"""
        sources = set()

        for cluster in clusters:
            for article in cluster["sample_articles"]:
                if article.get("source"):
                    sources.add(article["source"])

        return len(sources)

    def _calculate_strategic_importance(
        self, clusters: List[Dict[str, Any]], category: str
    ) -> float:
        """Calculate strategic importance score for a category"""
        if not clusters:
            return 0.0

        # Base score by category importance
        category_weights = {
            "geopolitical": 1.0,
            "security": 0.9,
            "economic": 0.8,
            "technology": 0.7,
        }

        base_score = category_weights.get(category, 0.5)

        # Boost based on cluster size and count
        total_articles = sum(c["size"] for c in clusters)
        size_boost = min(total_articles / 50.0, 1.0)  # Cap at 50 articles

        # Boost based on keyword match strength
        keyword_matches = sum(
            len(c.get("matched_strategic_keywords", [])) for c in clusters
        )
        keyword_boost = min(keyword_matches / 10.0, 1.0)

        return min((base_score + size_boost + keyword_boost) / 3.0, 1.0)

    def _classify_strategic_category(self, keyword: str) -> str:
        """Classify keyword into strategic category"""
        keyword_lower = keyword.lower()

        for category, keywords in self.strategic_keywords.items():
            if keyword_lower in keywords:
                return category

        return "general"

    def _prioritize_triggers(
        self, triggers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank triggers by priority score and strategic importance"""

        # Sort by priority score descending
        sorted_triggers = sorted(
            triggers, key=lambda x: x.get("priority_score", 0), reverse=True
        )

        # Add rank and recommendation strength
        for i, trigger in enumerate(sorted_triggers):
            trigger["rank"] = i + 1
            trigger["recommendation_strength"] = (
                self._calculate_recommendation_strength(trigger)
            )

            # Add estimated curation effort
            trigger["estimated_effort_hours"] = self._estimate_curation_effort(trigger)

            # Add suggested deadline
            trigger["suggested_deadline"] = self._suggest_review_deadline(trigger)

        return sorted_triggers

    def _calculate_recommendation_strength(self, trigger: Dict[str, Any]) -> str:
        """Calculate recommendation strength category"""
        score = trigger.get("priority_score", 0)

        if score >= 0.8:
            return "strong"
        elif score >= 0.6:
            return "moderate"
        else:
            return "weak"

    def _estimate_curation_effort(self, trigger: Dict[str, Any]) -> float:
        """Estimate hours needed for manual curation"""
        base_effort = 1.0  # Base 1 hour

        # Add time based on cluster count
        cluster_effort = trigger.get("cluster_count", 1) * 0.5

        # Add time based on strategic complexity
        category = trigger.get("strategic_category", "general")
        complexity_multiplier = {
            "geopolitical": 1.5,
            "security": 1.3,
            "economic": 1.2,
            "technology": 1.1,
            "general": 1.0,
        }.get(category, 1.0)

        return (base_effort + cluster_effort) * complexity_multiplier

    def _suggest_review_deadline(self, trigger: Dict[str, Any]) -> str:
        """Suggest review deadline based on priority and strategic importance"""
        strength = trigger.get("recommendation_strength", "weak")

        deadline_map = {
            "strong": 24,  # 24 hours
            "moderate": 48,  # 48 hours
            "weak": 72,  # 72 hours
        }

        hours = deadline_map.get(strength, 72)
        deadline = datetime.now() + timedelta(hours=hours)

        return deadline.isoformat()

    def generate_trigger_report(self, triggers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive trigger analysis report"""

        if not triggers:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "no_triggers",
                "message": "No consolidation opportunities identified",
                "triggers": [],
            }

        # Summary statistics
        total_clusters = sum(t.get("cluster_count", 0) for t in triggers)
        total_articles = sum(t.get("total_articles", 0) for t in triggers)

        strong_recommendations = [
            t for t in triggers if t.get("recommendation_strength") == "strong"
        ]
        moderate_recommendations = [
            t for t in triggers if t.get("recommendation_strength") == "moderate"
        ]

        # Category breakdown
        category_breakdown = {}
        for trigger in triggers:
            category = trigger.get("strategic_category", "general")
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += 1

        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "triggers_found",
            "summary": {
                "total_triggers": len(triggers),
                "strong_recommendations": len(strong_recommendations),
                "moderate_recommendations": len(moderate_recommendations),
                "total_clusters_affected": total_clusters,
                "total_articles_affected": total_articles,
                "estimated_total_effort_hours": sum(
                    t.get("estimated_effort_hours", 0) for t in triggers
                ),
            },
            "category_breakdown": category_breakdown,
            "top_priorities": triggers[:5],  # Top 5 highest priority
            "triggers": triggers,
        }

        return report


# CLI interface for testing and daily operations
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze curation triggers")
    parser.add_argument("--days", type=int, default=7, help="Days back to analyze")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    analyzer = CurationTriggerAnalyzer()

    try:
        triggers = analyzer.analyze_daily_triggers(args.days)
        report = analyzer.generate_trigger_report(triggers)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {args.output}")
        else:
            print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"Analysis failed: {e}")
        exit(1)
