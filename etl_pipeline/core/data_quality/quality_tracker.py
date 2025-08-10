"""
Data Quality Tracker for Strategic Narrative Intelligence ETL Pipeline

This module provides utilities for tracking and recording data quality issues
in the ETL pipeline, populating the data_quality_notes JSONB field in narratives.

Integrates with:
- Article ingestion pipeline
- Clustering processes (CLUST-1, CLUST-2)
- Content extraction and processing
- Duplicate detection
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

from ..database import get_db_session
from ..database.models import Article, NarrativeNSF1

logger = structlog.get_logger(__name__)


class QualityIssueType(Enum):
    """Types of data quality issues that can be tracked"""

    MISSING_METADATA = "missing_metadata"
    EXTRACTION_ANOMALY = "extraction_anomaly"
    CLUSTERING_IRREGULARITY = "clustering_irregularity"
    DUPLICATE_DETECTION = "duplicate_detection"
    SOURCE_RELIABILITY = "source_reliability"
    CONTENT_TRUNCATION = "content_truncation"
    LANGUAGE_DETECTION = "language_detection"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"


@dataclass
class QualityIssue:
    """Data structure for tracking quality issues"""

    issue_type: QualityIssueType
    summary: str
    source_count: Optional[int] = None
    example_articles: Optional[List[str]] = None
    severity: str = "medium"  # low, medium, high, critical
    metadata: Optional[Dict[str, Any]] = None


class DataQualityTracker:
    """
    Tracks and records data quality issues throughout the ETL pipeline
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.session_issues = []  # Track issues during current session

    def track_missing_metadata(
        self, articles: List[Dict[str, Any]], missing_fields: List[str]
    ) -> QualityIssue:
        """Track articles with missing critical metadata"""

        issue = QualityIssue(
            issue_type=QualityIssueType.MISSING_METADATA,
            summary=f"{len(articles)} articles missing {', '.join(missing_fields)}",
            source_count=len(set(a.get("source_name", "") for a in articles)),
            example_articles=[a.get("url", "") for a in articles[:3]],
            severity="medium" if len(articles) < 10 else "high",
            metadata={
                "missing_fields": missing_fields,
                "affected_articles_count": len(articles),
                "detection_context": "ingestion_pipeline",
            },
        )

        self.session_issues.append(issue)
        return issue

    def track_extraction_anomaly(
        self, article_id: str, article_url: str, anomaly_type: str, details: str
    ) -> QualityIssue:
        """Track content extraction anomalies"""

        issue = QualityIssue(
            issue_type=QualityIssueType.EXTRACTION_ANOMALY,
            summary=f"Content extraction {anomaly_type}: {details}",
            source_count=1,
            example_articles=[article_url],
            severity="low" if anomaly_type == "truncation" else "medium",
            metadata={
                "anomaly_type": anomaly_type,
                "article_id": article_id,
                "extraction_details": details,
                "detection_context": "content_extraction",
            },
        )

        self.session_issues.append(issue)
        return issue

    def track_clustering_irregularity(
        self,
        cluster_id: str,
        irregularity_type: str,
        affected_articles: List[str],
        details: str,
    ) -> QualityIssue:
        """Track clustering algorithm irregularities"""

        issue = QualityIssue(
            issue_type=QualityIssueType.CLUSTERING_IRREGULARITY,
            summary=f"Clustering {irregularity_type} in cluster {cluster_id}: {details}",
            source_count=None,  # Not applicable for clustering issues
            example_articles=affected_articles[:3],
            severity="medium" if len(affected_articles) < 5 else "high",
            metadata={
                "cluster_id": cluster_id,
                "irregularity_type": irregularity_type,
                "affected_articles_count": len(affected_articles),
                "clustering_details": details,
                "detection_context": "clustering_process",
            },
        )

        self.session_issues.append(issue)
        return issue

    def track_duplicate_detection_issue(
        self,
        original_id: str,
        duplicate_ids: List[str],
        detection_method: str,
        confidence: float,
    ) -> QualityIssue:
        """Track duplicate detection inconsistencies"""

        issue = QualityIssue(
            issue_type=QualityIssueType.DUPLICATE_DETECTION,
            summary=f"Duplicate detection {detection_method} found {len(duplicate_ids)} duplicates with {confidence:.2f} confidence",
            source_count=None,
            example_articles=[],  # Would need URLs from article IDs
            severity="low" if confidence > 0.8 else "medium",
            metadata={
                "original_article_id": original_id,
                "duplicate_article_ids": duplicate_ids,
                "detection_method": detection_method,
                "confidence_score": confidence,
                "detection_context": "duplicate_detection",
            },
        )

        self.session_issues.append(issue)
        return issue

    def track_source_reliability_issue(
        self,
        source_name: str,
        reliability_score: float,
        issue_description: str,
        affected_articles: List[str],
    ) -> QualityIssue:
        """Track source reliability concerns"""

        severity = "low"
        if reliability_score < 0.3:
            severity = "high"
        elif reliability_score < 0.5:
            severity = "medium"

        issue = QualityIssue(
            issue_type=QualityIssueType.SOURCE_RELIABILITY,
            summary=f"Source {source_name} reliability {reliability_score:.2f}: {issue_description}",
            source_count=1,
            example_articles=affected_articles[:3],
            severity=severity,
            metadata={
                "source_name": source_name,
                "reliability_score": reliability_score,
                "issue_description": issue_description,
                "affected_articles_count": len(affected_articles),
                "detection_context": "source_quality_assessment",
            },
        )

        self.session_issues.append(issue)
        return issue

    def add_quality_note_to_narrative(
        self, narrative_id: str, issue: QualityIssue
    ) -> bool:
        """Add a quality issue note to a specific narrative"""

        with get_db_session() as session:
            try:
                # Find narrative by narrative_id (display ID)
                narrative = (
                    session.query(NarrativeNSF1)
                    .filter(NarrativeNSF1.narrative_id == narrative_id)
                    .first()
                )

                if not narrative:
                    self.logger.error(
                        "Narrative not found for quality note",
                        narrative_id=narrative_id,
                    )
                    return False

                # Add quality note using model helper method
                narrative.add_data_quality_note(
                    summary=issue.summary,
                    source_count=issue.source_count,
                    example_articles=issue.example_articles or [],
                )

                session.commit()

                self.logger.info(
                    "Added quality note to narrative",
                    narrative_id=narrative_id,
                    issue_type=issue.issue_type.value,
                    severity=issue.severity,
                )

                return True

            except Exception as exc:
                session.rollback()
                self.logger.error(
                    "Failed to add quality note to narrative",
                    narrative_id=narrative_id,
                    error=str(exc),
                )
                return False

    def batch_add_quality_notes(
        self, narrative_issues: Dict[str, List[QualityIssue]]
    ) -> Dict[str, bool]:
        """Add quality notes to multiple narratives in batch"""

        results = {}

        with get_db_session() as session:
            try:
                for narrative_id, issues in narrative_issues.items():
                    # Find narrative
                    narrative = (
                        session.query(NarrativeNSF1)
                        .filter(NarrativeNSF1.narrative_id == narrative_id)
                        .first()
                    )

                    if not narrative:
                        self.logger.warning(
                            "Narrative not found for batch quality notes",
                            narrative_id=narrative_id,
                        )
                        results[narrative_id] = False
                        continue

                    # Add all quality notes for this narrative
                    for issue in issues:
                        narrative.add_data_quality_note(
                            summary=issue.summary,
                            source_count=issue.source_count,
                            example_articles=issue.example_articles or [],
                        )

                    results[narrative_id] = True

                session.commit()

                self.logger.info(
                    "Batch added quality notes",
                    narratives_updated=sum(results.values()),
                    total_issues=sum(
                        len(issues) for issues in narrative_issues.values()
                    ),
                )

            except Exception as exc:
                session.rollback()
                self.logger.error("Failed to batch add quality notes", error=str(exc))
                results = {k: False for k in narrative_issues.keys()}

        return results

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of quality issues tracked in current session"""

        if not self.session_issues:
            return {
                "total_issues": 0,
                "by_type": {},
                "by_severity": {},
                "recommendations": [],
            }

        by_type = {}
        by_severity = {}

        for issue in self.session_issues:
            # Count by type
            issue_type = issue.issue_type.value
            by_type[issue_type] = by_type.get(issue_type, 0) + 1

            # Count by severity
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1

        # Generate recommendations
        recommendations = []
        if by_type.get("missing_metadata", 0) > 5:
            recommendations.append(
                "Review feed configurations for metadata completeness"
            )
        if by_type.get("extraction_anomaly", 0) > 3:
            recommendations.append(
                "Investigate content extraction pipeline reliability"
            )
        if by_severity.get("high", 0) > 0:
            recommendations.append("Address high-severity quality issues immediately")

        return {
            "total_issues": len(self.session_issues),
            "by_type": by_type,
            "by_severity": by_severity,
            "recommendations": recommendations,
        }

    def clear_session(self):
        """Clear session-tracked issues"""
        self.session_issues = []
        self.logger.info("Cleared data quality tracking session")


# ============================================================================
# ETL Integration Functions
# ============================================================================


def track_ingestion_quality_issues(
    articles_data: List[Dict[str, Any]], tracker: Optional[DataQualityTracker] = None
) -> List[QualityIssue]:
    """
    Analyze ingested articles for quality issues and track them.

    Called during article ingestion to identify and track quality problems.
    """
    if tracker is None:
        tracker = DataQualityTracker()

    issues = []

    # Check for missing critical metadata
    missing_title = [a for a in articles_data if not a.get("title", "").strip()]
    if missing_title:
        issues.append(tracker.track_missing_metadata(missing_title, ["title"]))

    missing_content = [a for a in articles_data if not a.get("content", "").strip()]
    if missing_content:
        issues.append(tracker.track_missing_metadata(missing_content, ["content"]))

    missing_source = [a for a in articles_data if not a.get("source_name", "").strip()]
    if missing_source:
        issues.append(tracker.track_missing_metadata(missing_source, ["source_name"]))

    # Check for extraction anomalies
    for article in articles_data:
        content = article.get("content", "")
        if content and len(content) < 100:
            issues.append(
                tracker.track_extraction_anomaly(
                    article.get("id", ""),
                    article.get("url", ""),
                    "truncation",
                    f"Content too short: {len(content)} characters",
                )
            )

    return issues


def track_clustering_quality_issues(
    cluster_results: List[Dict[str, Any]], tracker: Optional[DataQualityTracker] = None
) -> List[QualityIssue]:
    """
    Analyze clustering results for quality issues.

    Called after CLUST-1 and CLUST-2 to identify clustering problems.
    """
    if tracker is None:
        tracker = DataQualityTracker()

    issues = []

    for cluster in cluster_results:
        cluster_id = cluster.get("cluster_id", "")
        articles = cluster.get("articles", [])

        # Check for single-article clusters (potential clustering failure)
        if len(articles) == 1:
            issues.append(
                tracker.track_clustering_irregularity(
                    cluster_id,
                    "single_article_cluster",
                    articles,
                    "Cluster contains only one article, may indicate clustering failure",
                )
            )

        # Check for extremely large clusters (potential under-clustering)
        if len(articles) > 50:
            issues.append(
                tracker.track_clustering_irregularity(
                    cluster_id,
                    "oversized_cluster",
                    articles[:3],  # Just first 3 as examples
                    f"Cluster contains {len(articles)} articles, may be under-clustered",
                )
            )

    return issues


# Global tracker instance for ETL pipeline use
global_quality_tracker = DataQualityTracker()
