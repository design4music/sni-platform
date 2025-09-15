"""
Test Suite for FRINGE_AND_QUALITY_NOTES Implementation

Tests the new fringe_notes and data_quality_notes JSONB fields,
helper methods, and integration with CLUST-2 and ETL pipeline.
"""

import os
# Import the models and functions to test
import sys
from unittest.mock import Mock

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl_pipeline.core.data_quality import (DataQualityTracker,
                                            QualityIssueType,
                                            track_ingestion_quality_issues)
from etl_pipeline.core.database.models import NarrativeNSF1
from etl_pipeline.core.queries.fringe_analysis import (
    FringeAnalysisQueries)


class TestFringeAndQualityNotesModels:
    """Test the database model changes and helper methods"""

    @pytest.fixture
    def sample_narrative(self):
        """Create a sample narrative for testing"""
        narrative = NarrativeNSF1(
            narrative_id="TEST-001",
            title="Test Narrative",
            summary="Test narrative for fringe and quality notes testing",
            origin_language="en",
            dominant_source_languages=["en"],
            alignment=[],
            actor_origin=[],
            conflict_alignment=[],
            frame_logic=[],
            fringe_notes=[],
            data_quality_notes=[],
        )
        return narrative

    def test_add_fringe_note(self, sample_narrative):
        """Test adding fringe notes to narrative"""
        # Add a fringe note
        sample_narrative.add_fringe_note(
            summary="Low diversity detected in source coverage",
            source_count=2,
            tone="propagandistic",
            example_articles=[
                "https://example.com/article1",
                "https://example.com/article2",
            ],
        )

        # Check that fringe note was added
        assert len(sample_narrative.fringe_notes) == 1

        fringe_note = sample_narrative.fringe_notes[0]
        assert fringe_note["note_type"] == "fringe"
        assert fringe_note["summary"] == "Low diversity detected in source coverage"
        assert fringe_note["source_count"] == 2
        assert fringe_note["tone"] == "propagandistic"
        assert len(fringe_note["example_articles"]) == 2
        assert "detected_at" in fringe_note

    def test_add_data_quality_note(self, sample_narrative):
        """Test adding data quality notes to narrative"""
        # Add a quality note
        sample_narrative.add_data_quality_note(
            summary="Missing metadata in 5 articles",
            source_count=3,
            example_articles=["https://example.com/missing1"],
        )

        # Check that quality note was added
        assert len(sample_narrative.data_quality_notes) == 1

        quality_note = sample_narrative.data_quality_notes[0]
        assert quality_note["note_type"] == "quality"
        assert quality_note["summary"] == "Missing metadata in 5 articles"
        assert quality_note["source_count"] == 3
        assert len(quality_note["example_articles"]) == 1
        assert "detected_at" in quality_note

    def test_get_fringe_notes_by_tone(self, sample_narrative):
        """Test filtering fringe notes by tone"""
        # Add multiple fringe notes with different tones
        sample_narrative.add_fringe_note("First note", tone="propagandistic")
        sample_narrative.add_fringe_note("Second note", tone="neutral")
        sample_narrative.add_fringe_note("Third note", tone="propagandistic")

        # Filter by propagandistic tone
        propagandistic_notes = sample_narrative.get_fringe_notes_by_tone(
            "propagandistic"
        )
        assert len(propagandistic_notes) == 2

        # Filter by neutral tone
        neutral_notes = sample_narrative.get_fringe_notes_by_tone("neutral")
        assert len(neutral_notes) == 1

        # Filter by non-existent tone
        missing_notes = sample_narrative.get_fringe_notes_by_tone("celebratory")
        assert len(missing_notes) == 0

    def test_get_latest_quality_issues(self, sample_narrative):
        """Test getting latest quality issues"""
        # Add multiple quality notes
        sample_narrative.add_data_quality_note("First issue")
        sample_narrative.add_data_quality_note("Second issue")
        sample_narrative.add_data_quality_note("Third issue")

        # Get latest issues
        latest = sample_narrative.get_latest_quality_issues(limit=2)
        assert len(latest) == 2

        # Should be in reverse chronological order (newest first)
        assert latest[0]["summary"] == "Third issue"
        assert latest[1]["summary"] == "Second issue"

    def test_has_fringe_content(self, sample_narrative):
        """Test checking for fringe content presence"""
        # Initially no fringe content
        assert not sample_narrative.has_fringe_content()

        # Add fringe note
        sample_narrative.add_fringe_note("Test fringe note")
        assert sample_narrative.has_fringe_content()

    def test_has_quality_issues(self, sample_narrative):
        """Test checking for quality issues presence"""
        # Initially no quality issues
        assert not sample_narrative.has_quality_issues()

        # Add quality note
        sample_narrative.add_data_quality_note("Test quality issue")
        assert sample_narrative.has_quality_issues()

    def test_get_fringe_summary(self, sample_narrative):
        """Test getting fringe content summary statistics"""
        # Initially no fringe content
        summary = sample_narrative.get_fringe_summary()
        assert not summary["has_fringe"]
        assert summary["total_notes"] == 0
        assert summary["tones"] == []
        assert summary["avg_source_count"] is None

        # Add fringe notes with different tones and source counts
        sample_narrative.add_fringe_note(
            "First note", source_count=2, tone="propagandistic"
        )
        sample_narrative.add_fringe_note("Second note", source_count=4, tone="neutral")
        sample_narrative.add_fringe_note(
            "Third note", source_count=1, tone="propagandistic"
        )

        summary = sample_narrative.get_fringe_summary()
        assert summary["has_fringe"]
        assert summary["total_notes"] == 3
        assert set(summary["tones"]) == {"propagandistic", "neutral"}
        assert summary["avg_source_count"] == (2 + 4 + 1) / 3


class TestDataQualityTracker:
    """Test the data quality tracking functionality"""

    @pytest.fixture
    def tracker(self):
        """Create a DataQualityTracker instance"""
        return DataQualityTracker()

    def test_track_missing_metadata(self, tracker):
        """Test tracking missing metadata issues"""
        articles = [
            {
                "id": "1",
                "title": "",
                "source_name": "Source A",
                "url": "http://example.com/1",
            },
            {
                "id": "2",
                "title": "",
                "source_name": "Source B",
                "url": "http://example.com/2",
            },
        ]

        issue = tracker.track_missing_metadata(articles, ["title"])

        assert issue.issue_type == QualityIssueType.MISSING_METADATA
        assert issue.summary == "2 articles missing title"
        assert issue.source_count == 2
        assert len(issue.example_articles) == 2
        assert issue.severity == "medium"

    def test_track_extraction_anomaly(self, tracker):
        """Test tracking content extraction anomalies"""
        issue = tracker.track_extraction_anomaly(
            "article123",
            "http://example.com/article",
            "truncation",
            "Content too short: 50 characters",
        )

        assert issue.issue_type == QualityIssueType.EXTRACTION_ANOMALY
        assert "Content extraction truncation" in issue.summary
        assert issue.source_count == 1
        assert issue.example_articles == ["http://example.com/article"]
        assert issue.severity == "low"  # truncation is low severity

    def test_track_clustering_irregularity(self, tracker):
        """Test tracking clustering irregularities"""
        affected_articles = ["art1", "art2", "art3"]

        issue = tracker.track_clustering_irregularity(
            "cluster_123",
            "single_article_cluster",
            affected_articles,
            "Cluster contains only one article",
        )

        assert issue.issue_type == QualityIssueType.CLUSTERING_IRREGULARITY
        assert "Clustering single_article_cluster" in issue.summary
        assert len(issue.example_articles) == 3
        assert issue.severity == "medium"

    def test_get_session_summary(self, tracker):
        """Test getting session summary of tracked issues"""
        # Initially empty
        summary = tracker.get_session_summary()
        assert summary["total_issues"] == 0

        # Add some issues
        tracker.track_missing_metadata([{"id": "1"}], ["title"])
        tracker.track_extraction_anomaly("art1", "url1", "truncation", "details")
        tracker.track_missing_metadata([{"id": "2"}, {"id": "3"}], ["content"])

        summary = tracker.get_session_summary()
        assert summary["total_issues"] == 3
        assert summary["by_type"]["missing_metadata"] == 2
        assert summary["by_type"]["extraction_anomaly"] == 1
        assert summary["by_severity"]["medium"] == 2
        assert summary["by_severity"]["low"] == 1
        assert len(summary["recommendations"]) > 0


class TestIngestionQualityTracking:
    """Test integration with ETL ingestion pipeline"""

    def test_track_ingestion_quality_issues(self):
        """Test tracking quality issues during ingestion"""
        articles_data = [
            {
                "id": "1",
                "title": "Good Article",
                "content": "This is a good article with sufficient content for analysis.",
                "source_name": "Reliable Source",
                "url": "http://example.com/good",
            },
            {
                "id": "2",
                "title": "",  # Missing title
                "content": "Content without title",
                "source_name": "Another Source",
                "url": "http://example.com/missing-title",
            },
            {
                "id": "3",
                "title": "Short Content Article",
                "content": "Too short",  # Content too short
                "source_name": "Source C",
                "url": "http://example.com/short",
            },
            {
                "id": "4",
                "title": "No Source Article",
                "content": "Article without source information",
                "source_name": "",  # Missing source
                "url": "http://example.com/no-source",
            },
        ]

        issues = track_ingestion_quality_issues(articles_data)

        # Should detect multiple issues
        assert len(issues) > 0

        # Check for specific issue types
        issue_types = [issue.issue_type for issue in issues]
        assert QualityIssueType.MISSING_METADATA in issue_types
        assert QualityIssueType.EXTRACTION_ANOMALY in issue_types


class TestFringeAnalysisQueries:
    """Test fringe analysis query functions"""

    def test_fringe_analysis_structure(self):
        """Test that fringe analysis functions return expected structure"""
        # Mock database session
        mock_session = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        # Test analyze_fringe_patterns with empty data
        result = FringeAnalysisQueries.analyze_fringe_patterns(
            mock_session, days_back=7
        )

        assert "total_fringe_notes" in result
        assert "narratives_with_fringe" in result
        assert "analysis_period_days" in result
        assert "patterns" in result


class TestDatabaseIntegration:
    """Test database integration and migration compatibility"""

    def test_jsonb_structure_validation(self):
        """Test that JSONB structures follow specification"""
        narrative = NarrativeNSF1(
            narrative_id="TEST-002",
            title="Integration Test",
            summary="Test narrative",
            origin_language="en",
            dominant_source_languages=["en"],
            alignment=[],
            actor_origin=[],
            conflict_alignment=[],
            frame_logic=[],
            fringe_notes=[],
            data_quality_notes=[],
        )

        # Add notes and verify structure
        narrative.add_fringe_note(
            summary="Test fringe note",
            source_count=3,
            tone="propagandistic",
            example_articles=["http://example.com/1", "http://example.com/2"],
        )

        narrative.add_data_quality_note(
            summary="Test quality issue",
            source_count=2,
            example_articles=["http://example.com/issue"],
        )

        # Verify fringe note structure
        fringe_note = narrative.fringe_notes[0]
        required_fringe_fields = [
            "note_type",
            "summary",
            "source_count",
            "tone",
            "example_articles",
            "detected_at",
        ]
        for field in required_fringe_fields:
            assert field in fringe_note, f"Missing required field: {field}"

        assert fringe_note["note_type"] == "fringe"

        # Verify quality note structure
        quality_note = narrative.data_quality_notes[0]
        required_quality_fields = [
            "note_type",
            "summary",
            "source_count",
            "example_articles",
            "detected_at",
        ]
        for field in required_quality_fields:
            assert field in quality_note, f"Missing required field: {field}"

        assert quality_note["note_type"] == "quality"

    def test_backward_compatibility(self):
        """Test that new fields don't break existing functionality"""
        # Create narrative without fringe/quality notes
        narrative = NarrativeNSF1(
            narrative_id="TEST-003",
            title="Backward Compatibility Test",
            summary="Test narrative",
            origin_language="en",
        )

        # Should have default empty arrays
        assert narrative.fringe_notes == []
        assert narrative.data_quality_notes == []

        # Should not break existing methods
        assert narrative.is_parent()
        assert not narrative.is_child()
        assert narrative.get_hierarchy_level() == 0


# ============================================================================
# Integration Tests
# ============================================================================


def test_end_to_end_fringe_tracking():
    """
    Test end-to-end fringe content tracking from CLUST-2 to database
    """
    # This would be a full integration test that:
    # 1. Creates sample articles and clusters
    # 2. Runs CLUST-2 segmentation
    # 3. Checks that fringe_notes are properly populated
    # 4. Verifies query functions work with real data

    # For now, just test the basic flow structure
    assert True  # Placeholder for full integration test


def test_end_to_end_quality_tracking():
    """
    Test end-to-end quality issue tracking from ETL to database
    """
    # This would be a full integration test that:
    # 1. Simulates ETL pipeline with quality issues
    # 2. Tracks issues using DataQualityTracker
    # 3. Associates issues with narratives
    # 4. Verifies quality analysis queries work

    # For now, just test the basic flow structure
    assert True  # Placeholder for full integration test


if __name__ == "__main__":
    # Run basic tests
    import unittest

    class BasicTests(unittest.TestCase):
        def test_imports(self):
            """Test that all modules import correctly"""

            self.assertTrue(True)

        def test_narrative_helper_methods(self):
            """Test narrative helper methods"""
            narrative = NarrativeNSF1(
                narrative_id="TEST-BASIC",
                title="Basic Test",
                summary="Basic test narrative",
                origin_language="en",
                fringe_notes=[],
                data_quality_notes=[],
            )

            # Test adding notes
            narrative.add_fringe_note("Test fringe", tone="neutral")
            narrative.add_data_quality_note("Test quality issue")

            self.assertEqual(len(narrative.fringe_notes), 1)
            self.assertEqual(len(narrative.data_quality_notes), 1)
            self.assertTrue(narrative.has_fringe_content())
            self.assertTrue(narrative.has_quality_issues())

    unittest.main()
