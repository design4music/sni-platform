"""
EF Enrichment CLI
Command-line interface for lean Event Family enrichment
"""

import asyncio
import sys
from pathlib import Path

import typer
from loguru import logger

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.enrich.processor import EFEnrichmentProcessor  # noqa: E402
from core.checkpoint import get_checkpoint_manager  # noqa: E402


def create_enrichment_cli() -> typer.Typer:
    """Create Typer CLI app for EF enrichment"""
    app = typer.Typer(
        help="Event Family Enrichment - Lean Strategic Context Enhancement"
    )

    @app.command()
    def enrich_queue(
        max_items: int = typer.Argument(
            10, help="Maximum number of EFs to enrich from queue"
        ),
        daily_cap: bool = typer.Option(
            False, "--daily-cap", help="Use daily cap limit instead of max_items"
        ),
        batch: int = typer.Option(
            None, "--batch", help="Process items in batches of this size (resumable)"
        ),
        resume: bool = typer.Option(
            False, "--resume", help="Resume from last checkpoint"
        ),
    ):
        """Process enrichment queue with lean context enhancement"""

        async def main():
            try:
                processor = EFEnrichmentProcessor()

                # Set up checkpoint manager for resumable operations
                checkpoint_manager = get_checkpoint_manager("p4_enrich")

                # Load checkpoint state
                checkpoint_state = checkpoint_manager.load_checkpoint() if resume else {}
                processed_count = checkpoint_state.get("processed_count", 0)
                last_ef_id = checkpoint_state.get("last_ef_id", None)

                if resume and checkpoint_state:
                    logger.info(f"Resuming from checkpoint: {processed_count} items processed, last EF: {last_ef_id}")

                # Determine batch processing vs original logic
                if batch is not None:
                    # Batch processing mode with checkpoints
                    max_process = batch
                    logger.info(f"Processing batch of {batch} EFs from enrichment queue (resumable)")
                elif daily_cap:
                    max_process = None  # Use processor's daily cap
                    logger.info(
                        f"Processing enrichment queue with daily cap ({processor.daily_enrichment_cap})"
                    )
                else:
                    max_process = max_items
                    logger.info(
                        f"Processing up to {max_items} EFs from enrichment queue"
                    )

                # Get the queue
                full_queue = await processor.get_enrichment_queue(limit=1000)

                # Filter queue based on checkpoint if resuming
                if resume and last_ef_id:
                    try:
                        last_index = full_queue.index(last_ef_id)
                        queue_to_process = full_queue[last_index + 1:]
                        logger.info(f"Resuming after EF {last_ef_id}, {len(queue_to_process)} items remaining")
                    except ValueError:
                        queue_to_process = full_queue
                        logger.warning(f"Last processed EF {last_ef_id} not found in queue, processing from start")
                else:
                    queue_to_process = full_queue

                # Apply batch limit if specified
                if max_process is not None and len(queue_to_process) > max_process:
                    queue_to_process = queue_to_process[:max_process]

                if not queue_to_process:
                    logger.info("No items to process (queue empty or all items already processed)")
                    return

                # Process items one by one with checkpoint updates
                results = {"processed": 0, "succeeded": 0, "failed": 0}

                for i, ef_id in enumerate(queue_to_process, 1):
                    logger.info(f"Processing EF {i}/{len(queue_to_process)}: {ef_id}")

                    # Process single EF
                    result = await processor.enrich_event_family(ef_id)

                    results["processed"] += 1
                    if result and result.status == "completed":
                        results["succeeded"] += 1
                    else:
                        results["failed"] += 1

                    # Update checkpoint every item
                    checkpoint_manager.update_progress(
                        processed_count=processed_count + results["processed"],
                        last_ef_id=ef_id,
                        total_succeeded=results["succeeded"],
                        total_failed=results["failed"]
                    )

                    # Log progress every 5 items
                    if i % 5 == 0:
                        logger.info(f"Progress: {i}/{len(queue_to_process)} processed")

                # Clear checkpoint on successful completion
                if batch is None:  # Only clear if not in batch mode
                    checkpoint_manager.clear_checkpoint()

                # Display results
                logger.info("=== ENRICHMENT RESULTS ===")
                logger.info(f"Items processed: {results['processed']}")
                logger.info(f"Successful: {results['succeeded']}")
                logger.info(f"Failed: {results['failed']}")

                if results["failed"] > 0:
                    logger.warning(
                        f"Success rate: {results['succeeded']/results['processed']:.1%}"
                    )
                else:
                    logger.success("All enrichments completed successfully!")

            except Exception as e:
                logger.error(f"Enrichment processing failed: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    @app.command()
    def enrich_single(
        ef_id: str = typer.Argument(..., help="Event Family UUID to enrich"),
        show_payload: bool = typer.Option(
            False, "--show-payload", help="Display enrichment payload after processing"
        ),
    ):
        """Enrich a single Event Family"""

        async def main():
            try:
                processor = EFEnrichmentProcessor()

                logger.info(f"Enriching Event Family: {ef_id}")

                # Process single EF
                result = await processor.enrich_event_family(ef_id)

                if not result:
                    logger.error(f"Failed to enrich EF {ef_id}")
                    raise typer.Exit(1)

                # Display results
                logger.info("=== ENRICHMENT COMPLETED ===")
                logger.info(f"Status: {result.status}")
                logger.info(f"Processing time: {result.processing_time_ms}ms")
                logger.info(f"Tokens used: {result.tokens_used}")
                logger.info(f"Sources found: {result.sources_found}")

                if result.status == "failed":
                    logger.error(f"Error: {result.error_message}")
                    raise typer.Exit(1)

                if show_payload:
                    logger.info("=== ENRICHMENT PAYLOAD ===")
                    payload = result.enrichment_payload

                    if payload.canonical_actors:
                        logger.info("Canonical Actors:")
                        for actor in payload.canonical_actors:
                            logger.info(f"  - {actor.name} ({actor.role})")

                    if payload.policy_status:
                        logger.info(f"Policy Status: {payload.policy_status}")

                    if payload.time_span.get("start"):
                        logger.info(
                            f"Time Span: {payload.time_span['start']} to {payload.time_span.get('end', 'ongoing')}"
                        )

                    if payload.magnitude:
                        logger.info("Magnitudes:")
                        for mag in payload.magnitude:
                            logger.info(f"  - {mag.value} {mag.unit} ({mag.what})")

                    if payload.official_sources:
                        logger.info("Official Sources:")
                        for source in payload.official_sources:
                            logger.info(f"  - {source}")

                    if payload.why_strategic:
                        logger.info(f"Strategic Significance: {payload.why_strategic}")

                logger.success(f"Enrichment completed for EF {ef_id}")

            except Exception as e:
                logger.error(f"Single EF enrichment failed: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    @app.command()
    def show_queue(
        limit: int = typer.Option(20, "--limit", help="Number of queue items to show"),
    ):
        """Show current enrichment queue prioritized by strategic importance"""

        async def main():
            try:
                processor = EFEnrichmentProcessor()

                logger.info("Fetching enrichment queue...")
                queue = await processor.get_enrichment_queue(limit=limit)

                if not queue:
                    logger.info("Enrichment queue is empty")
                    return

                logger.info(f"=== ENRICHMENT QUEUE ({len(queue)} items) ===")

                # Get EF details for display
                from sqlalchemy import text

                from core.database import get_db_session

                with get_db_session() as session:
                    for i, ef_id in enumerate(queue, 1):
                        result = session.execute(
                            text(
                                """
                                SELECT title, event_type, primary_theater, created_at,
                                       (SELECT COUNT(*) FROM titles t WHERE t.event_family_id = ef.id) as title_count
                                FROM event_families ef
                                WHERE id = :ef_id
                            """
                            ),
                            {"ef_id": ef_id},
                        ).fetchone()

                        if result:
                            age_days = (
                                processor.config.project_root.stat().st_mtime
                                - result.created_at.timestamp()
                            ) // 86400
                            logger.info(
                                f"{i:2d}. {result.title} "
                                f"({result.title_count} titles, {result.primary_theater}/{result.event_type}, "
                                f"{age_days:.0f}d old)"
                            )

            except Exception as e:
                logger.error(f"Failed to show queue: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    @app.command()
    def show_enrichment(
        ef_id: str = typer.Argument(..., help="Event Family UUID"),
    ):
        """Display existing enrichment for an Event Family"""

        async def main():
            try:
                processor = EFEnrichmentProcessor()

                # Load enrichment record
                record = await processor.get_enrichment_for_ef(ef_id)

                if not record:
                    logger.warning(f"No enrichment found for EF {ef_id}")
                    return

                # Display enrichment details
                logger.info(f"=== ENRICHMENT RECORD: {ef_id} ===")
                logger.info(f"Status: {record.status}")
                logger.info(f"Enriched at: {record.enriched_at}")
                logger.info(f"Processing time: {record.processing_time_ms}ms")
                logger.info(f"Tokens used: {record.tokens_used}")

                if record.status == "failed":
                    logger.error(f"Error: {record.error_message}")
                    return

                # Display payload
                payload = record.enrichment_payload

                if payload.canonical_actors:
                    logger.info("\nCanonical Actors:")
                    for actor in payload.canonical_actors:
                        logger.info(f"  - {actor.name} ({actor.role})")

                if payload.policy_status:
                    logger.info(f"\nPolicy Status: {payload.policy_status}")

                if payload.time_span.get("start"):
                    end_date = payload.time_span.get("end", "ongoing")
                    logger.info(f"Time Span: {payload.time_span['start']} → {end_date}")

                if payload.magnitude:
                    logger.info("\nMagnitudes:")
                    for mag in payload.magnitude:
                        logger.info(f"  - {mag.value:,.0f} {mag.unit}")
                        logger.info(f"    Context: {mag.what}")

                if payload.official_sources:
                    logger.info("\nOfficial Sources:")
                    for source in payload.official_sources:
                        logger.info(f"  - {source}")

                if payload.why_strategic:
                    logger.info("\nStrategic Significance:")
                    logger.info(f"  {payload.why_strategic}")

            except Exception as e:
                logger.error(f"Failed to show enrichment: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    @app.command()
    def stats():
        """Show enrichment system statistics"""

        async def main():
            try:
                processor = EFEnrichmentProcessor()

                # Count enrichment files
                enrichment_files = list(
                    processor.enrichment_dir.glob("ef_*_enrichment.json")
                )
                total_enrichments = len(enrichment_files)

                # Count by status
                import json

                stats = {"completed": 0, "failed": 0, "processing": 0}

                for filepath in enrichment_files:
                    try:
                        with open(filepath, "r") as f:
                            data = json.load(f)
                            status = data.get("status", "unknown")
                            if status in stats:
                                stats[status] += 1
                    except Exception:
                        continue

                # Get queue size
                queue = await processor.get_enrichment_queue(limit=1000)
                queue_size = len(queue)

                # Display statistics
                logger.info("=== ENRICHMENT SYSTEM STATISTICS ===")
                logger.info(f"Total enrichments: {total_enrichments}")
                logger.info(f"  Completed: {stats['completed']}")
                logger.info(f"  Failed: {stats['failed']}")
                logger.info(f"  Processing: {stats['processing']}")
                logger.info(f"Pending queue size: {queue_size}")
                logger.info(f"Daily enrichment cap: {processor.daily_enrichment_cap}")
                logger.info(f"Storage location: {processor.enrichment_dir}")

                if total_enrichments > 0:
                    success_rate = stats["completed"] / total_enrichments
                    logger.info(f"Success rate: {success_rate:.1%}")

            except Exception as e:
                logger.error(f"Failed to get statistics: {e}")
                raise typer.Exit(1)

        asyncio.run(main())

    return app


if __name__ == "__main__":
    app = create_enrichment_cli()
    app()
