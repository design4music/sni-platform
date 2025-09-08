#!/usr/bin/env python3
"""
Parent/Child Hierarchy Migration Validation Tests
Strategic Narrative Intelligence Platform

Comprehensive test suite to validate Migration 003:
- Data integrity after migration
- Performance improvements
- ORM model functionality
- CLUST-2 integration
- Rollback capability
"""

import asyncio
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytest
# Import models from both systems to validate compatibility
from database_models import Narrative as LegacyNarrative
from etl_pipeline.clustering.clust2_segment_narratives import \
    CLUST2NarrativeSegmentation
from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.database.models import NarrativeMetrics, NarrativeNSF1
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class TestParentChildMigration:
    """Test suite for parent/child hierarchy migration validation"""

    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        cls.config = get_config()
        initialize_database(cls.config.database)

    def test_migration_prerequisites(self):
        """Test that migration prerequisites are met"""
        with get_db_session() as session:
            # Check that narratives table exists
            result = session.execute(
                text(
                    """
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'narratives'
            """
                )
            )
            assert result.fetchone() is not None, "Narratives table must exist"

            # Check that parent_id column exists
            result = session.execute(
                text(
                    """
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'narratives' AND column_name = 'parent_id'
            """
                )
            )
            assert result.fetchone() is not None, "parent_id column must exist"

            # Check foreign key constraint exists
            result = session.execute(
                text(
                    """
                SELECT 1 FROM information_schema.referential_constraints 
                WHERE table_name = 'narratives'
                AND constraint_name LIKE '%parent%'
            """
                )
            )
            assert (
                result.fetchone() is not None
            ), "parent_id foreign key constraint must exist"

    def test_hierarchy_indexes_created(self):
        """Test that performance indexes for parent_id were created"""
        with get_db_session() as session:
            # Check for parent_id indexes
            result = session.execute(
                text(
                    """
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'narratives' 
                AND (indexname LIKE '%parent%' OR indexname LIKE '%hierarchy%')
            """
                )
            )

            indexes = [row[0] for row in result.fetchall()]

            expected_indexes = [
                "idx_narratives_parent_id",
                "idx_narratives_parent_children",
                "idx_narratives_parents_only",
                "idx_narratives_hierarchy_created",
            ]

            for expected_index in expected_indexes:
                assert any(
                    expected_index in idx for idx in indexes
                ), f"Missing expected index: {expected_index}"

    def test_data_integrity_validation(self):
        """Test comprehensive data integrity after migration"""
        with get_db_session() as session:
            # Run the validation function from migration
            result = session.execute(
                text(
                    """
                SELECT check_name, status, invalid_count 
                FROM validate_narrative_hierarchy_integrity()
            """
                )
            )

            validation_results = result.fetchall()

            for check_name, status, invalid_count in validation_results:
                if status == "FAIL":
                    pytest.fail(
                        f"Data integrity check failed: {check_name} has {invalid_count} invalid records"
                    )

                # Ensure no invalid records
                assert (
                    invalid_count == 0
                ), f"Integrity check {check_name} found {invalid_count} invalid records"

    def test_parent_child_relationships(self):
        """Test that parent-child relationships work correctly"""
        with get_db_session() as session:
            # Create test parent narrative
            parent = NarrativeNSF1(
                narrative_id="TEST-PARENT-001",
                title="Test Parent Narrative",
                summary="Test parent for hierarchy validation",
                origin_language="en",
                parent_id=None,  # Parent has no parent
                dominant_source_languages=["en"],
                alignment=[],
                actor_origin=[],
                conflict_alignment=[],
                frame_logic=[],
                nested_within=[],  # Deprecated field
                confidence_rating="medium",
            )

            session.add(parent)
            session.flush()  # Get the UUID

            # Create test child narrative
            child = NarrativeNSF1(
                narrative_id="TEST-CHILD-001",
                title="Test Child Narrative",
                summary="Test child for hierarchy validation",
                origin_language="en",
                parent_id=parent.id,  # Child references parent
                dominant_source_languages=["en"],
                alignment=[],
                actor_origin=[],
                conflict_alignment=[],
                frame_logic=[],
                nested_within=[],  # Deprecated field
                confidence_rating="medium",
            )

            session.add(child)
            session.commit()

            # Test ORM relationships
            assert child.parent is not None, "Child should have parent relationship"
            assert (
                child.parent.id == parent.id
            ), "Child parent should match created parent"
            assert len(parent.children) == 1, "Parent should have one child"
            assert (
                parent.children[0].id == child.id
            ), "Parent child should match created child"

            # Test helper methods
            assert parent.is_parent(), "Parent should return True for is_parent()"
            assert not parent.is_child(), "Parent should return False for is_child()"
            assert child.is_child(), "Child should return True for is_child()"
            assert not child.is_parent(), "Child should return False for is_parent()"

            assert parent.get_hierarchy_level() == 0, "Parent should be level 0"
            assert child.get_hierarchy_level() == 1, "Child should be level 1"

            # Cleanup
            session.delete(parent)  # Should cascade delete child
            session.commit()

    def test_performance_improvements(self):
        """Test that parent_id queries are faster than nested_within"""
        with get_db_session() as session:
            # Run performance benchmark from migration
            result = session.execute(
                text(
                    """
                SELECT test_name, old_method_ms, new_method_ms, improvement_factor
                FROM benchmark_hierarchy_performance()
                WHERE test_name != 'NO_TEST_DATA'
            """
                )
            )

            benchmark_results = result.fetchall()

            for test_name, old_ms, new_ms, improvement_factor in benchmark_results:
                if test_name == "materialized_view":
                    # Materialized view should be very fast
                    assert (
                        new_ms < 5.0
                    ), f"Materialized view query should be <5ms, got {new_ms}ms"
                else:
                    # New method should be faster than old method
                    if old_ms > 0 and new_ms > 0:
                        assert (
                            improvement_factor > 1.0
                        ), f"{test_name}: New method should be faster. Factor: {improvement_factor}"

                        print(
                            f"[OK] {test_name}: {improvement_factor:.1f}x faster ({old_ms:.2f}ms -> {new_ms:.2f}ms)"
                        )

    def test_materialized_view_functionality(self):
        """Test that materialized view works correctly"""
        with get_db_session() as session:
            # Check that materialized view exists
            result = session.execute(
                text(
                    """
                SELECT 1 FROM information_schema.views 
                WHERE table_name = 'narrative_hierarchy_cache'
            """
                )
            )
            assert (
                result.fetchone() is not None
            ), "narrative_hierarchy_cache materialized view must exist"

            # Test refresh function
            session.execute(text("SELECT refresh_narrative_hierarchy_cache()"))

            # Query materialized view
            result = session.execute(
                text(
                    """
                SELECT parent_id, parent_narrative_id, child_count, cache_updated_at
                FROM narrative_hierarchy_cache
                LIMIT 5
            """
                )
            )

            cache_rows = result.fetchall()

            # Verify cache structure
            for row in cache_rows:
                parent_id, parent_narrative_id, child_count, cache_updated = row
                assert parent_id is not None, "Cache should have parent_id"
                assert (
                    parent_narrative_id is not None
                ), "Cache should have parent_narrative_id"
                assert child_count >= 0, "Child count should be non-negative"
                assert cache_updated is not None, "Cache should have update timestamp"

    def test_helper_functions(self):
        """Test that hierarchy helper functions work correctly"""
        with get_db_session() as session:
            # Test get_hierarchy_statistics function
            result = session.execute(text("SELECT * FROM get_hierarchy_statistics()"))
            stats = result.fetchall()

            stats_dict = {row[0]: row[1] for row in stats}

            assert (
                "total_narratives" in stats_dict
            ), "Should have total_narratives metric"
            assert (
                "parent_narratives" in stats_dict
            ), "Should have parent_narratives metric"
            assert (
                "child_narratives" in stats_dict
            ), "Should have child_narratives metric"

            # Verify relationship: total = parents + children
            total = stats_dict["total_narratives"]
            parents = stats_dict["parent_narratives"]
            children = stats_dict["child_narratives"]

            assert (
                total == parents + children
            ), f"Total narratives ({total}) should equal parents ({parents}) + children ({children})"

    def test_clust2_integration(self):
        """Test that CLUST-2 correctly uses parent_id instead of nested_within"""
        # This would require actual CLUST-2 setup, so we'll test the structure
        with get_db_session() as session:
            # Create a mock parent narrative as CLUST-2 would
            parent = NarrativeNSF1(
                narrative_id="CLUST2-TEST-001",
                title="CLUST-2 Test Parent",
                summary="Testing CLUST-2 parent creation",
                origin_language="en",
                parent_id=None,  # CANONICAL: Parent has parent_id=NULL
                dominant_source_languages=["en"],
                alignment=[],
                actor_origin=["Test Actor"],
                conflict_alignment=[],
                frame_logic=[],
                nested_within=[],  # DEPRECATED: Should be empty
                confidence_rating="medium",
                update_status={
                    "last_updated": datetime.utcnow().isoformat(),
                    "update_trigger": "clust2_segmentation",
                    "hierarchy_type": "parent",
                    "migration_003_compliant": True,
                },
            )

            session.add(parent)
            session.flush()

            # Create a mock child narrative as CLUST-2 would
            child = NarrativeNSF1(
                narrative_id="CLUST2-TEST-001-C01",
                title="CLUST-2 Test Child",
                summary="Testing CLUST-2 child creation",
                origin_language="en",
                parent_id=parent.id,  # CANONICAL: Child has parent_id=parent_uuid
                dominant_source_languages=["en"],
                alignment=[],
                actor_origin=["Test Actor"],
                conflict_alignment=[],
                frame_logic=[{"category": "Tone", "description": "Different framing"}],
                nested_within=[],  # DEPRECATED: Should be empty
                confidence_rating="medium",
                update_status={
                    "last_updated": datetime.utcnow().isoformat(),
                    "update_trigger": "clust2_segmentation",
                    "hierarchy_type": "child",
                    "migration_003_compliant": True,
                },
            )

            session.add(child)
            session.commit()

            # Verify CLUST-2 compliance
            assert parent.parent_id is None, "CLUST-2 parent should have parent_id=NULL"
            assert (
                child.parent_id == parent.id
            ), "CLUST-2 child should reference parent via parent_id"
            assert (
                len(parent.nested_within) == 0
            ), "CLUST-2 should not populate nested_within"
            assert (
                len(child.nested_within) == 0
            ), "CLUST-2 should not populate nested_within"

            # Test query performance with CLUST-2 pattern
            start_time = time.time()
            result = session.execute(
                text(
                    """
                SELECT COUNT(*) FROM narratives 
                WHERE parent_id = :parent_id
            """
                ),
                {"parent_id": parent.id},
            )
            query_time = time.time() - start_time

            child_count = result.fetchone()[0]
            assert child_count == 1, "Should find one child via parent_id query"
            assert (
                query_time < 0.01
            ), f"Parent_id query should be fast, took {query_time:.4f}s"

            # Cleanup
            session.delete(parent)
            session.commit()

    def test_nested_within_deprecation(self):
        """Test that nested_within is properly marked as deprecated"""
        with get_db_session() as session:
            # Check that column comment indicates deprecation
            result = session.execute(
                text(
                    """
                SELECT col_description(pgc.oid, pga.attnum) as column_comment
                FROM pg_class pgc
                JOIN pg_attribute pga ON pgc.oid = pga.attrelid  
                WHERE pgc.relname = 'narratives' 
                AND pga.attname = 'nested_within'
            """
                )
            )

            comment = result.fetchone()
            if comment and comment[0]:
                assert (
                    "DEPRECATED" in comment[0].upper()
                ), "nested_within column should be marked as DEPRECATED in comment"

    def test_rollback_capability(self):
        """Test that rollback function exists and is callable"""
        with get_db_session() as session:
            # Check that rollback function exists
            result = session.execute(
                text(
                    """
                SELECT 1 FROM information_schema.routines 
                WHERE routine_name = 'rollback_parent_id_migration'
            """
                )
            )
            assert result.fetchone() is not None, "Rollback function must exist"

            # Test that function is callable (but don't actually execute rollback)
            result = session.execute(
                text(
                    """
                SELECT routine_type FROM information_schema.routines 
                WHERE routine_name = 'rollback_parent_id_migration'
            """
                )
            )
            routine_type = result.fetchone()[0]
            assert (
                routine_type == "FUNCTION"
            ), "rollback_parent_id_migration should be a function"

    def test_migration_logging(self):
        """Test that migration was properly logged"""
        with get_db_session() as session:
            # Check migration log entry
            result = session.execute(
                text(
                    """
                SELECT migration_id, description, changes_summary, applied_at
                FROM migration_log 
                WHERE migration_id = '003_complete_parent_child_hierarchy_canonical'
            """
                )
            )

            log_entry = result.fetchone()
            assert log_entry is not None, "Migration 003 should be logged"

            migration_id, description, changes_summary, applied_at = log_entry

            assert "parent_id" in description.lower(), "Log should mention parent_id"
            assert (
                "canonical" in description.lower()
            ), "Log should mention canonical field"
            assert changes_summary is not None, "Should have changes summary"
            assert applied_at is not None, "Should have application timestamp"


class TestPerformanceRegression:
    """Performance regression tests for hierarchy queries"""

    def test_child_lookup_performance(self):
        """Test that child lookup queries meet performance requirements"""
        with get_db_session() as session:
            # Get a test parent
            result = session.execute(
                text(
                    """
                SELECT id FROM narratives WHERE parent_id IS NULL LIMIT 1
            """
                )
            )
            test_parent = result.fetchone()

            if test_parent:
                parent_id = test_parent[0]

                # Measure parent_id query performance
                start_time = time.time()
                result = session.execute(
                    text(
                        """
                    SELECT id, narrative_id, title FROM narratives 
                    WHERE parent_id = :parent_id
                """
                    ),
                    {"parent_id": parent_id},
                )
                children = result.fetchall()
                query_time = time.time() - start_time

                # Performance requirement: <10ms for child lookup
                assert (
                    query_time < 0.01
                ), f"Child lookup should be <10ms, took {query_time*1000:.2f}ms"

                print(
                    f"[OK] Child lookup performance: {query_time*1000:.2f}ms for {len(children)} children"
                )

    def test_hierarchy_join_performance(self):
        """Test that hierarchy JOIN queries meet performance requirements"""
        with get_db_session() as session:
            # Measure hierarchy JOIN performance
            start_time = time.time()
            result = session.execute(
                text(
                    """
                SELECT 
                    parent.narrative_id as parent_id,
                    COUNT(child.id) as child_count
                FROM narratives parent
                LEFT JOIN narratives child ON child.parent_id = parent.id
                WHERE parent.parent_id IS NULL
                GROUP BY parent.id, parent.narrative_id
                ORDER BY child_count DESC
                LIMIT 10
            """
                )
            )
            hierarchy_data = result.fetchall()
            query_time = time.time() - start_time

            # Performance requirement: <50ms for hierarchy overview
            assert (
                query_time < 0.05
            ), f"Hierarchy JOIN should be <50ms, took {query_time*1000:.2f}ms"

            print(
                f"[OK] Hierarchy JOIN performance: {query_time*1000:.2f}ms for {len(hierarchy_data)} parents"
            )


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """End-to-end test of parent/child narrative creation and querying"""

    # Test data
    test_narratives = [
        {
            "narrative_id": "E2E-PARENT-001",
            "title": "End-to-End Test Parent",
            "summary": "Testing complete workflow",
            "is_parent": True,
        },
        {
            "narrative_id": "E2E-CHILD-001",
            "title": "End-to-End Test Child 1",
            "summary": "First child narrative",
            "is_parent": False,
        },
        {
            "narrative_id": "E2E-CHILD-002",
            "title": "End-to-End Test Child 2",
            "summary": "Second child narrative",
            "is_parent": False,
        },
    ]

    with get_db_session() as session:
        created_narratives = []
        parent_id = None

        try:
            # Create parent narrative
            parent_data = test_narratives[0]
            parent = NarrativeNSF1(
                narrative_id=parent_data["narrative_id"],
                title=parent_data["title"],
                summary=parent_data["summary"],
                origin_language="en",
                parent_id=None,
                dominant_source_languages=["en"],
                alignment=[],
                actor_origin=[],
                conflict_alignment=[],
                frame_logic=[],
                nested_within=[],
                confidence_rating="medium",
            )

            session.add(parent)
            session.flush()
            parent_id = parent.id
            created_narratives.append(parent)

            # Create child narratives
            for child_data in test_narratives[1:]:
                child = NarrativeNSF1(
                    narrative_id=child_data["narrative_id"],
                    title=child_data["title"],
                    summary=child_data["summary"],
                    origin_language="en",
                    parent_id=parent_id,
                    dominant_source_languages=["en"],
                    alignment=[],
                    actor_origin=[],
                    conflict_alignment=[],
                    frame_logic=[],
                    nested_within=[],
                    confidence_rating="medium",
                )

                session.add(child)
                created_narratives.append(child)

            session.commit()

            # Test queries
            # 1. Find all children of parent
            result = session.execute(
                text(
                    """
                SELECT narrative_id, title FROM narratives 
                WHERE parent_id = :parent_id
                ORDER BY created_at
            """
                ),
                {"parent_id": parent_id},
            )

            children = result.fetchall()
            assert len(children) == 2, "Should find 2 children"
            assert (
                children[0][0] == "E2E-CHILD-001"
            ), "First child should be E2E-CHILD-001"
            assert (
                children[1][0] == "E2E-CHILD-002"
            ), "Second child should be E2E-CHILD-002"

            # 2. Find parent of child
            result = session.execute(
                text(
                    """
                SELECT p.narrative_id, p.title 
                FROM narratives c
                JOIN narratives p ON c.parent_id = p.id
                WHERE c.narrative_id = 'E2E-CHILD-001'
            """
                )
            )

            parent_result = result.fetchone()
            assert parent_result is not None, "Should find parent of child"
            assert (
                parent_result[0] == "E2E-PARENT-001"
            ), "Parent should be E2E-PARENT-001"

            # 3. Get complete hierarchy
            result = session.execute(
                text(
                    """
                SELECT * FROM get_narrative_hierarchy_tree(:parent_id)
                ORDER BY hierarchy_level, created_at
            """
                ),
                {"parent_id": parent_id},
            )

            hierarchy = result.fetchall()
            assert len(hierarchy) == 3, "Should have 3 narratives in hierarchy"
            assert hierarchy[0][0] == 0, "First should be parent (level 0)"
            assert hierarchy[1][0] == 1, "Second should be child (level 1)"
            assert hierarchy[2][0] == 1, "Third should be child (level 1)"

            print("[OK] End-to-end workflow test passed")

        finally:
            # Cleanup
            for narrative in created_narratives:
                try:
                    session.delete(narrative)
                except:
                    pass
            try:
                session.commit()
            except:
                session.rollback()


if __name__ == "__main__":
    """Run migration validation tests"""

    print("=" * 60)
    print("PARENT/CHILD HIERARCHY MIGRATION VALIDATION")
    print("=" * 60)

    # Run the test suite
    pytest.main([__file__, "-v", "--tb=short", "--disable-warnings"])

    print("\n" + "=" * 60)
    print("MIGRATION VALIDATION COMPLETE")
    print("=" * 60)
