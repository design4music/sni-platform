"""
Query utilities for Strategic Narrative Intelligence ETL Pipeline

Provides specialized query functions for fringe analysis and data quality tracking.
"""

from .fringe_analysis import (FringeAnalysisQueries,
                              get_fringe_analysis_dashboard,
                              get_quality_trends,
                              search_narratives_by_fringe_tone)

__all__ = [
    "FringeAnalysisQueries",
    "get_fringe_analysis_dashboard",
    "search_narratives_by_fringe_tone",
    "get_quality_trends",
]
