#!/usr/bin/env python3
"""
Daily CLUST-1 runner with hub-assist enabled (production mode)
Strict profile + event signals + hub-assist ON
"""

import argparse
import logging
import os
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_stage(stage, window=72, extra_args=None):
    """Run a CLUST-1 stage with hub-assist enabled."""
    cmd = [
        "python",
        "etl_pipeline/clustering/clust1_taxonomy_graph.py",
        "--stage",
        stage,
        "--window",
        str(window),
        "--profile",
        "strict",
        "--use_hub_assist",
        "1",
        "--macro_enable",
        "1",
    ]

    # Add stage-specific arguments
    if stage == "densify":
        cmd.extend(["--hub_pair_cos", "0.90", "--cos", "0.86"])

    if extra_args:
        cmd.extend(extra_args)

    logger.info(f"Running CLUST-1 {stage} stage: {' '.join(cmd[1:])}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode != 0:
            logger.error(f"Stage {stage} failed: {result.stderr}")
            return False

        logger.info(f"✓ Stage {stage} completed successfully")

        # Log key metrics from output
        for line in result.stdout.split("\n"):
            if any(
                keyword in line.lower()
                for keyword in ["seeds", "clusters", "members", "macro", "final"]
            ):
                logger.info(f"  {line.strip()}")

        return True

    except Exception as e:
        logger.error(f"Failed to run stage {stage}: {e}")
        return False


def run_orphan_attach(window=72):
    """Run orphan attachment stage."""
    cmd = [
        "python",
        "etl_pipeline/clustering/clust1_orphan_attach.py",
        "--window",
        str(window),
        "--cos",
        "0.89",
    ]

    logger.info(f"Running orphan attach: {' '.join(cmd[1:])}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode != 0:
            logger.error(f"Orphan attach failed: {result.stderr}")
            return False

        logger.info("✓ Orphan attach completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to run orphan attach: {e}")
        return False


def main():
    """Run complete CLUST-1 pipeline with hub-assist."""
    parser = argparse.ArgumentParser(description="Daily CLUST-1 runner with hub-assist")
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument(
        "--skip-refresh", action="store_true", help="Skip materialized view refresh"
    )

    args = parser.parse_args()

    logger.info(f"Starting CLUST-1 hub-assist pipeline (window: {args.window}h)")

    try:
        # Step 1: Refresh materialized views (unless skipped)
        if not args.skip_refresh:
            logger.info("Step 1: Refreshing materialized views...")
            refresh_result = subprocess.run(
                ["python", "etl_pipeline/clustering/clust0_refresh_event_signals.py"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
            )

            if refresh_result.returncode != 0:
                logger.error("Materialized view refresh failed")
                return False
        else:
            logger.info("Step 1: Skipping materialized view refresh")

        # Step 2: Seed stage
        logger.info("Step 2: Running seed stage...")
        if not run_stage("seed", args.window):
            return False

        # Step 3: Densify stage
        logger.info("Step 3: Running densify stage...")
        if not run_stage("densify", args.window):
            return False

        # Step 4: Orphan attach
        logger.info("Step 4: Running orphan attach...")
        if not run_orphan_attach(args.window):
            return False

        # Step 5: Persist stage
        logger.info("Step 5: Running persist stage...")
        if not run_stage("persist", args.window):
            return False

        logger.info("🎉 CLUST-1 hub-assist pipeline completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
