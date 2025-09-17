#!/usr/bin/env python3
"""
Phase 2A: Enhanced Gate Processing
Combines strategic filtering (CLUST-1) + entity extraction
to populate both gate_keep and titles.entities columns in one pass.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text

from apps.filter.entity_enrichment import get_entity_enrichment_service
from apps.filter.strategic_gate import get_strategic_gate_service
from core.database import get_db_session


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
        gate_service = get_strategic_gate_service()
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
                entities = entity_service.extract_entities_for_title(title_data)

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
                            gate_reason = :gate_reason,
                            gate_score = :gate_score,
                            gate_actor_hit = :gate_actor_hit
                        WHERE id = :title_id
                        """

                        # Build gate_reason
                        if is_strategic:
                            gate_reason = (
                                f"Strategic: {len(entities['actors'])} entities"
                            )
                            gate_actor_hit = (
                                entities["actors"][0] if entities["actors"] else None
                            )
                        else:
                            if entities["actors"]:
                                gate_reason = f"Blocked by stop words: {len(entities['actors'])} entities"
                                stats["blocked_by_stop"] += 1
                            else:
                                gate_reason = "No strategic entities found"
                            gate_actor_hit = None

                        session.execute(
                            text(update_query),
                            {
                                "gate_keep": is_strategic,
                                "entities": entities,  # SQLAlchemy will JSON serialize this
                                "gate_reason": gate_reason,
                                "gate_score": 0.8 if is_strategic else 0.2,
                                "gate_actor_hit": gate_actor_hit,
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
    await run_enhanced_gate_processing(
        hours=args.hours, max_titles=args.max_titles, dry_run=args.dry_run
    )


if __name__ == "__main__":
    asyncio.run(main())
