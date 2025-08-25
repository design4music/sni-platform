#!/usr/bin/env python3
"""
Manual Curation Integration Tests
Strategic Narrative Intelligence ETL Pipeline

Comprehensive integration tests for manual parent narrative curation system.
Tests database schema, API endpoints, and workflow validation.
"""

import json
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from etl_pipeline.core.curation.manual_narrative_manager import \
    ManualNarrativeManager
from etl_pipeline.core.database import get_db_session
from etl_pipeline.core.database.models import NarrativeNSF1 as Narrative


class TestManualCurationSchema:
    """Test database schema for manual curation"""

    @pytest.fixture
    def db_session(self):
        """Database session fixture"""
        session = get_db_session()
        yield session
        session.close()

    def test_curation_status_enum_exists(self, db_session):
        """Test that curation status enum type exists"""
        result = db_session.execute(
            text("SELECT 1 FROM pg_type WHERE typname = 'curation_status'")
        ).fetchone()
        assert result is not None, "curation_status enum type should exist"

    def test_curation_columns_exist(self, db_session):
        """Test that new curation columns exist in narratives table"""
        required_columns = [
            "curation_status",
            "curation_source",
            "curator_id",
            "reviewer_id",
            "curation_notes",
            "manual_cluster_ids",
            "editorial_priority",
            "review_deadline",
            "published_at",
        ]

        for column in required_columns:
            result = db_session.execute(
                text(
                    f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'narratives' AND column_name = '{column}'
                """
                )
            ).fetchone()
            assert (
                result is not None
            ), f"Column {column} should exist in narratives table"

    def test_audit_log_table_exists(self, db_session):
        """Test that audit log table exists with proper structure"""
        result = db_session.execute(
            text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'narrative_curation_log'"
            )
        ).fetchone()
        assert result is not None, "narrative_curation_log table should exist"

        # Check key columns
        required_columns = ["narrative_id", "action_type", "actor_id", "created_at"]
        for column in required_columns:
            result = db_session.execute(
                text(
                    f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'narrative_curation_log' AND column_name = '{column}'
                """
                )
            ).fetchone()
            assert result is not None, f"Audit log should have {column} column"

    def test_cluster_groups_table_exists(self, db_session):
        """Test that manual cluster groups table exists"""
        result = db_session.execute(
            text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'manual_cluster_groups'"
            )
        ).fetchone()
        assert result is not None, "manual_cluster_groups table should exist"

    def test_curation_views_exist(self, db_session):
        """Test that curation dashboard views exist"""
        views = ["curation_dashboard", "pending_reviews"]
        for view in views:
            result = db_session.execute(
                text(
                    f"SELECT 1 FROM information_schema.views WHERE table_name = '{view}'"
                )
            ).fetchone()
            assert result is not None, f"View {view} should exist"

    def test_curation_functions_exist(self, db_session):
        """Test that curation functions exist"""
        functions = [
            "create_manual_parent_narrative",
            "assign_children_to_manual_parent",
            "update_curation_status",
            "validate_curation_workflow",
        ]

        for func in functions:
            result = db_session.execute(
                text(
                    f"SELECT 1 FROM information_schema.routines WHERE routine_name = '{func}'"
                )
            ).fetchone()
            assert result is not None, f"Function {func} should exist"


class TestManualNarrativeManager:
    """Test ManualNarrativeManager functionality"""

    @pytest.fixture
    def db_session(self):
        """Database session fixture"""
        session = get_db_session()
        yield session
        session.rollback()  # Rollback any changes after test
        session.close()

    @pytest.fixture
    def manager(self, db_session):
        """Manual narrative manager fixture"""
        return ManualNarrativeManager(db_session)

    def test_create_manual_parent_basic(self, manager):
        """Test basic manual parent creation"""
        curator_id = "test_curator_001"
        title = "Test Strategic Parent Narrative"
        summary = "This is a test strategic parent narrative created for integration testing purposes."

        narrative_uuid, narrative_id = manager.create_manual_parent(
            title=title,
            summary=summary,
            curator_id=curator_id,
            cluster_ids=["cluster_001", "cluster_002"],
            editorial_priority=2,
        )

        # Validate return values
        assert narrative_uuid is not None
        assert narrative_id is not None
        assert len(narrative_uuid) == 36  # UUID format
        assert narrative_id.startswith("EN-")  # Expected format

        # Validate in database
        narrative = manager.get_narrative_by_uuid(narrative_uuid)
        assert narrative is not None
        assert narrative.title == title
        assert narrative.summary == summary
        assert narrative.parent_id is None  # Should be parent narrative

    def test_create_manual_parent_with_metadata(self, manager):
        """Test manual parent creation with additional metadata"""
        curator_id = "test_curator_002"
        title = "Strategic Parent with Metadata"
        summary = "Parent narrative with additional metadata for testing comprehensive functionality."
        metadata = {
            "strategic_themes": ["geopolitics", "energy"],
            "confidence_level": "high",
            "source_diversity": 15,
        }

        narrative_uuid, narrative_id = manager.create_manual_parent(
            title=title,
            summary=summary,
            curator_id=curator_id,
            metadata=metadata,
            editorial_priority=1,
        )

        # Verify creation
        assert narrative_uuid is not None
        assert narrative_id is not None

    def test_assign_children_to_parent(self, manager, db_session):
        """Test assigning child narratives to manual parent"""
        # First create a manual parent
        curator_id = "test_curator_003"
        parent_uuid, parent_id = manager.create_manual_parent(
            title="Parent for Assignment Test",
            summary="Parent narrative created specifically for testing child assignment functionality.",
            curator_id=curator_id,
        )

        # Create some child narratives (simulate existing CLUST-2 output)
        child_uuids = []
        for i in range(3):
            child = Narrative(
                narrative_id=f"EN-TEST-CHILD-{i:03d}",
                title=f"Test Child Narrative {i+1}",
                summary=f"Child narrative {i+1} for assignment testing",
                origin_language="en",
                parent_id=None,  # Start as orphaned
            )
            db_session.add(child)
            db_session.flush()  # Get UUID
            child_uuids.append(str(child.id))

        db_session.commit()

        # Assign children to parent
        assigned_count = manager.assign_children_to_parent(
            parent_uuid=parent_uuid,
            child_uuids=child_uuids,
            curator_id=curator_id,
            rationale="Testing child assignment functionality",
        )

        # Validate assignment
        assert assigned_count == 3

        # Verify in database
        for child_uuid in child_uuids:
            child = manager.get_narrative_by_uuid(child_uuid)
            assert child is not None
            assert str(child.parent_id) == parent_uuid

    def test_update_curation_status_workflow(self, manager):
        """Test curation status workflow validation"""
        curator_id = "test_curator_004"

        # Create manual parent in draft status
        parent_uuid, parent_id = manager.create_manual_parent(
            title="Status Workflow Test",
            summary="Testing curation status workflow transitions and validation rules.",
            curator_id=curator_id,
        )

        # Test valid transitions
        # Draft -> Pending Review
        success = manager.update_curation_status(
            narrative_uuid=parent_uuid,
            new_status="pending_review",
            actor_id=curator_id,
            notes="Submitting for review",
        )
        assert success is True

        # Pending Review -> Approved
        success = manager.update_curation_status(
            narrative_uuid=parent_uuid,
            new_status="approved",
            actor_id="reviewer_001",
            notes="Approved for publication",
        )
        assert success is True

        # Approved -> Published
        success = manager.update_curation_status(
            narrative_uuid=parent_uuid,
            new_status="published",
            actor_id="publisher_001",
            notes="Published to production",
        )
        assert success is True

    def test_get_curation_dashboard(self, manager):
        """Test curation dashboard data retrieval"""
        # Create some test data
        curator_id = "dashboard_curator"

        for i in range(3):
            manager.create_manual_parent(
                title=f"Dashboard Test Narrative {i+1}",
                summary=f"Test narrative {i+1} for dashboard functionality testing and validation.",
                curator_id=curator_id,
                editorial_priority=i + 1,
            )

        # Get dashboard data
        dashboard_data = manager.get_curation_dashboard(curator_id=curator_id, limit=10)

        # Validate results
        assert len(dashboard_data) >= 3
        for item in dashboard_data:
            assert item["curator_id"] == curator_id
            assert item["is_manual"] is True
            assert item["is_parent"] is True

    def test_get_pending_reviews(self, manager):
        """Test pending reviews retrieval"""
        curator_id = "pending_curator"
        reviewer_id = "pending_reviewer"

        # Create narrative in pending review state
        parent_uuid, parent_id = manager.create_manual_parent(
            title="Pending Review Test",
            summary="Narrative created specifically for testing pending review functionality.",
            curator_id=curator_id,
        )

        # Move to pending review
        manager.update_curation_status(
            narrative_uuid=parent_uuid, new_status="pending_review", actor_id=curator_id
        )

        # Get pending reviews
        pending_reviews = manager.get_pending_reviews()

        # Should find our test narrative
        assert len(pending_reviews) >= 1
        found = False
        for review in pending_reviews:
            if review["id"] == parent_uuid:
                found = True
                assert review["curation_status"] == "pending_review"
                break
        assert found, "Test narrative should be in pending reviews"

    def test_create_cluster_group(self, manager):
        """Test manual cluster group creation"""
        curator_id = "cluster_curator"
        group_name = "Test Strategic Cluster Group"
        cluster_ids = ["clust1_001", "clust1_002", "clust2_003"]

        group_uuid = manager.create_cluster_group(
            group_name=group_name,
            cluster_ids=cluster_ids,
            curator_id=curator_id,
            description="Test cluster grouping for integration validation",
            rationale="Testing cluster grouping functionality",
            strategic_significance="High - represents coordinated disinformation campaign",
        )

        # Validate creation
        assert group_uuid is not None
        assert len(group_uuid) == 36  # UUID format

    def test_validate_curation_workflow(self, manager):
        """Test curation workflow validation"""
        validation_results = manager.validate_curation_workflow()

        # Should return validation structure
        assert "timestamp" in validation_results
        assert "overall_status" in validation_results
        assert "checks" in validation_results
        assert isinstance(validation_results["checks"], list)

        # Should have at least some checks
        assert len(validation_results["checks"]) >= 3


class TestWorkflowIntegration:
    """Test end-to-end workflow integration"""

    @pytest.fixture
    def db_session(self):
        session = get_db_session()
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def manager(self, db_session):
        return ManualNarrativeManager(db_session)

    def test_complete_manual_curation_workflow(self, manager, db_session):
        """Test complete workflow from creation to publication"""
        curator_id = "integration_curator"
        reviewer_id = "integration_reviewer"

        # Step 1: Create strategic cluster group
        group_uuid = manager.create_cluster_group(
            group_name="Integration Test Strategic Group",
            cluster_ids=["int_clust_001", "int_clust_002", "int_clust_003"],
            curator_id=curator_id,
            rationale="Testing complete workflow integration",
        )
        assert group_uuid is not None

        # Step 2: Create manual parent narrative
        parent_uuid, parent_id = manager.create_manual_parent(
            title="Complete Integration Test Narrative",
            summary="This is a comprehensive test of the complete manual curation workflow from creation to publication.",
            curator_id=curator_id,
            cluster_ids=["int_clust_001", "int_clust_002", "int_clust_003"],
            editorial_priority=1,
        )
        assert parent_uuid is not None

        # Step 3: Create and assign child narratives
        child_uuids = []
        for i in range(2):
            child = Narrative(
                narrative_id=f"EN-INT-CHILD-{i:03d}",
                title=f"Integration Child {i+1}",
                summary=f"Child narrative {i+1} for complete workflow integration testing",
                origin_language="en",
            )
            db_session.add(child)
            db_session.flush()
            child_uuids.append(str(child.id))

        db_session.commit()

        assigned_count = manager.assign_children_to_parent(
            parent_uuid=parent_uuid,
            child_uuids=child_uuids,
            curator_id=curator_id,
            rationale="Complete workflow test assignment",
        )
        assert assigned_count == 2

        # Step 4: Progress through workflow states
        # Draft -> Pending Review
        success = manager.update_curation_status(
            narrative_uuid=parent_uuid,
            new_status="pending_review",
            actor_id=curator_id,
            notes="Ready for editorial review",
        )
        assert success is True

        # Pending Review -> Approved
        success = manager.update_curation_status(
            narrative_uuid=parent_uuid,
            new_status="approved",
            actor_id=reviewer_id,
            notes="Approved after review",
        )
        assert success is True

        # Approved -> Published
        success = manager.update_curation_status(
            narrative_uuid=parent_uuid,
            new_status="published",
            actor_id=reviewer_id,
            notes="Published to production system",
        )
        assert success is True

        # Step 5: Validate final state
        narrative = manager.get_narrative_by_uuid(parent_uuid)
        assert narrative is not None

        # Verify parent-child relationships
        children = (
            db_session.query(Narrative).filter(Narrative.parent_id == parent_uuid).all()
        )
        assert len(children) == 2

        # Step 6: Run workflow validation
        validation = manager.validate_curation_workflow()
        assert validation["overall_status"] in ["PASS", "WARNING"]  # Should not be FAIL

        print(f"\n✓ Complete workflow integration test passed:")
        print(f"  - Created cluster group: {group_uuid}")
        print(f"  - Created parent narrative: {parent_id}")
        print(f"  - Assigned {assigned_count} children")
        print(f"  - Progressed through workflow states to 'published'")
        print(f"  - Validation status: {validation['overall_status']}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
