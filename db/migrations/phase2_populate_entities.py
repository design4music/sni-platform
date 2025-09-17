#!/usr/bin/env python3
"""
Phase 2A Backfill: Populate existing titles with entities
Backfills titles.entities for existing strategic titles
"""

import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.filter.entity_enrichment import \
    get_entity_enrichment_service  # noqa: E402
from core.database import get_db_session  # noqa: E402


def backfill_entities_for_strategic_titles(
    limit: int = 5000, batch_size: int = 500
) -> dict:
    """
    Backfill entities for existing strategic titles.

    Args:
        limit: Maximum titles to process
        batch_size: Process in batches of this size

    Returns:
        processing stats
    """
    logger.info("=== PHASE 2A ENTITY BACKFILL ===")

    stats = {
        "total_processed": 0,
        "strategic_enriched": 0,
        "non_strategic_enriched": 0,
        "errors": 0,
    }

    try:
        service = get_entity_enrichment_service()

        # Get strategic titles without entities
        with get_db_session() as session:
            query = """
            SELECT id 
            FROM titles 
            WHERE gate_keep = true 
            AND (entities IS NULL OR entities->>'extraction_version' != '2.0')
            ORDER BY created_at DESC
            LIMIT :limit
            """

            results = session.execute(text(query), {"limit": limit}).fetchall()
            title_ids = [str(row.id) for row in results]

        logger.info(f"Found {len(title_ids)} strategic titles to backfill")

        # Process in batches
        for i in range(0, len(title_ids), batch_size):
            batch_ids = title_ids[i : i + batch_size]
            logger.info(
                f"Processing batch {i//batch_size + 1}: {len(batch_ids)} titles"
            )

            batch_stats = service.enrich_titles_batch(title_ids=batch_ids)

            stats["total_processed"] += batch_stats["processed"]
            stats["strategic_enriched"] += batch_stats["strategic"]
            stats["non_strategic_enriched"] += batch_stats["non_strategic"]
            stats["errors"] += batch_stats["errors"]

        logger.info("=== BACKFILL COMPLETE ===")
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Strategic enriched: {stats['strategic_enriched']}")
        logger.info(f"Non-strategic enriched: {stats['non_strategic_enriched']}")
        logger.info(f"Errors: {stats['errors']}")

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        raise

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill entities for existing strategic titles"
    )
    parser.add_argument("--limit", type=int, default=5000, help="Max titles to process")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size")

    args = parser.parse_args()

    backfill_entities_for_strategic_titles(limit=args.limit, batch_size=args.batch_size)
