#!/usr/bin/env python3
"""
Manual Curation API Endpoints
Strategic Narrative Intelligence ETL Pipeline

FastAPI endpoints for manual parent narrative curation workflow.
Provides REST API for editorial interface and curation management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from etl_pipeline.core.curation.manual_narrative_manager import \
    ManualNarrativeManager
from etl_pipeline.core.database import get_db_session

logger = structlog.get_logger(__name__)

# Create router for curation endpoints
curation_router = APIRouter(prefix="/curation", tags=["curation"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateManualParentRequest(BaseModel):
    """Request model for creating manual parent narratives"""

    title: str = Field(
        ..., min_length=10, max_length=500, description="Narrative title"
    )
    summary: str = Field(..., min_length=50, description="Narrative summary")
    curator_id: str = Field(..., description="ID of curator creating this narrative")
    cluster_ids: Optional[List[str]] = Field(
        default=[], description="Optional CLUST-1/CLUST-2 cluster IDs to group"
    )
    editorial_priority: int = Field(
        default=3, ge=1, le=5, description="Priority level (1=high, 5=low)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional metadata"
    )

    @validator("cluster_ids")
    def validate_cluster_ids(cls, v):
        """Validate cluster IDs format"""
        if v and len(v) > 50:  # Reasonable limit
            raise ValueError("Too many cluster IDs (max 50)")
        return v or []


class AssignChildrenRequest(BaseModel):
    """Request model for assigning children to parent"""

    parent_uuid: str = Field(..., description="UUID of parent narrative")
    child_uuids: List[str] = Field(
        ..., min_items=1, description="List of child narrative UUIDs"
    )
    curator_id: str = Field(..., description="ID of curator performing assignment")
    rationale: Optional[str] = Field(None, description="Explanation for the assignment")

    @validator("child_uuids")
    def validate_child_uuids(cls, v):
        """Validate child UUIDs"""
        if len(v) > 20:  # Reasonable limit
            raise ValueError("Too many child narratives (max 20 per assignment)")
        return v


class UpdateStatusRequest(BaseModel):
    """Request model for updating curation status"""

    narrative_uuid: str = Field(..., description="UUID of narrative to update")
    new_status: str = Field(..., description="New curation status")
    actor_id: str = Field(..., description="ID of user making the change")
    notes: Optional[str] = Field(
        None, description="Optional notes about the status change"
    )

    @validator("new_status")
    def validate_status(cls, v):
        """Validate status values"""
        valid_statuses = [
            "auto_generated",
            "manual_draft",
            "pending_review",
            "reviewed",
            "approved",
            "published",
            "archived",
        ]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v


class CreateClusterGroupRequest(BaseModel):
    """Request model for creating cluster groups"""

    group_name: str = Field(
        ..., min_length=5, max_length=255, description="Name for cluster grouping"
    )
    cluster_ids: List[str] = Field(
        ..., min_items=1, description="CLUST-1/CLUST-2 cluster IDs"
    )
    curator_id: str = Field(..., description="ID of curator creating the group")
    description: Optional[str] = Field(None, description="Description of the group")
    rationale: Optional[str] = Field(
        None, description="Why these clusters were grouped"
    )
    strategic_significance: Optional[str] = Field(
        None, description="Strategic importance"
    )
    cluster_metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Metadata from clusters"
    )


class CurationDashboardResponse(BaseModel):
    """Response model for curation dashboard"""

    id: str
    narrative_id: str
    title: str
    curation_status: str
    curation_source: str
    curator_id: Optional[str]
    reviewer_id: Optional[str]
    editorial_priority: int
    review_deadline: Optional[str]
    created_at: str
    updated_at: str
    published_at: Optional[str]
    child_count: int
    manual_cluster_count: int
    is_parent: bool
    is_manual: bool
    is_overdue: bool
    last_activity: Optional[str]


class PendingReviewResponse(BaseModel):
    """Response model for pending reviews"""

    id: str
    narrative_id: str
    title: str
    curation_status: str
    curator_id: Optional[str]
    reviewer_id: Optional[str]
    editorial_priority: int
    review_deadline: Optional[str]
    child_count: int
    review_urgency: int
    days_until_deadline: Optional[int]
    created_at: str
    updated_at: str


class ValidationResponse(BaseModel):
    """Response model for workflow validation"""

    timestamp: str
    overall_status: str
    checks: List[Dict[str, Any]]
    error: Optional[str] = None


# ============================================================================
# Dependencies
# ============================================================================


def get_manual_manager(
    session: Session = Depends(get_db_session),
) -> ManualNarrativeManager:
    """Dependency to get manual narrative manager"""
    return ManualNarrativeManager(session)


# ============================================================================
# API Endpoints
# ============================================================================


@curation_router.post("/parent", response_model=Dict[str, str])
async def create_manual_parent(
    request: CreateManualParentRequest,
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Create a new manual parent narrative

    Creates a strategic parent narrative that can group multiple CLUST-1/CLUST-2
    clusters into a cohesive strategic narrative.
    """
    try:
        narrative_uuid, narrative_display_id = manager.create_manual_parent(
            title=request.title,
            summary=request.summary,
            curator_id=request.curator_id,
            cluster_ids=request.cluster_ids,
            editorial_priority=request.editorial_priority,
            metadata=request.metadata,
        )

        return {
            "narrative_uuid": narrative_uuid,
            "narrative_id": narrative_display_id,
            "status": "created",
            "message": f"Manual parent narrative {narrative_display_id} created successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create manual parent", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@curation_router.post("/assign-children", response_model=Dict[str, Any])
async def assign_children(
    request: AssignChildrenRequest,
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Assign child narratives to a manual parent

    Links existing child narratives to a manual parent narrative,
    creating the hierarchical relationship.
    """
    try:
        assigned_count = manager.assign_children_to_parent(
            parent_uuid=request.parent_uuid,
            child_uuids=request.child_uuids,
            curator_id=request.curator_id,
            rationale=request.rationale,
        )

        return {
            "assigned_count": assigned_count,
            "requested_count": len(request.child_uuids),
            "status": "success",
            "message": f"Successfully assigned {assigned_count} child narratives",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to assign children", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@curation_router.put("/status", response_model=Dict[str, Any])
async def update_status(
    request: UpdateStatusRequest,
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Update curation status with workflow validation

    Updates the curation status of a narrative following workflow rules
    (e.g., draft → pending_review → approved → published).
    """
    try:
        success = manager.update_curation_status(
            narrative_uuid=request.narrative_uuid,
            new_status=request.new_status,
            actor_id=request.actor_id,
            notes=request.notes,
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Status update rejected by workflow validation"
            )

        return {
            "success": True,
            "new_status": request.new_status,
            "message": f"Status updated to {request.new_status}",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@curation_router.get("/dashboard", response_model=List[CurationDashboardResponse])
async def get_dashboard(
    curator_id: Optional[str] = Query(None, description="Filter by curator ID"),
    status_filter: Optional[List[str]] = Query(
        None, description="Filter by status values"
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Get curation dashboard data

    Returns narrative data for the curation workflow dashboard,
    including manual narratives and their workflow status.
    """
    try:
        dashboard_data = manager.get_curation_dashboard(
            curator_id=curator_id, status_filter=status_filter, limit=limit
        )

        return [CurationDashboardResponse(**item) for item in dashboard_data]

    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@curation_router.get("/pending-reviews", response_model=List[PendingReviewResponse])
async def get_pending_reviews(
    reviewer_id: Optional[str] = Query(None, description="Filter by reviewer ID"),
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Get items pending review

    Returns narratives that need editorial review, ordered by urgency.
    """
    try:
        pending_data = manager.get_pending_reviews(reviewer_id=reviewer_id)

        return [PendingReviewResponse(**item) for item in pending_data]

    except Exception as e:
        logger.error("Failed to get pending reviews", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@curation_router.post("/cluster-group", response_model=Dict[str, str])
async def create_cluster_group(
    request: CreateClusterGroupRequest,
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Create a manual cluster group

    Groups CLUST-1/CLUST-2 clusters for later assignment to a parent narrative.
    Useful for preparing strategic groupings before narrative creation.
    """
    try:
        group_uuid = manager.create_cluster_group(
            group_name=request.group_name,
            cluster_ids=request.cluster_ids,
            curator_id=request.curator_id,
            description=request.description,
            rationale=request.rationale,
            strategic_significance=request.strategic_significance,
            cluster_metadata=request.cluster_metadata,
        )

        return {
            "group_uuid": group_uuid,
            "group_name": request.group_name,
            "status": "created",
            "message": f"Cluster group '{request.group_name}' created successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create cluster group", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@curation_router.get("/validate", response_model=ValidationResponse)
async def validate_workflow(
    manager: ManualNarrativeManager = Depends(get_manual_manager),
):
    """
    Validate curation workflow integrity

    Runs comprehensive checks on the curation workflow to identify
    data integrity issues or workflow problems.
    """
    try:
        validation_results = manager.validate_curation_workflow()
        return ValidationResponse(**validation_results)

    except Exception as e:
        logger.error("Failed to validate workflow", error=str(e))
        return ValidationResponse(
            timestamp=datetime.utcnow().isoformat(),
            overall_status="ERROR",
            error=str(e),
            checks=[],
        )


@curation_router.get("/narrative/{narrative_uuid}", response_model=Dict[str, Any])
async def get_narrative_details(
    narrative_uuid: str, manager: ManualNarrativeManager = Depends(get_manual_manager)
):
    """
    Get detailed information about a narrative

    Returns comprehensive narrative data including curation metadata,
    parent-child relationships, and workflow history.
    """
    try:
        narrative = manager.get_narrative_by_uuid(narrative_uuid)
        if not narrative:
            raise HTTPException(status_code=404, detail="Narrative not found")

        # Build comprehensive response
        response = {
            "id": str(narrative.id),
            "narrative_id": narrative.narrative_id,
            "title": narrative.title,
            "summary": narrative.summary,
            "origin_language": narrative.origin_language,
            "confidence_rating": narrative.confidence_rating,
            "created_at": narrative.created_at.isoformat(),
            "updated_at": narrative.updated_at.isoformat(),
            # Hierarchy info
            "parent_id": str(narrative.parent_id) if narrative.parent_id else None,
            "is_parent": narrative.is_parent(),
            "is_child": narrative.is_child(),
            "hierarchy_level": narrative.get_hierarchy_level(),
            # Curation fields (if available)
            "fringe_notes": narrative.fringe_notes or [],
            "data_quality_notes": narrative.data_quality_notes or [],
        }

        # Add curation fields if they exist (from migration)
        if hasattr(narrative, "curation_status"):
            response.update(
                {
                    "curation_status": getattr(narrative, "curation_status", None),
                    "curation_source": getattr(narrative, "curation_source", None),
                    "curator_id": getattr(narrative, "curator_id", None),
                    "reviewer_id": getattr(narrative, "reviewer_id", None),
                    "editorial_priority": getattr(
                        narrative, "editorial_priority", None
                    ),
                    "manual_cluster_ids": getattr(narrative, "manual_cluster_ids", []),
                    "curation_notes": getattr(narrative, "curation_notes", []),
                }
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get narrative details", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Health Check and Status Endpoints
# ============================================================================


@curation_router.get("/health", response_model=Dict[str, Any])
async def health_check(manager: ManualNarrativeManager = Depends(get_manual_manager)):
    """
    Health check for curation system

    Returns basic system health and statistics.
    """
    try:
        # Get basic counts from dashboard
        dashboard_data = manager.get_curation_dashboard(limit=1000)

        status_counts = {}
        for item in dashboard_data:
            status = item.get("curation_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_narratives": len(dashboard_data),
                "status_distribution": status_counts,
                "manual_narratives": len(
                    [item for item in dashboard_data if item.get("is_manual", False)]
                ),
                "parent_narratives": len(
                    [item for item in dashboard_data if item.get("is_parent", False)]
                ),
            },
        }

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
