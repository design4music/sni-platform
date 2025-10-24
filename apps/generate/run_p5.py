#!/usr/bin/env python3
"""
Phase 5: Framed Narratives CLI
Command-line interface for narrative framing analysis
"""

import asyncio
import sys
from pathlib import Path

import typer
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.generate.framing_processor import run_framing_processor  # noqa: E402
from core.config import get_config  # noqa: E402

app = typer.Typer(help="Phase 5: Framed Narratives Generation")


@app.command()
def process(
    max_items: int = typer.Option(
        None, "--max-items", help="Maximum EFs to process (default: config value)"
    ),
):
    """
    Process Event Families to extract narrative framings.

    Only processes 'active' EFs without existing framed narratives.
    """
    config = get_config()

    if not config.phase_5_framing_enabled:
        logger.warning("Phase 5 (Framing) is disabled in configuration")
        return

    limit = max_items or config.phase_5_max_items

    logger.info(f"Starting Phase 5: Framed Narratives (limit={limit})")

    try:
        stats = asyncio.run(run_framing_processor(limit))

        logger.info("=== PHASE 5 RESULTS ===")
        logger.info(f"Event Families processed: {stats['processed']}")
        logger.info(f"Framed Narratives created: {stats['total_frames']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Duration: {stats['duration_seconds']:.1f}s")

        if stats["processed"] > 0:
            avg_time = stats["duration_seconds"] / stats["processed"]
            logger.info(f"Average time per EF: {avg_time:.1f}s")

    except Exception as e:
        logger.error(f"Phase 5 processing failed: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
