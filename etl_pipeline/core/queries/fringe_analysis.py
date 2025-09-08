"""
Fringe Analysis Query Functions for Strategic Narrative Intelligence

Provides specialized queries for analyzing fringe content and data quality patterns
using the new fringe_notes and data_quality_notes JSONB fields.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..database import get_db_session
from ..database.models import NarrativeMetrics, NarrativeNSF1

logger = structlog.get_logger(__name__)


class FringeAnalysisQueries:
    """
    Specialized queries for fringe content and quality analysis
    """

    @staticmethod
    def get_narratives_with_fringe_content(
        session: Session, limit: int = 50, tone_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get narratives that have fringe content annotations.

        Args:
            session: Database session
            limit: Maximum number of results
            tone_filter: Optional tone to filter by (e.g., 'propagandistic')

        Returns:
            List of narratives with fringe content details
        """

        base_query = """
        SELECT 
            n.narrative_id,
            n.title,
            n.created_at,
            n.updated_at,
            jsonb_array_length(n.fringe_notes) as fringe_count,
            jsonb_array_length(n.data_quality_notes) as quality_count,
            n.fringe_notes,
            nm.trending_score,
            nm.credibility_score
        FROM narratives n
        LEFT JOIN narrative_metrics nm ON n.id = nm.narrative_uuid
        WHERE jsonb_array_length(n.fringe_notes) > 0
        """

        params = {"limit": limit}

        if tone_filter:
            base_query += """
            AND EXISTS (
                SELECT 1 FROM jsonb_array_elements(n.fringe_notes) note
                WHERE note->>'tone' = :tone_filter
            )
            """
            params["tone_filter"] = tone_filter

        base_query += " ORDER BY n.updated_at DESC LIMIT :limit"

        result = session.execute(text(base_query), params)

        narratives = []
        for row in result:
            row_dict = dict(row._mapping)

            # Extract fringe tone summary
            fringe_notes = row_dict.get("fringe_notes", [])
            tones = [note.get("tone") for note in fringe_notes if note.get("tone")]

            narratives.append(
                {
                    "narrative_id": row_dict["narrative_id"],
                    "title": row_dict["title"],
                    "created_at": row_dict["created_at"],
                    "updated_at": row_dict["updated_at"],
                    "fringe_count": row_dict["fringe_count"],
                    "quality_count": row_dict["quality_count"],
                    "fringe_tones": list(set(tones)),
                    "trending_score": row_dict.get("trending_score"),
                    "credibility_score": row_dict.get("credibility_score"),
                    "latest_fringe_note": (
                        fringe_notes[-1].get("summary") if fringe_notes else None
                    ),
                }
            )

        return narratives

    @staticmethod
    def analyze_fringe_patterns(
        session: Session, days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze patterns in fringe content over time.

        Args:
            session: Database session
            days_back: Number of days to analyze

        Returns:
            Analysis of fringe content patterns
        """

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = """
        WITH fringe_analysis AS (
            SELECT 
                n.narrative_id,
                n.title,
                n.created_at,
                note->>'tone' as tone,
                (note->>'source_count')::integer as source_count,
                note->>'summary' as note_summary,
                note->>'detected_at' as detected_at
            FROM narratives n,
                 jsonb_array_elements(n.fringe_notes) note
            WHERE n.created_at >= :cutoff_date
              AND note->>'note_type' = 'fringe'
        )
        SELECT 
            COUNT(*) as total_fringe_notes,
            COUNT(DISTINCT narrative_id) as narratives_with_fringe,
            AVG(source_count) as avg_source_count,
            array_agg(DISTINCT tone) FILTER (WHERE tone IS NOT NULL) as unique_tones,
            COUNT(*) FILTER (WHERE tone = 'propagandistic') as propagandistic_count,
            COUNT(*) FILTER (WHERE tone = 'neutral') as neutral_count,
            COUNT(*) FILTER (WHERE source_count = 1) as single_source_count,
            COUNT(*) FILTER (WHERE source_count >= 3) as multi_source_count
        FROM fringe_analysis
        """

        result = session.execute(text(query), {"cutoff_date": cutoff_date}).fetchone()

        if not result:
            return {
                "total_fringe_notes": 0,
                "narratives_with_fringe": 0,
                "analysis_period_days": days_back,
                "patterns": {},
            }

        row_dict = dict(result._mapping)

        return {
            "total_fringe_notes": row_dict["total_fringe_notes"],
            "narratives_with_fringe": row_dict["narratives_with_fringe"],
            "avg_source_count": (
                float(row_dict["avg_source_count"])
                if row_dict["avg_source_count"]
                else 0
            ),
            "unique_tones": row_dict["unique_tones"] or [],
            "analysis_period_days": days_back,
            "patterns": {
                "propagandistic_percentage": (
                    row_dict["propagandistic_count"]
                    / max(row_dict["total_fringe_notes"], 1)
                )
                * 100,
                "single_source_percentage": (
                    row_dict["single_source_count"]
                    / max(row_dict["total_fringe_notes"], 1)
                )
                * 100,
                "multi_source_percentage": (
                    row_dict["multi_source_count"]
                    / max(row_dict["total_fringe_notes"], 1)
                )
                * 100,
            },
        }

    @staticmethod
    def get_quality_issues_summary(
        session: Session, days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get summary of data quality issues across narratives.

        Args:
            session: Database session
            days_back: Number of days to analyze

        Returns:
            Summary of quality issues by type and severity
        """

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = """
        WITH quality_analysis AS (
            SELECT 
                n.narrative_id,
                n.title,
                n.created_at,
                note->>'summary' as issue_summary,
                (note->>'source_count')::integer as source_count,
                note->>'detected_at' as detected_at,
                CASE 
                    WHEN note->>'summary' ILIKE '%missing%' THEN 'missing_data'
                    WHEN note->>'summary' ILIKE '%extraction%' THEN 'extraction_issue'
                    WHEN note->>'summary' ILIKE '%clustering%' THEN 'clustering_issue'
                    WHEN note->>'summary' ILIKE '%duplicate%' THEN 'duplicate_issue'
                    ELSE 'other'
                END as issue_category
            FROM narratives n,
                 jsonb_array_elements(n.data_quality_notes) note
            WHERE n.created_at >= :cutoff_date
              AND note->>'note_type' = 'quality'
        )
        SELECT 
            COUNT(*) as total_quality_issues,
            COUNT(DISTINCT narrative_id) as narratives_with_issues,
            AVG(source_count) as avg_affected_sources,
            COUNT(*) FILTER (WHERE issue_category = 'missing_data') as missing_data_count,
            COUNT(*) FILTER (WHERE issue_category = 'extraction_issue') as extraction_issue_count,
            COUNT(*) FILTER (WHERE issue_category = 'clustering_issue') as clustering_issue_count,
            COUNT(*) FILTER (WHERE issue_category = 'duplicate_issue') as duplicate_issue_count,
            COUNT(*) FILTER (WHERE issue_category = 'other') as other_issue_count
        FROM quality_analysis
        """

        result = session.execute(text(query), {"cutoff_date": cutoff_date}).fetchone()

        if not result:
            return {
                "total_quality_issues": 0,
                "narratives_with_issues": 0,
                "analysis_period_days": days_back,
                "issue_breakdown": {},
            }

        row_dict = dict(result._mapping)

        return {
            "total_quality_issues": row_dict["total_quality_issues"],
            "narratives_with_issues": row_dict["narratives_with_issues"],
            "avg_affected_sources": (
                float(row_dict["avg_affected_sources"])
                if row_dict["avg_affected_sources"]
                else 0
            ),
            "analysis_period_days": days_back,
            "issue_breakdown": {
                "missing_data": row_dict["missing_data_count"],
                "extraction_issues": row_dict["extraction_issue_count"],
                "clustering_issues": row_dict["clustering_issue_count"],
                "duplicate_issues": row_dict["duplicate_issue_count"],
                "other_issues": row_dict["other_issue_count"],
            },
        }

    @staticmethod
    def get_breadth_validation_failures(
        session: Session, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get narratives that failed breadth validation in CLUST-2.

        Args:
            session: Database session
            limit: Maximum number of results

        Returns:
            List of narratives that failed breadth validation
        """

        query = """
        SELECT 
            n.narrative_id,
            n.title,
            n.created_at,
            note->>'summary' as failure_reason,
            (note->>'source_count')::integer as source_count,
            note->>'detected_at' as detected_at,
            jsonb_array_length(n.fringe_notes) as total_fringe_notes
        FROM narratives n,
             jsonb_array_elements(n.fringe_notes) note
        WHERE note->>'summary' ILIKE '%breadth%'
          AND note->>'note_type' = 'fringe'
        ORDER BY n.created_at DESC
        LIMIT :limit
        """

        result = session.execute(text(query), {"limit": limit})

        failures = []
        for row in result:
            row_dict = dict(row._mapping)
            failures.append(
                {
                    "narrative_id": row_dict["narrative_id"],
                    "title": row_dict["title"],
                    "created_at": row_dict["created_at"],
                    "failure_reason": row_dict["failure_reason"],
                    "source_count": row_dict["source_count"],
                    "detected_at": row_dict["detected_at"],
                    "total_fringe_notes": row_dict["total_fringe_notes"],
                }
            )

        return failures

    @staticmethod
    def get_high_fringe_narratives(
        session: Session, min_fringe_count: int = 3, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Get narratives with high fringe content (multiple fringe notes).

        Args:
            session: Database session
            min_fringe_count: Minimum number of fringe notes to qualify
            limit: Maximum number of results

        Returns:
            List of narratives with high fringe content
        """

        query = """
        SELECT 
            n.narrative_id,
            n.title,
            n.created_at,
            n.updated_at,
            jsonb_array_length(n.fringe_notes) as fringe_count,
            (
                SELECT jsonb_agg(DISTINCT note->>'tone')
                FROM jsonb_array_elements(n.fringe_notes) note
                WHERE note->>'tone' IS NOT NULL
            ) as unique_tones,
            (
                SELECT AVG((note->>'source_count')::integer)
                FROM jsonb_array_elements(n.fringe_notes) note
                WHERE note->>'source_count' IS NOT NULL
            ) as avg_source_count,
            nm.trending_score,
            nm.credibility_score
        FROM narratives n
        LEFT JOIN narrative_metrics nm ON n.id = nm.narrative_uuid
        WHERE jsonb_array_length(n.fringe_notes) >= :min_fringe_count
        ORDER BY jsonb_array_length(n.fringe_notes) DESC, n.updated_at DESC
        LIMIT :limit
        """

        result = session.execute(
            text(query), {"min_fringe_count": min_fringe_count, "limit": limit}
        )

        narratives = []
        for row in result:
            row_dict = dict(row._mapping)
            narratives.append(
                {
                    "narrative_id": row_dict["narrative_id"],
                    "title": row_dict["title"],
                    "created_at": row_dict["created_at"],
                    "updated_at": row_dict["updated_at"],
                    "fringe_count": row_dict["fringe_count"],
                    "unique_tones": row_dict["unique_tones"] or [],
                    "avg_source_count": (
                        float(row_dict["avg_source_count"])
                        if row_dict["avg_source_count"]
                        else None
                    ),
                    "trending_score": row_dict["trending_score"],
                    "credibility_score": row_dict["credibility_score"],
                }
            )

        return narratives


# ============================================================================
# Convenience Functions for Common Queries
# ============================================================================


def get_fringe_analysis_dashboard(days_back: int = 7) -> Dict[str, Any]:
    """
    Get comprehensive fringe analysis data for dashboard display.

    Args:
        days_back: Number of days to analyze

    Returns:
        Dashboard data with fringe content analysis
    """

    with get_db_session() as session:
        try:
            # Get fringe patterns
            patterns = FringeAnalysisQueries.analyze_fringe_patterns(session, days_back)

            # Get quality issues summary
            quality_summary = FringeAnalysisQueries.get_quality_issues_summary(
                session, days_back
            )

            # Get recent fringe narratives
            recent_fringe = FringeAnalysisQueries.get_narratives_with_fringe_content(
                session, limit=10
            )

            # Get breadth validation failures
            breadth_failures = FringeAnalysisQueries.get_breadth_validation_failures(
                session, limit=5
            )

            # Get high fringe narratives
            high_fringe = FringeAnalysisQueries.get_high_fringe_narratives(
                session, min_fringe_count=2, limit=10
            )

            return {
                "analysis_period_days": days_back,
                "generated_at": datetime.utcnow().isoformat(),
                "fringe_patterns": patterns,
                "quality_summary": quality_summary,
                "recent_fringe_narratives": recent_fringe,
                "breadth_validation_failures": breadth_failures,
                "high_fringe_narratives": high_fringe,
                "summary_stats": {
                    "total_fringe_narratives": len(recent_fringe),
                    "total_breadth_failures": len(breadth_failures),
                    "total_high_fringe_narratives": len(high_fringe),
                    "quality_issues_count": quality_summary["total_quality_issues"],
                },
            }

        except Exception as exc:
            logger.error("Failed to generate fringe analysis dashboard", error=str(exc))
            return {
                "error": f"Analysis failed: {str(exc)}",
                "generated_at": datetime.utcnow().isoformat(),
            }


def search_narratives_by_fringe_tone(
    tone: str, limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for narratives with specific fringe tone.

    Args:
        tone: Target tone (e.g., 'propagandistic', 'neutral')
        limit: Maximum number of results

    Returns:
        List of narratives with matching fringe tone
    """

    with get_db_session() as session:
        return FringeAnalysisQueries.get_narratives_with_fringe_content(
            session, limit=limit, tone_filter=tone
        )


def get_quality_trends(days_back: int = 30) -> Dict[str, Any]:
    """
    Get data quality trends over time.

    Args:
        days_back: Number of days to analyze

    Returns:
        Quality trends analysis
    """

    with get_db_session() as session:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get quality issues by day
            query = """
            WITH daily_quality AS (
                SELECT 
                    DATE(n.created_at) as issue_date,
                    COUNT(*) as daily_issues,
                    COUNT(DISTINCT n.narrative_id) as affected_narratives
                FROM narratives n,
                     jsonb_array_elements(n.data_quality_notes) note
                WHERE n.created_at >= :cutoff_date
                  AND note->>'note_type' = 'quality'
                GROUP BY DATE(n.created_at)
                ORDER BY issue_date
            )
            SELECT 
                issue_date,
                daily_issues,
                affected_narratives,
                SUM(daily_issues) OVER (ORDER BY issue_date) as cumulative_issues
            FROM daily_quality
            """

            result = session.execute(text(query), {"cutoff_date": cutoff_date})

            trends = []
            for row in result:
                row_dict = dict(row._mapping)
                trends.append(
                    {
                        "date": row_dict["issue_date"].isoformat(),
                        "daily_issues": row_dict["daily_issues"],
                        "affected_narratives": row_dict["affected_narratives"],
                        "cumulative_issues": row_dict["cumulative_issues"],
                    }
                )

            return {
                "analysis_period_days": days_back,
                "daily_trends": trends,
                "total_issues": trends[-1]["cumulative_issues"] if trends else 0,
            }

        except Exception as exc:
            logger.error("Failed to get quality trends", error=str(exc))
            return {"error": f"Trends analysis failed: {str(exc)}"}
