"""
CLUST-2 Workflow
Strategic Narrative Intelligence ETL Pipeline

Separate workflow for CLUST-2 interpretive narrative segmentation.
This runs after CLUST-1 and creates parent/child narrative hierarchies.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from ..core.config import get_config
from .clust1_thematic_grouping import ClusteringResult
from .clust2_segment_narratives import (CLUST2NarrativeSegmentation,
                                        SegmentationResult)

logger = structlog.get_logger(__name__)


@dataclass
class CLUST2WorkflowResult:
    """Result of CLUST-2 workflow"""

    parent_narratives_created: int
    child_narratives_created: int
    clusters_processed: int
    processing_duration_seconds: float
    segmentation_results: List[SegmentationResult]


class CLUST2Workflow:
    """
    Workflow for running CLUST-2 interpretive narrative segmentation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)

        # Initialize CLUST-2 system
        self.clust2_config = self.config.get("clust2", {})
        self.clust2_system = CLUST2NarrativeSegmentation(self.clust2_config)

        self.logger.info("CLUST-2 Workflow initialized")

    async def process_clusters(
        self, clusters: List[ClusteringResult]
    ) -> CLUST2WorkflowResult:
        """
        Process CLUST-1 clusters through CLUST-2 segmentation

        Args:
            clusters: Results from CLUST-1 thematic grouping

        Returns:
            CLUST-2 workflow results
        """
        start_time = datetime.utcnow()

        try:
            self.logger.info("Starting CLUST-2 workflow", cluster_count=len(clusters))

            if not clusters:
                return CLUST2WorkflowResult(
                    parent_narratives_created=0,
                    child_narratives_created=0,
                    clusters_processed=0,
                    processing_duration_seconds=0.0,
                    segmentation_results=[],
                )

            # Run CLUST-2 segmentation
            segmentation_results = await self.clust2_system.process_clusters(clusters)

            # Calculate results
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            parent_count = len(segmentation_results)
            child_count = sum(
                len(result.parent_narrative.children) for result in segmentation_results
            )

            result = CLUST2WorkflowResult(
                parent_narratives_created=parent_count,
                child_narratives_created=child_count,
                clusters_processed=len(segmentation_results),
                processing_duration_seconds=duration,
                segmentation_results=segmentation_results,
            )

            self.logger.info(
                "CLUST-2 workflow completed",
                parent_narratives=result.parent_narratives_created,
                child_narratives=result.child_narratives_created,
                duration_seconds=result.processing_duration_seconds,
            )

            return result

        except Exception as exc:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(
                "CLUST-2 workflow failed",
                duration_seconds=duration,
                error=str(exc),
                exc_info=True,
            )
            raise


# Convenience function
async def run_clust2_workflow(clusters: List[ClusteringResult]) -> CLUST2WorkflowResult:
    """Run CLUST-2 workflow on clusters"""
    config = get_config()
    clust2_config = getattr(config, "clustering", {})

    workflow = CLUST2Workflow(clust2_config)
    return await workflow.process_clusters(clusters)


if __name__ == "__main__":
    # CLI interface for testing
    import argparse

    parser = argparse.ArgumentParser(
        description="Run CLUST-2 workflow on existing clusters"
    )
    parser.add_argument(
        "--cluster-ids", nargs="+", help="Specific cluster IDs to process"
    )

    args = parser.parse_args()

    async def main():
        # This would need to load clusters from database by ID
        # For now, just show usage
        print("CLUST-2 Workflow")
        print(
            "Usage: python -m etl_pipeline.clustering.clust2_workflow --cluster-ids CLUST1_20241202_001"
        )

    asyncio.run(main())
