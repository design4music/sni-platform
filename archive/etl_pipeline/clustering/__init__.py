"""
Clustering Module
Strategic Narrative Intelligence ETL Pipeline

This module provides the complete clustering system for transforming
raw articles into thematic clusters and matching them to narratives.

Components:
- CLUST-1: Mechanical thematic grouping using semantic embeddings
- Narrative Matcher: Bridge between clusters and narrative objects
- Clustering Orchestrator: Coordinates the complete workflow

Usage:
    from etl_pipeline.clustering import run_clustering_workflow

    # Run complete workflow
    result = await run_clustering_workflow(article_limit=500)

    # Run CLUST-1 only
    clusters = await run_clust1_clustering(article_limit=500)
"""

# New keyword-based CLUST-1 (no longer exports old classes)
# CLUST-1 implementations archived to archive/2025-08-10/

from .clustering_orchestrator import (ClusteringOrchestrator,
                                      ClusteringWorkflowResult,
                                      run_clust1_clustering,
                                      run_clustering_workflow)
from .narrative_matcher import (MatchingDecision, NarrativeCentroid,
                                NarrativeMatcher, run_narrative_matching)

__all__ = [
    # Main entry points
    "run_clustering_workflow",
    "run_clust1_clustering",
    "run_narrative_matching",
    # Core classes (old CLUST1ThematicGrouping replaced with keyword-based system)
    "NarrativeMatcher",
    "ClusteringOrchestrator",
    # Data classes
    "MatchingDecision",
    "ClusteringWorkflowResult",
    "NarrativeCentroid",
]
