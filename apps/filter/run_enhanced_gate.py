#!/usr/bin/env python3
"""
Phase 2A: Enhanced Gate Processing
Combines strategic filtering (CLUST-1) + entity extraction
to populate both gate_keep and titles.entities columns in one pass.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.filter.entity_enrichment import get_entity_enrichment_service
from core.checkpoint import get_checkpoint_manager
from core.database import get_db_session


async def run_enhanced_gate_processing_batch(
    batch_size: int = None,
    resume: bool = False,
    hours: int = 24,
    max_titles: int = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Enhanced gate processing with batch processing and checkpoint support.

    Args:
        batch_size: Number of titles to process in this batch
        resume: Resume from last checkpoint
        hours: Process titles from last N hours
        max_titles: Maximum titles to process
        dry_run: Don't write to database

    Returns:
        processing stats
    """
    logger.info("=== PHASE 2A ENHANCED GATE PROCESSING (BATCH MODE) ===")

    stats = {
        "titles_processed": 0,
        "strategic_titles": 0,
        "non_strategic_titles": 0,
        "entities_extracted": 0,
        "blocked_by_stop": 0,
        "errors": 0,
        "processing_time": 0,
    }

    start_time = asyncio.get_event_loop().time()

    try:
        # Set up checkpoint manager
        checkpoint_manager = get_checkpoint_manager("p2_filter")

        # Load checkpoint state
        checkpoint_state = checkpoint_manager.load_checkpoint() if resume else {}
        processed_count = checkpoint_state.get("processed_count", 0)
        last_title_id = checkpoint_state.get("last_title_id", None)

        if resume and checkpoint_state:
            logger.info(
                f"Resuming from checkpoint: {processed_count} titles processed, last title ID: {last_title_id}"
            )

        # Get services
        entity_service = get_entity_enrichment_service()

        # Get titles to process
        with get_db_session() as session:
            query = f"""
            SELECT
                id,
                title_display,
                gate_keep,
                entities
            FROM titles
            WHERE created_at >= NOW() - INTERVAL '{hours} HOUR'
            AND (
                gate_keep IS NULL
                OR entities IS NULL
                OR entities->>'extraction_version' != '2.0'
            )
            ORDER BY id ASC
            """

            results = session.execute(text(query)).fetchall()

        logger.info(f"Found {len(results)} total titles for processing")

        # Filter titles based on checkpoint if resuming
        if resume and last_title_id:
            try:
                title_ids = [str(row.id) for row in results]
                last_index = title_ids.index(last_title_id)
                titles_to_process = results[last_index + 1 :]
                logger.info(
                    f"Resuming after title ID {last_title_id}, {len(titles_to_process)} titles remaining"
                )
            except ValueError:
                titles_to_process = results
                logger.warning(
                    f"Last processed title ID {last_title_id} not found, processing from start"
                )
        else:
            titles_to_process = results

        # Apply batch limits
        batch_limit = batch_size or max_titles
        if batch_limit and len(titles_to_process) > batch_limit:
            titles_to_process = titles_to_process[:batch_limit]
            logger.info(
                f"Processing batch of {len(titles_to_process)} titles (batch size: {batch_limit})"
            )
        else:
            logger.info(f"Processing {len(titles_to_process)} titles")

        if not titles_to_process:
            logger.info(
                "No titles to process (all titles already processed or empty batch)"
            )
            return stats

        # Process each title
        for i, row in enumerate(titles_to_process, 1):
            try:
                title_data = {
                    "id": str(row.id),
                    "title_display": row.title_display,
                    "gate_keep": row.gate_keep,
                    "entities": row.entities,
                }

                # Extract entities (this also determines strategic status)
                entities = await entity_service.extract_entities_for_title(title_data)

                # Strategic gate decision based on entities
                is_strategic = entities["is_strategic"]

                if not dry_run:
                    # Update both gate_keep and entities in one query
                    with get_db_session() as session:
                        update_query = """
                        UPDATE titles
                        SET
                            gate_keep = :gate_keep,
                            entities = :entities,
                            processing_status = 'gated'
                        WHERE id = :title_id
                        """

                        if not is_strategic and entities["actors"]:
                            stats["blocked_by_stop"] += 1

                        session.execute(
                            text(update_query),
                            {
                                "gate_keep": is_strategic,
                                "entities": json.dumps(entities),
                                "title_id": title_data["id"],
                            },
                        )
                        session.commit()

                # Update stats
                stats["titles_processed"] += 1
                if is_strategic:
                    stats["strategic_titles"] += 1
                else:
                    stats["non_strategic_titles"] += 1

                if entities["actors"]:
                    stats["entities_extracted"] += 1

                # Update checkpoint every 10 items
                if i % 10 == 0:
                    checkpoint_manager.update_progress(
                        processed_count=processed_count + stats["titles_processed"],
                        last_title_id=title_data["id"],
                        total_strategic=stats["strategic_titles"],
                        total_non_strategic=stats["non_strategic_titles"],
                        total_entities=stats["entities_extracted"],
                    )

                # Log progress every 100 titles
                if stats["titles_processed"] % 100 == 0:
                    logger.info(f"Processed {stats['titles_processed']} titles...")

            except Exception as e:
                logger.error(f"Error processing title {row.id}: {e}")
                stats["errors"] += 1

                # Update checkpoint even on error
                checkpoint_manager.update_progress(
                    processed_count=processed_count + stats["titles_processed"],
                    last_title_id=str(row.id),
                    total_strategic=stats["strategic_titles"],
                    total_non_strategic=stats["non_strategic_titles"],
                    total_entities=stats["entities_extracted"],
                )
                continue

        # Final checkpoint update
        if titles_to_process:
            checkpoint_manager.update_progress(
                processed_count=processed_count + stats["titles_processed"],
                last_title_id=str(titles_to_process[-1].id),
                total_strategic=stats["strategic_titles"],
                total_non_strategic=stats["non_strategic_titles"],
                total_entities=stats["entities_extracted"],
            )

        # Clear checkpoint on successful completion (if not in batch mode)
        if batch_size is None:
            checkpoint_manager.clear_checkpoint()

        stats["processing_time"] = asyncio.get_event_loop().time() - start_time

        # Final summary
        logger.info("=== ENHANCED GATE PROCESSING COMPLETE ===")
        logger.info(f"Titles processed: {stats['titles_processed']}")
        logger.info(f"Strategic titles: {stats['strategic_titles']}")
        logger.info(f"Non-strategic titles: {stats['non_strategic_titles']}")
        logger.info(f"Entities extracted: {stats['entities_extracted']}")
        logger.info(f"Blocked by stop words: {stats['blocked_by_stop']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Processing time: {stats['processing_time']:.2f}s")

        if dry_run:
            logger.info("DRY RUN: No database changes made")

    except Exception as e:
        logger.error(f"Enhanced gate processing failed: {e}")
        stats["errors"] = stats["titles_processed"] + 1
        raise

    return stats


async def run_enhanced_gate_processing(
    hours: int = 24, max_titles: int = None, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Enhanced gate processing combining strategic filtering + entity enrichment.

    Args:
        hours: Process titles from last N hours
        max_titles: Maximum titles to process
        dry_run: Don't write to database

    Returns:
        processing stats
    """
    logger.info("=== PHASE 2A ENHANCED GATE PROCESSING ===")

    stats = {
        "titles_processed": 0,
        "strategic_titles": 0,
        "non_strategic_titles": 0,
        "entities_extracted": 0,
        "blocked_by_stop": 0,
        "errors": 0,
        "processing_time": 0,
    }

    start_time = asyncio.get_event_loop().time()

    try:
        # Get services
        entity_service = get_entity_enrichment_service()

        # Get titles to process
        with get_db_session() as session:
            query = f"""
            SELECT 
                id,
                title_display,
                gate_keep,
                entities
            FROM titles 
            WHERE created_at >= NOW() - INTERVAL '{hours} HOUR'
            AND (
                gate_keep IS NULL 
                OR entities IS NULL 
                OR entities->>'extraction_version' != '2.0'
            )
            ORDER BY created_at DESC
            """

            if max_titles:
                query += f" LIMIT {max_titles}"

            results = session.execute(text(query)).fetchall()

        logger.info(f"Found {len(results)} titles to process")

        # Process each title
        for row in results:
            try:
                title_data = {
                    "id": str(row.id),
                    "title_display": row.title_display,
                    "gate_keep": row.gate_keep,
                    "entities": row.entities,
                }

                # Extract entities (this also determines strategic status)
                entities = await entity_service.extract_entities_for_title(title_data)

                # Strategic gate decision based on entities
                is_strategic = entities["is_strategic"]

                if not dry_run:
                    # Update both gate_keep and entities in one query
                    with get_db_session() as session:
                        update_query = """
                        UPDATE titles
                        SET
                            gate_keep = :gate_keep,
                            entities = :entities,
                            processing_status = 'gated'
                        WHERE id = :title_id
                        """

                        if not is_strategic and entities["actors"]:
                            stats["blocked_by_stop"] += 1

                        session.execute(
                            text(update_query),
                            {
                                "gate_keep": is_strategic,
                                "entities": json.dumps(entities),
                                "title_id": title_data["id"],
                            },
                        )
                        session.commit()

                # Update stats
                stats["titles_processed"] += 1
                if is_strategic:
                    stats["strategic_titles"] += 1
                else:
                    stats["non_strategic_titles"] += 1

                if entities["actors"]:
                    stats["entities_extracted"] += 1

                # Log progress every 100 titles
                if stats["titles_processed"] % 100 == 0:
                    logger.info(f"Processed {stats['titles_processed']} titles...")

            except Exception as e:
                logger.error(f"Error processing title {row.id}: {e}")
                stats["errors"] += 1
                continue

        stats["processing_time"] = asyncio.get_event_loop().time() - start_time

        # Final summary
        logger.info("=== ENHANCED GATE PROCESSING COMPLETE ===")
        logger.info(f"Titles processed: {stats['titles_processed']}")
        logger.info(f"Strategic titles: {stats['strategic_titles']}")
        logger.info(f"Non-strategic titles: {stats['non_strategic_titles']}")
        logger.info(f"Entities extracted: {stats['entities_extracted']}")
        logger.info(f"Blocked by stop words: {stats['blocked_by_stop']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Processing time: {stats['processing_time']:.2f}s")

        if dry_run:
            logger.info("DRY RUN: No database changes made")

    except Exception as e:
        logger.error(f"Enhanced gate processing failed: {e}")
        stats["errors"] = stats["titles_processed"] + 1
        raise

    return stats


async def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Gate Processing (Phase 2A)")
    parser.add_argument(
        "--hours", type=int, default=24, help="Process titles from last N hours"
    )
    parser.add_argument("--max-titles", type=int, help="Maximum titles to process")
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        help="Process titles in batches of this size (resumable)",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't write to database"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show enrichment status only"
    )

    args = parser.parse_args()

    if args.status:
        # Show status only
        entity_service = get_entity_enrichment_service()
        status = entity_service.get_enrichment_status()
        print("Enhanced Gate Processing Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return

    # Run enhanced processing
    # Use batch processing if --batch or --resume flags are provided
    if args.batch is not None or args.resume:
        await run_enhanced_gate_processing_batch(
            batch_size=args.batch,
            resume=args.resume,
            hours=args.hours,
            max_titles=args.max_titles,
            dry_run=args.dry_run,
        )
    else:
        await run_enhanced_gate_processing(
            hours=args.hours, max_titles=args.max_titles, dry_run=args.dry_run
        )


if __name__ == "__main__":
    asyncio.run(main())
