"""
MAP/REDUCE Event Family Processor
Alternative implementation using parallel MAP/REDUCE approach for improved performance
"""

import asyncio
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from loguru import logger

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.generate.database import get_gen1_database
from apps.generate.map_classifier import MapClassifier
from apps.generate.mapreduce_models import (EFGroup, MapReduceResult,
                                            TitleClassification)
from apps.generate.models import EventFamily
from apps.generate.reduce_assembler import ReduceAssembler
from core.config import get_config


class MapReduceProcessor:
    """
    MAP/REDUCE Event Family processor

    Alternative to MultiPassProcessor with parallel processing:
    1. MAP: Classify titles -> (theater, event_type) in parallel
    2. GROUP: Group by (theater, event_type) - code only
    3. REDUCE: Generate EF content per group in parallel
    4. UPSERT: Merge with existing EFs by ef_key
    """

    def __init__(self):
        self.config = get_config()
        self.db = get_gen1_database()
        self.mapper = MapClassifier(self.config)
        self.reducer = ReduceAssembler(self.config)

    async def run_pass1_mapreduce(
        self, max_titles: Optional[int] = None
    ) -> MapReduceResult:
        """
        Run MAP/REDUCE Pass 1: Parallel title classification and EF assembly

        Args:
            max_titles: Maximum number of titles to process

        Returns:
            MapReduceResult with processing statistics and results
        """
        start_time = time.time()
        logger.info("=== MAP/REDUCE PASS 1: Parallel EF Assembly ===")

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
                    "extracted_actors": title.get(
                        "entities"
                    ),  # Include entities data for key_actors extraction
                }
                for title in titles
            ]

            # Step 2: MAP Phase - Parallel classification
            logger.info("Starting MAP phase: parallel title classification...")
            map_start = time.time()

            classifications = await self.mapper.process_titles_parallel(title_data)
            map_duration = time.time() - map_start

            if not classifications:
                logger.error("MAP phase produced no classifications")
                return self._create_empty_result()

            logger.info(
                f"MAP phase completed: {len(classifications)} classifications in {map_duration:.1f}s"
            )

            # Step 3: GROUP Phase - Group by (theater, event_type)
            logger.info("Starting GROUP phase: grouping by theater + event_type...")
            group_start = time.time()

            ef_groups = self._group_classifications(classifications, title_data)
            group_duration = time.time() - group_start

            logger.info(
                f"GROUP phase completed: {len(ef_groups)} EF groups in {group_duration:.1f}s"
            )

            # Step 4: REDUCE Phase - Parallel EF generation
            logger.info("Starting REDUCE phase: parallel EF generation...")
            reduce_start = time.time()

            event_families = await self.reducer.process_groups_parallel(ef_groups)
            reduce_duration = time.time() - reduce_start

            logger.info(
                f"REDUCE phase completed: {len(event_families)} Event Families in {reduce_duration:.1f}s"
            )

            # Step 5: Database upsert
            logger.info("Upserting Event Families to database...")
            upsert_results = await self._upsert_event_families(event_families)

            # Calculate final results
            total_duration = time.time() - start_time
            classification_success_rate = (
                len(classifications) / len(title_data) if title_data else 0
            )
            reduce_success_rate = (
                len(event_families) / len(ef_groups) if ef_groups else 0
            )

            result = MapReduceResult(
                total_titles_processed=len(title_data),
                map_batches_processed=len(title_data) // self.config.map_batch_size
                + (1 if len(title_data) % self.config.map_batch_size else 0),
                ef_groups_created=len(ef_groups),
                map_phase_seconds=map_duration,
                group_phase_seconds=group_duration,
                reduce_phase_seconds=reduce_duration,
                total_seconds=total_duration,
                event_families_created=upsert_results.get("created", 0),
                event_families_merged=upsert_results.get("merged", 0),
                titles_assigned=upsert_results.get("titles_assigned", 0),
                classification_success_rate=classification_success_rate,
                reduce_success_rate=reduce_success_rate,
            )

            logger.info(f"MAP/REDUCE Pass 1 completed: {result.summary}")
            return result

        except Exception as e:
            logger.error(f"MAP/REDUCE Pass 1 failed: {e}")
            raise

    def _group_classifications(
        self,
        classifications: List[TitleClassification],
        title_data: List[Dict[str, Any]],
    ) -> List[EFGroup]:
        """
        Group classifications by (theater, event_type)

        Args:
            classifications: Results from MAP phase
            title_data: Original title data with metadata

        Returns:
            List of EFGroup objects ready for REDUCE phase
        """
        # Create lookup for title data
        title_lookup = {title["id"]: title for title in title_data}

        # Group by (theater, event_type)
        groups = defaultdict(list)
        for classification in classifications:
            key = (classification.primary_theater, classification.event_type)

            # Get original title data
            title_info = title_lookup.get(classification.id)
            if title_info:
                groups[key].append(
                    {"classification": classification, "title_data": title_info}
                )

        # Convert to EFGroup objects
        ef_groups = []
        for (theater, event_type), group_items in groups.items():
            # Extract data
            title_ids = [item["classification"].id for item in group_items]
            titles = [
                {"id": item["title_data"]["id"], "title": item["title_data"]["title"]}
                for item in group_items
            ]

            # Extract and combine key_actors from all titles
            all_actors = set()
            for item in group_items:
                # Database query renames 'entities' to 'extracted_actors'
                title_entities = item["title_data"].get("extracted_actors") or {}

                if isinstance(title_entities, dict):
                    # Extract actors from the dictionary structure
                    actors_list = title_entities.get("actors", [])
                    if isinstance(actors_list, list):
                        all_actors.update(actors_list)
                elif isinstance(title_entities, list):
                    # Fallback: handle direct list format
                    all_actors.update(title_entities)
                elif isinstance(title_entities, str):
                    # Fallback: handle comma-separated string
                    all_actors.update(
                        [
                            actor.strip()
                            for actor in title_entities.split(",")
                            if actor.strip()
                        ]
                    )

            key_actors = sorted(list(all_actors))  # Sort for consistency

            # Calculate temporal scope
            dates = []
            for item in group_items:
                pubdate = item["title_data"].get("pubdate_utc")
                if pubdate:
                    if isinstance(pubdate, str):
                        # Parse if string
                        try:
                            dates.append(
                                datetime.fromisoformat(pubdate.replace("Z", "+00:00"))
                            )
                        except:
                            pass
                    elif isinstance(pubdate, datetime):
                        dates.append(pubdate)

            if dates:
                temporal_start = min(dates)
                temporal_end = max(dates)
            else:
                # Fallback to current time
                temporal_start = temporal_end = datetime.utcnow()

            ef_group = EFGroup(
                primary_theater=theater,
                event_type=event_type,
                title_ids=title_ids,
                titles=titles,
                key_actors=key_actors,
                temporal_scope_start=temporal_start,
                temporal_scope_end=temporal_end,
            )

            ef_groups.append(ef_group)

        logger.debug(
            f"Grouped {len(classifications)} classifications into {len(ef_groups)} EF groups"
        )
        return ef_groups

    async def _upsert_event_families(
        self, event_families: List[EventFamily]
    ) -> Dict[str, Any]:
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
                    confidence=ef.confidence_score,
                    reason="MAP/REDUCE pipeline processing",
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
    """Create Typer CLI app for MAP/REDUCE processor"""
    app = typer.Typer(help="MAP/REDUCE Event Family Processor")

    @app.command()
    def run_mapreduce(
        max_titles: int = typer.Argument(
            1000, help="Maximum number of titles to process"
        ),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Dry run mode (no database writes)"
        ),
        background: bool = typer.Option(
            False, "--background", help="Run in background with longer timeouts"
        ),
    ):
        """Run MAP/REDUCE Event Family processing"""

        async def main():
            try:
                # Check if MAP/REDUCE is enabled
                config = get_config()
                if not getattr(
                    config, "mapreduce_enabled", True
                ):  # Default to True for testing
                    logger.warning("MAP/REDUCE processing may be disabled in config")

                processor = MapReduceProcessor()

                if background:
                    logger.info(
                        f"BACKGROUND MODE: Processing {max_titles} titles with extended timeouts"
                    )
                    # For background mode, increase timeouts
                    processor.config.map_timeout_seconds = 300  # 5 minutes
                    processor.config.reduce_timeout_seconds = 180  # 3 minutes

                if dry_run:
                    logger.info("DRY RUN MODE: No database writes will be performed")
                    # TODO: Implement dry run logic
                    return

                result = await processor.run_pass1_mapreduce(max_titles)

                logger.info("=== MAP/REDUCE RESULTS ===")
                logger.info(f"Total processing time: {result.total_seconds:.1f}s")
                logger.info(f"  MAP phase: {result.map_phase_seconds:.1f}s")
                logger.info(f"  GROUP phase: {result.group_phase_seconds:.1f}s")
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
                logger.error(f"MAP/REDUCE processing failed: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    return app


if __name__ == "__main__":
    app = create_cli_app()
    app()
