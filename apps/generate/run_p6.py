#!/usr/bin/env python3
"""
RAI Analysis CLI for SNI-v2
Process Framed Narratives through external RAI service
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio  # noqa: E402

import typer  # noqa: E402
from loguru import logger  # noqa: E402

from apps.generate.rai_processor import run_rai_processor  # noqa: E402

app = typer.Typer(
    help="RAI (Risk Assessment Intelligence) Analysis for Framed Narratives"
)


@app.command()
def process(
    max_items: int = typer.Option(
        None,
        "--max-items",
        "-n",
        help="Maximum number of Framed Narratives to process (default: from config)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    Process Framed Narratives through RAI analysis service

    Sends FNs to external RAI service and stores analysis results.
    Only processes FNs that haven't been analyzed yet (rai_analysis IS NULL).
    """
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    try:
        logger.info("Starting RAI analysis processing...")

        # Run async processor
        stats = asyncio.run(run_rai_processor(limit=max_items))

        # Print results
        logger.info("=== RAI ANALYSIS SUMMARY ===")
        logger.info(f"Processed: {stats['processed']}")
        logger.info(f"Success: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Duration: {stats['duration_seconds']:.1f}s")

        if stats["processed"] > 0:
            success_rate = (stats["success"] / stats["processed"]) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")

        # Exit with appropriate code
        sys.exit(0 if stats["failed"] == 0 else 1)

    except Exception as e:
        logger.error(f"RAI processing failed: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def status():
    """
    Show RAI analysis queue status

    Displays counts of pending and analyzed Framed Narratives.
    """
    from sqlalchemy import text

    from core.database import get_db_session

    try:
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT
                    COUNT(*) FILTER (WHERE rai_analysis IS NULL) as pending,
                    COUNT(*) FILTER (WHERE rai_analysis IS NOT NULL) as analyzed,
                    COUNT(*) as total
                FROM framed_narratives fn
                JOIN event_families ef ON fn.event_family_id = ef.id
                WHERE ef.status IN ('active', 'enriched')
            """
                )
            )
            row = result.fetchone()

            typer.echo("\nRAI Analysis Status:")
            typer.echo(f"  Pending:  {row.pending}")
            typer.echo(f"  Analyzed: {row.analyzed}")
            typer.echo(f"  Total:    {row.total}")
            typer.echo()

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
