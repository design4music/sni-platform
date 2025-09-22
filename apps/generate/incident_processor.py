"""
Incident-Based MAP/REDUCE Event Family Processor
New implementation using semantic incident clustering first, then analysis
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.generate.database import get_gen1_database  # noqa: E402
from apps.generate.map_classifier import MapClassifier  # noqa: E402
from apps.generate.mapreduce_models import MapReduceResult  # noqa: E402
from apps.generate.models import EventFamily  # noqa: E402
from apps.generate.reduce_assembler import ReduceAssembler  # noqa: E402
from core.config import get_config  # noqa: E402


class IncidentProcessor:
    """
    Incident-based MAP/REDUCE Event Family processor

    New architecture:
    1. MAP: Cluster titles into strategic incidents
    2. REDUCE: Analyze each incident -> (theater, event_type) + EF content
    3. UPSERT: Merge with existing EFs by ef_key
    """

    def __init__(self):
        self.config = get_config()
        self.db = get_gen1_database()
        self.mapper = MapClassifier(self.config)
        self.reducer = ReduceAssembler(self.config)

    async def run_incident_processing(
        self, max_titles: Optional[int] = None
    ) -> MapReduceResult:
        """
        Run incident-based processing: Cluster incidents first, then analyze

        Args:
            max_titles: Maximum number of titles to process

        Returns:
            MapReduceResult with processing statistics and results
        """
        start_time = time.time()
        logger.info("=== INCIDENT-BASED MAP/REDUCE: Semantic Clustering First ===")

        try:
            # Step 1: Get unassigned titles
            logger.info("Fetching unassigned strategic titles...")
            titles = self.db.get_unassigned_strategic_titles(limit=max_titles)

            if not titles:
                logger.warning("No unassigned strategic titles found")
                return self._create_empty_result()

            logger.info(f"Found {len(titles)} unassigned strategic titles")

            # Convert to format expected by MAP phase
            title_data = [
                {
                    "id": str(title["id"]),
                    "title": title["text"],
                    "pubdate_utc": title.get("pubdate_utc"),
                    "extracted_actors": title.get("entities"),
                }
                for title in titles
            ]

            # Step 2: MAP Phase - Incident clustering
            logger.info("Starting MAP phase: semantic incident clustering...")
            map_start = time.time()

            incident_clusters = await self.mapper.process_incidents_parallel(title_data)
            map_duration = time.time() - map_start

            if not incident_clusters:
                logger.error("MAP phase produced no incident clusters")
                return self._create_empty_result()

            logger.info(
                f"MAP phase completed: {len(incident_clusters)} incident clusters in {map_duration:.1f}s"
            )

            # Log incident clusters for debugging
            for i, cluster in enumerate(incident_clusters):
                logger.info(
                    f"  Incident {i+1}: '{cluster.incident_name}' ({len(cluster.title_ids)} titles)"
                )

            # Step 3: REDUCE Phase - Incident analysis
            logger.info("Starting REDUCE phase: incident analysis...")
            reduce_start = time.time()

            event_families = await self.reducer.process_incidents_parallel(
                incident_clusters, title_data
            )

            # Step 3.5: Handle orphaned titles (single-title EFs)
            clustered_title_ids = set()
            for cluster in incident_clusters:
                clustered_title_ids.update(cluster.title_ids)

            orphaned_titles = [
                t for t in title_data if t["id"] not in clustered_title_ids
            ]

            if orphaned_titles:
                logger.info(
                    f"Processing {len(orphaned_titles)} orphaned titles as single-title EFs..."
                )

                # Create single-title clusters for orphaned titles
                single_title_clusters = []
                for title in orphaned_titles:
                    from apps.generate.mapreduce_models import IncidentCluster

                    single_cluster = IncidentCluster(
                        incident_name=f"Strategic Event: {title['title'][:50]}...",
                        title_ids=[title["id"]],
                        rationale="Single strategic title without incident siblings in this batch",
                    )
                    single_title_clusters.append(single_cluster)

                # Process single-title clusters through same REDUCE logic
                single_title_efs = await self.reducer.process_incidents_parallel(
                    single_title_clusters, title_data
                )
                event_families.extend(single_title_efs)

                logger.info(
                    f"Generated {len(single_title_efs)} single-title EFs from orphaned titles"
                )

            reduce_duration = time.time() - reduce_start

            logger.info(
                f"REDUCE phase completed: {len(event_families)} Event Families in {reduce_duration:.1f}s"
            )

            # Step 4: Database upsert
            logger.info("Upserting Event Families to database...")
            upsert_results = await self._upsert_event_families(event_families)

            # Calculate final results
            total_duration = time.time() - start_time
            clustering_success_rate = (
                len(incident_clusters)
                / (len(title_data) // self.config.map_batch_size + 1)
                if title_data
                else 0
            )
            reduce_success_rate = (
                len(event_families) / len(incident_clusters) if incident_clusters else 0
            )

            result = MapReduceResult(
                total_titles_processed=len(title_data),
                map_batches_processed=len(title_data) // self.config.map_batch_size
                + (1 if len(title_data) % self.config.map_batch_size else 0),
                ef_groups_created=len(incident_clusters),
                map_phase_seconds=map_duration,
                group_phase_seconds=0.0,  # No grouping phase in incident approach
                reduce_phase_seconds=reduce_duration,
                total_seconds=total_duration,
                event_families_created=upsert_results.get("created", 0),
                event_families_merged=upsert_results.get("merged", 0),
                titles_assigned=upsert_results.get("titles_assigned", 0),
                classification_success_rate=clustering_success_rate,
                reduce_success_rate=reduce_success_rate,
            )

            logger.info(f"Incident-based processing completed: {result.summary}")
            return result

        except Exception as e:
            logger.error(f"Incident-based processing failed: {e}")
            raise

    async def _upsert_event_families(self, event_families: List[EventFamily]) -> dict:
        """
        Upsert Event Families to database using existing ef_key logic

        Args:
            event_families: EventFamily objects to upsert

        Returns:
            Dictionary with upsert statistics
        """
        created_count = 0
        merged_count = 0
        titles_assigned = 0

        for ef in event_families:
            try:
                # Use existing database upsert logic
                success, existing_ef_id = await self.db.upsert_event_family_by_ef_key(
                    ef
                )

                if existing_ef_id:
                    # Existing EF was updated (merged)
                    merged_count += 1
                    logger.debug(f"Merged EF with ef_key {ef.ef_key}: {ef.title}")
                else:
                    # New EF was created
                    created_count += 1
                    logger.debug(f"Created new EF: {ef.title}")

                # Assign titles to the Event Family
                final_ef_id = existing_ef_id if existing_ef_id else ef.id
                assigned = await self.db.assign_titles_to_event_family(
                    title_ids=ef.source_title_ids,
                    event_family_id=final_ef_id,
                    confidence=ef.confidence_score
                    or 0.85,  # Use EF confidence or default
                    reason="Incident-based MAP/REDUCE pipeline processing",
                )
                titles_assigned += assigned

            except Exception as e:
                logger.error(f"Failed to upsert Event Family '{ef.title}': {e}")
                continue

        logger.info(
            f"Upsert results: {created_count} created, {merged_count} merged, {titles_assigned} titles assigned"
        )

        return {
            "created": created_count,
            "merged": merged_count,
            "titles_assigned": titles_assigned,
        }

    def _create_empty_result(self) -> MapReduceResult:
        """Create empty result for error cases"""
        return MapReduceResult(
            total_titles_processed=0,
            map_batches_processed=0,
            ef_groups_created=0,
            map_phase_seconds=0.0,
            group_phase_seconds=0.0,
            reduce_phase_seconds=0.0,
            total_seconds=0.0,
            event_families_created=0,
            event_families_merged=0,
            titles_assigned=0,
            classification_success_rate=0.0,
            reduce_success_rate=0.0,
        )


# CLI Interface
def create_cli_app():
    """Create Typer CLI app for incident processor"""
    app = typer.Typer(help="Incident-Based MAP/REDUCE Event Family Processor")

    @app.command()
    def run_incident_processing(
        max_titles: int = typer.Argument(
            50, help="Maximum number of titles to process"
        ),
        background: bool = typer.Option(
            False, "--background", help="Run in background with longer timeouts"
        ),
    ):
        """Run incident-based Event Family processing"""

        async def main():
            try:
                processor = IncidentProcessor()

                if background:
                    logger.info(
                        f"BACKGROUND MODE: Processing {max_titles} titles with extended timeouts"
                    )
                    # For background mode, increase timeouts
                    processor.config.map_timeout_seconds = 300  # 5 minutes
                    processor.config.reduce_timeout_seconds = 180  # 3 minutes

                result = await processor.run_incident_processing(max_titles)

                logger.info("=== INCIDENT PROCESSING RESULTS ===")
                logger.info(f"Total processing time: {result.total_seconds:.1f}s")
                logger.info(f"  MAP phase: {result.map_phase_seconds:.1f}s")
                logger.info(f"  REDUCE phase: {result.reduce_phase_seconds:.1f}s")
                logger.info(
                    f"Event Families: {result.event_families_created} created, {result.event_families_merged} merged"
                )
                logger.info(f"Titles assigned: {result.titles_assigned}")
                logger.info(
                    f"Success rates: MAP {result.classification_success_rate:.1%}, REDUCE {result.reduce_success_rate:.1%}"
                )

                if result.map_errors:
                    logger.warning(f"MAP errors: {len(result.map_errors)}")
                if result.reduce_errors:
                    logger.warning(f"REDUCE errors: {len(result.reduce_errors)}")

            except Exception as e:
                logger.error(f"Incident processing failed: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    return app


if __name__ == "__main__":
    app = create_cli_app()
    app()
