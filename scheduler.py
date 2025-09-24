#!/usr/bin/env python3
"""
SNI Pipeline Scheduler
Simple Python scheduler for running the SNI pipeline phases in a loop.
Uses the timeout mitigation system with --batch and --resume flags.
"""

import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/scheduler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def run_command(cmd, timeout_minutes, phase_name):
    """
    Run a command with timeout protection

    Args:
        cmd: Command list to run
        timeout_minutes: Timeout in minutes
        phase_name: Name for logging
    """
    try:
        logger.info(f"Starting {phase_name}: {' '.join(cmd)}")
        start_time = datetime.now()

        result = subprocess.run(
            cmd,
            check=False,
            timeout=timeout_minutes * 60,
            capture_output=True,
            text=True,
        )

        duration = (datetime.now() - start_time).total_seconds()

        if result.returncode == 0:
            logger.info(f"{phase_name} completed successfully in {duration:.1f}s")
        else:
            logger.warning(f"{phase_name} failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"{phase_name} stderr: {result.stderr[:500]}")

    except subprocess.TimeoutExpired:
        logger.warning(
            f"{phase_name} timed out after {timeout_minutes} minutes - will resume next cycle"
        )
    except Exception as e:
        logger.error(f"{phase_name} error: {e}")


def run_pipeline_cycle():
    """Run one complete pipeline cycle"""
    logger.info("=== Starting Pipeline Cycle ===")

    # P1 - RSS Ingestion (30 min timeout, 500 feed batch)
    run_command(
        ["python", "apps/ingest/run_ingestion.py", "--batch", "500", "--resume"],
        30,
        "P1 RSS Ingestion",
    )

    # P2 - Strategic Filtering (15 min timeout, 1000 title batch)
    run_command(
        ["python", "apps/filter/run_enhanced_gate.py", "--batch", "1000", "--resume"],
        15,
        "P2 Strategic Filtering",
    )

    # P3 - Event Family Generation (Background worker - skip in scheduler)
    # NOTE: P3 should run as a separate background process:
    # python apps/generate/incident_processor.py 1000 --background
    logger.info("P3 Generate: Skipping (should run as background worker)")

    # P4 - EF Enrichment (45 min timeout, 50 EF batch)
    run_command(
        ["python", "apps/enrich/cli.py", "enrich-queue", "--batch", "50", "--resume"],
        45,
        "P4 EF Enrichment",
    )

    logger.info("=== Pipeline Cycle Complete ===")


def main():
    """Main scheduler loop"""
    logger.info("SNI Pipeline Scheduler Starting...")
    logger.info("Note: Start P3 background worker separately:")
    logger.info("  python apps/generate/incident_processor.py 1000 --background")

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            logger.info(f"Starting cycle #{cycle_count}")

            run_pipeline_cycle()

            # 12-hour sleep between cycles (matching cron setup)
            sleep_hours = 12
            sleep_seconds = sleep_hours * 3600

            logger.info(f"Sleeping for {sleep_hours} hours until next cycle...")
            time.sleep(sleep_seconds)

    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise


if __name__ == "__main__":
    main()
