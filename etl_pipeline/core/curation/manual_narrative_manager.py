#!/usr/bin/env python3
"""
Manual Parent Narrative Manager
Strategic Narrative Intelligence ETL Pipeline

Handles manual curation of parent narratives that span multiple CLUST-1/CLUST-2 clusters.
Integrates with existing pipeline while providing editorial workflow management.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from etl_pipeline.core.database import get_db_session
from etl_pipeline.core.database.models import NarrativeNSF1 as Narrative

logger = structlog.get_logger(__name__)


class ManualNarrativeManager:
    """
    Manager for manual parent narrative curation workflow

    Provides high-level operations for:
    - Creating strategic parent narratives manually
    - Grouping multiple CLUST-1/CLUST-2 clusters into cohesive narratives
    - Managing editorial workflow (draft → review → publish)
    - Integrating with automated pipeline outputs
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize with database session"""
        self.session = session or get_db_session()
        self.logger = logger.bind(component="manual_narrative_manager")

    def create_manual_parent(
        self,
        title: str,
        summary: str,
        curator_id: str,
        cluster_ids: Optional[List[str]] = None,
        editorial_priority: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """
        Create a new manual parent narrative

        Args:
            title: Narrative title
            summary: Narrative summary
            curator_id: ID of curator creating this narrative
            cluster_ids: Optional list of CLUST-1/CLUST-2 cluster IDs to group
            editorial_priority: Priority level (1=high, 5=low)
            metadata: Additional metadata for the narrative

        Returns:
            Tuple of (narrative_uuid, narrative_display_id)
        """
        try:
            # Use SQL function for consistent ID generation and logging
            result = self.session.execute(
                text(
                    """
                    SELECT narrative_uuid, narrative_display_id, status
                    FROM create_manual_parent_narrative(
                        :title, :summary, :curator_id, :cluster_ids, :priority
                    )
                """
                ),
                {
                    "title": title,
                    "summary": summary,
                    "curator_id": curator_id,
                    "cluster_ids": json.dumps(cluster_ids or []),
                    "priority": editorial_priority,
                },
            ).fetchone()

            if not result or result.status != "created":
                raise ValueError(
                    f"Failed to create manual parent: {result.status if result else 'unknown error'}"
                )

            narrative_uuid = str(result.narrative_uuid)
            narrative_display_id = result.narrative_display_id

            # Add optional metadata if provided
            if metadata:
                self._add_curation_note(
                    narrative_uuid,
                    curator_id,
                    "metadata_added",
                    f"Initial metadata: {json.dumps(metadata, indent=2)}",
                    metadata,
                )

            self.logger.info(
                "Created manual parent narrative",
                narrative_uuid=narrative_uuid,
                narrative_id=narrative_display_id,
                curator=curator_id,
                cluster_count=len(cluster_ids or []),
            )

            return narrative_uuid, narrative_display_id

        except Exception as e:
            self.logger.error(
                "Failed to create manual parent narrative",
                error=str(e),
                curator=curator_id,
                title=title[:50] + "..." if len(title) > 50 else title,
            )
            raise

    def assign_children_to_parent(
        self,
        parent_uuid: str,
        child_uuids: List[str],
        curator_id: str,
        rationale: Optional[str] = None,
    ) -> int:
        """
        Assign child narratives to a manual parent narrative

        Args:
            parent_uuid: UUID of the parent narrative
            child_uuids: List of child narrative UUIDs to assign
            curator_id: ID of curator performing assignment
            rationale: Optional explanation for the assignment

        Returns:
            Number of children successfully assigned
        """
        try:
            # Convert Python list to PostgreSQL array format
            child_array = "{" + ",".join(child_uuids) + "}"

            result = self.session.execute(
                text(
                    """
                    SELECT assigned_count, status
                    FROM assign_children_to_manual_parent(
                        :parent_uuid::uuid, :child_uuids::uuid[], :curator_id, :rationale
                    )
                """
                ),
                {
                    "parent_uuid": parent_uuid,
                    "child_uuids": child_array,
                    "curator_id": curator_id,
                    "rationale": rationale,
                },
            ).fetchone()

            if not result:
                raise ValueError("Assignment function returned no result")

            if result.status != "success":
                raise ValueError(f"Assignment failed: {result.status}")

            assigned_count = result.assigned_count

            self.logger.info(
                "Assigned children to manual parent",
                parent_uuid=parent_uuid,
                assigned_count=assigned_count,
                requested_count=len(child_uuids),
                curator=curator_id,
            )

            return assigned_count

        except Exception as e:
            self.logger.error(
                "Failed to assign children to parent",
                error=str(e),
                parent_uuid=parent_uuid,
                child_count=len(child_uuids),
                curator=curator_id,
            )
            raise

    def update_curation_status(
        self,
        narrative_uuid: str,
        new_status: str,
        actor_id: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Update the curation status of a narrative with workflow validation

        Args:
            narrative_uuid: UUID of narrative to update
            new_status: New curation status
            actor_id: ID of user making the change
            notes: Optional notes about the status change

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.session.execute(
                text(
                    """
                    SELECT success, message
                    FROM update_curation_status(
                        :narrative_uuid::uuid, :new_status::curation_status, :actor_id, :notes
                    )
                """
                ),
                {
                    "narrative_uuid": narrative_uuid,
                    "new_status": new_status,
                    "actor_id": actor_id,
                    "notes": notes,
                },
            ).fetchone()

            if not result:
                raise ValueError("Status update function returned no result")

            if not result.success:
                self.logger.warning(
                    "Status update rejected",
                    narrative_uuid=narrative_uuid,
                    new_status=new_status,
                    reason=result.message,
                    actor=actor_id,
                )
                return False

            self.logger.info(
                "Updated curation status",
                narrative_uuid=narrative_uuid,
                new_status=new_status,
                actor=actor_id,
                notes=notes,
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to update curation status",
                error=str(e),
                narrative_uuid=narrative_uuid,
                new_status=new_status,
                actor=actor_id,
            )
            return False

    def get_curation_dashboard(
        self,
        curator_id: Optional[str] = None,
        status_filter: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get curation dashboard data

        Args:
            curator_id: Optional filter by curator
            status_filter: Optional list of status values to filter by
            limit: Maximum number of items to return

        Returns:
            List of narrative dictionaries for dashboard
        """
        try:
            query = """
                SELECT 
                    id,
                    narrative_id,
                    title,
                    curation_status,
                    curation_source,
                    curator_id,
                    reviewer_id,
                    editorial_priority,
                    review_deadline,
                    created_at,
                    updated_at,
                    published_at,
                    child_count,
                    manual_cluster_count,
                    is_parent,
                    is_manual,
                    is_overdue,
                    last_activity
                FROM curation_dashboard
            """

            conditions = []
            params = {}

            if curator_id:
                conditions.append("curator_id = :curator_id")
                params["curator_id"] = curator_id

            if status_filter:
                conditions.append("curation_status = ANY(:status_filter)")
                params["status_filter"] = status_filter

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY editorial_priority ASC, updated_at DESC LIMIT :limit"
            params["limit"] = limit

            result = self.session.execute(text(query), params).fetchall()

            dashboard_items = []
            for row in result:
                item = {
                    "id": str(row.id),
                    "narrative_id": row.narrative_id,
                    "title": row.title,
                    "curation_status": row.curation_status,
                    "curation_source": row.curation_source,
                    "curator_id": row.curator_id,
                    "reviewer_id": row.reviewer_id,
                    "editorial_priority": row.editorial_priority,
                    "review_deadline": (
                        row.review_deadline.isoformat() if row.review_deadline else None
                    ),
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                    "published_at": (
                        row.published_at.isoformat() if row.published_at else None
                    ),
                    "child_count": row.child_count,
                    "manual_cluster_count": row.manual_cluster_count,
                    "is_parent": row.is_parent,
                    "is_manual": row.is_manual,
                    "is_overdue": row.is_overdue,
                    "last_activity": (
                        row.last_activity.isoformat() if row.last_activity else None
                    ),
                }
                dashboard_items.append(item)

            return dashboard_items

        except Exception as e:
            self.logger.error("Failed to get curation dashboard", error=str(e))
            return []

    def get_pending_reviews(
        self, reviewer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get items pending review, ordered by urgency

        Args:
            reviewer_id: Optional filter by assigned reviewer

        Returns:
            List of narrative dictionaries needing review
        """
        try:
            query = """
                SELECT 
                    id,
                    narrative_id,
                    title,
                    curation_status,
                    curator_id,
                    reviewer_id,
                    editorial_priority,
                    review_deadline,
                    child_count,
                    review_urgency,
                    days_until_deadline,
                    created_at,
                    updated_at
                FROM pending_reviews
            """

            params = {}
            if reviewer_id:
                query += " WHERE reviewer_id = :reviewer_id"
                params["reviewer_id"] = reviewer_id

            result = self.session.execute(text(query), params).fetchall()

            pending_items = []
            for row in result:
                item = {
                    "id": str(row.id),
                    "narrative_id": row.narrative_id,
                    "title": row.title,
                    "curation_status": row.curation_status,
                    "curator_id": row.curator_id,
                    "reviewer_id": row.reviewer_id,
                    "editorial_priority": row.editorial_priority,
                    "review_deadline": (
                        row.review_deadline.isoformat() if row.review_deadline else None
                    ),
                    "child_count": row.child_count,
                    "review_urgency": row.review_urgency,
                    "days_until_deadline": row.days_until_deadline,
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                }
                pending_items.append(item)

            return pending_items

        except Exception as e:
            self.logger.error("Failed to get pending reviews", error=str(e))
            return []

    def create_cluster_group(
        self,
        group_name: str,
        cluster_ids: List[str],
        curator_id: str,
        description: Optional[str] = None,
        rationale: Optional[str] = None,
        strategic_significance: Optional[str] = None,
        cluster_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a manual cluster group for later narrative assignment

        Args:
            group_name: Name for this cluster grouping
            cluster_ids: List of CLUST-1/CLUST-2 cluster IDs
            curator_id: ID of curator creating the group
            description: Optional description of the group
            rationale: Why these clusters were grouped together
            strategic_significance: Strategic importance of this grouping
            cluster_metadata: Optional metadata from original clusters

        Returns:
            UUID of created cluster group
        """
        try:
            group_uuid = str(uuid.uuid4())

            self.session.execute(
                text(
                    """
                    INSERT INTO manual_cluster_groups (
                        id, group_name, group_description, cluster_ids, cluster_metadata,
                        curator_id, curation_rationale, strategic_significance
                    ) VALUES (
                        :group_uuid::uuid, :group_name, :description, :cluster_ids::jsonb, :cluster_metadata::jsonb,
                        :curator_id, :rationale, :strategic_significance
                    )
                """
                ),
                {
                    "group_uuid": group_uuid,
                    "group_name": group_name,
                    "description": description,
                    "cluster_ids": json.dumps(cluster_ids),
                    "cluster_metadata": json.dumps(cluster_metadata or {}),
                    "curator_id": curator_id,
                    "rationale": rationale,
                    "strategic_significance": strategic_significance,
                },
            )

            self.session.commit()

            self.logger.info(
                "Created manual cluster group",
                group_uuid=group_uuid,
                group_name=group_name,
                cluster_count=len(cluster_ids),
                curator=curator_id,
            )

            return group_uuid

        except Exception as e:
            self.session.rollback()
            self.logger.error(
                "Failed to create cluster group",
                error=str(e),
                group_name=group_name,
                curator=curator_id,
            )
            raise

    def validate_curation_workflow(self) -> Dict[str, Any]:
        """
        Validate curation workflow integrity

        Returns:
            Dictionary with validation results
        """
        try:
            result = self.session.execute(
                text(
                    "SELECT check_name, status, details, affected_count FROM validate_curation_workflow()"
                )
            ).fetchall()

            validation_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "PASS",
                "checks": [],
            }

            for row in result:
                check = {
                    "check_name": row.check_name,
                    "status": row.status,
                    "details": row.details,
                    "affected_count": row.affected_count,
                }
                validation_results["checks"].append(check)

                # Update overall status if any check fails
                if row.status == "FAIL":
                    validation_results["overall_status"] = "FAIL"
                elif (
                    row.status == "WARNING"
                    and validation_results["overall_status"] == "PASS"
                ):
                    validation_results["overall_status"] = "WARNING"

            self.logger.info(
                "Completed curation workflow validation",
                overall_status=validation_results["overall_status"],
                check_count=len(validation_results["checks"]),
            )

            return validation_results

        except Exception as e:
            self.logger.error("Failed to validate curation workflow", error=str(e))
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "ERROR",
                "error": str(e),
                "checks": [],
            }

    def _add_curation_note(
        self,
        narrative_uuid: str,
        actor_id: str,
        note_type: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a curation note to the audit log

        Args:
            narrative_uuid: UUID of narrative
            actor_id: ID of user adding note
            note_type: Type of note (for categorization)
            summary: Summary of the action/note
            metadata: Optional additional data
        """
        try:
            self.session.execute(
                text(
                    """
                    INSERT INTO narrative_curation_log (
                        narrative_id, action_type, action_reason, actor_id, metadata
                    ) VALUES (
                        :narrative_uuid::uuid, :note_type, :summary, :actor_id, :metadata::jsonb
                    )
                """
                ),
                {
                    "narrative_uuid": narrative_uuid,
                    "note_type": note_type,
                    "summary": summary,
                    "actor_id": actor_id,
                    "metadata": json.dumps(metadata or {}),
                },
            )
            self.session.commit()

        except Exception as e:
            self.logger.warning(
                "Failed to add curation note",
                error=str(e),
                narrative_uuid=narrative_uuid,
                note_type=note_type,
            )

    def get_narrative_by_uuid(self, narrative_uuid: str) -> Optional[Narrative]:
        """Get narrative by UUID"""
        try:
            return (
                self.session.query(Narrative)
                .filter(Narrative.id == narrative_uuid)
                .first()
            )
        except Exception as e:
            self.logger.error(
                "Failed to get narrative by UUID",
                error=str(e),
                narrative_uuid=narrative_uuid,
            )
            return None

    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()


# Convenience functions for common operations
def create_strategic_parent(
    title: str,
    summary: str,
    curator_id: str,
    cluster_ids: Optional[List[str]] = None,
    priority: int = 3,
) -> Tuple[str, str]:
    """
    Quick function to create a strategic parent narrative

    Returns:
        Tuple of (narrative_uuid, narrative_display_id)
    """
    with ManualNarrativeManager() as manager:
        return manager.create_manual_parent(
            title, summary, curator_id, cluster_ids, priority
        )


def assign_narratives_to_parent(
    parent_uuid: str,
    child_uuids: List[str],
    curator_id: str,
    rationale: Optional[str] = None,
) -> int:
    """
    Quick function to assign child narratives to a parent

    Returns:
        Number of children successfully assigned
    """
    with ManualNarrativeManager() as manager:
        return manager.assign_children_to_parent(
            parent_uuid, child_uuids, curator_id, rationale
        )
