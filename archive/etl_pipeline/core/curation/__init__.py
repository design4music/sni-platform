"""
Manual Parent Narrative Curation System
Strategic Narrative Intelligence ETL Pipeline

This module provides comprehensive manual curation capabilities for creating
strategic parent narratives that span multiple CLUST-1/CLUST-2 cluster outputs.

Key Components:
- ManualNarrativeManager: Core business logic for curation workflow
- Database schema enhancements for editorial control
- RESTful API endpoints for frontend integration
- Complete audit trail and validation system

Usage:
    from etl_pipeline.core.curation import ManualNarrativeManager

    manager = ManualNarrativeManager()
    parent_uuid, parent_id = manager.create_manual_parent(
        title="Strategic Parent Narrative",
        summary="Comprehensive strategic analysis...",
        curator_id="analyst_001"
    )
"""

from .manual_narrative_manager import ManualNarrativeManager

__all__ = ["ManualNarrativeManager"]

__version__ = "1.0.0"
__author__ = "SNI Strategic Narrative Intelligence Team"
