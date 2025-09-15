#!/usr/bin/env python3
"""
Reset Processing Status Utility
Resets titles back to pending status for reprocessing
"""

import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_config


def reset_to_pending():
    """Reset all gated titles back to pending status"""
    config = get_config()
    engine = create_engine(config.database_url)

    with engine.connect() as conn:
        # Get current counts
        result = conn.execute(
            text(
                """
            SELECT 
                COUNT(*) FILTER (WHERE processing_status = 'pending') as pending,
                COUNT(*) FILTER (WHERE processing_status = 'gated') as gated,
                COUNT(*) as total
            FROM titles
        """
            )
        )
        before = result.fetchone()

        logger.info(
            f"Before reset: {before.pending} pending, {before.gated} gated, {before.total} total"
        )

        # Reset all to pending
        result = conn.execute(
            text(
                """
            UPDATE titles SET 
                processing_status = 'pending',
                gate_keep = NULL,
                gate_reason = NULL,
                gate_score = NULL,
                gate_actor_hit = NULL,
                gate_at = NULL
            WHERE processing_status = 'gated'
        """
            )
        )

        updated_count = result.rowcount
        conn.commit()

        logger.info(f"Reset {updated_count} titles back to pending status")

        # Verify final counts
        result = conn.execute(
            text(
                """
            SELECT 
                COUNT(*) FILTER (WHERE processing_status = 'pending') as pending,
                COUNT(*) FILTER (WHERE processing_status = 'gated') as gated,
                COUNT(*) as total
            FROM titles
        """
            )
        )
        after = result.fetchone()

        logger.info(
            f"After reset: {after.pending} pending, {after.gated} gated, {after.total} total"
        )

        return updated_count


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Reset Processing Status")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the reset (required for safety)",
    )

    args = parser.parse_args()

    if not args.confirm:
        print("This will reset ALL gated titles back to pending status.")
        print("Use --confirm to actually perform the reset.")
        return

    try:
        updated = reset_to_pending()
        print(f"Successfully reset {updated} titles to pending status")

    except Exception as e:
        logger.error(f"Reset failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
