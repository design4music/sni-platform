#!/usr/bin/env python3
"""
SNI-v2 Unified Pipeline Orchestrator
Coordinates RSS ingestion → strategic filtering → Event Family generation
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import typer
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import get_config  # noqa: E402

app = typer.Typer(help="SNI-v2 Pipeline Orchestrator")
config = get_config()


class PipelineOrchestrator:
    """Main pipeline coordinator"""

    def __init__(self):
        self.config = get_config()
        self.start_time = datetime.now()
        self.cycle_count = 0
        self.error_count = 0
        self.status = {"phase": "idle", "last_run": None, "errors": []}

    def log_status(self, phase: str, status: str, details: Optional[Dict] = None):
        """Update pipeline status tracking"""
        self.status.update(
            {
                "phase": phase,
                "status": status,
                "last_update": datetime.now().isoformat(),
                "cycle": self.cycle_count,
                "details": details or {},
            }
        )

        # Write status to file for monitoring
        status_file = Path(self.config.pipeline_status_file)
        status_file.parent.mkdir(exist_ok=True)

        with open(status_file, "w") as f:
            json.dump(self.status, f, indent=2, default=str)

        # Write heartbeat
        heartbeat_file = Path(self.config.pipeline_heartbeat_file)
        with open(heartbeat_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "cycle": self.cycle_count,
                    "uptime_minutes": (datetime.now() - self.start_time).total_seconds()
                    / 60,
                },
                f,
                indent=2,
            )

    async def run_phase_1_ingest(self) -> Dict:
        """Phase 1: RSS Ingestion"""
        if not self.config.phase_1_ingest_enabled:
            return {"status": "skipped", "reason": "disabled"}

        logger.info("=== PHASE 1: RSS INGESTION ===")
        self.log_status("1_ingest", "running")

        try:
            # Run ingestion subprocess

            cmd = [sys.executable, "-m", "apps.ingest.run_ingestion"]
            if (
                hasattr(self.config, "phase_1_max_feeds")
                and self.config.phase_1_max_feeds
            ):
                cmd.extend(["--max-feeds", str(self.config.phase_1_max_feeds)])

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"Ingestion failed: {stderr.decode()}")

            result = {"stdout": stdout.decode(), "stderr": stderr.decode()}

            self.log_status("1_ingest", "completed", {"result": result})
            logger.info(f"Phase 1 completed: {result}")
            return {"status": "success", "result": result}

        except Exception as e:
            self.error_count += 1
            self.status["errors"].append(
                {
                    "phase": "1_ingest",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self.log_status("1_ingest", "error", {"error": str(e)})
            logger.error(f"Phase 1 failed: {e}")
            return {"status": "error", "error": str(e)}

    async def run_phase_2_filter(self) -> Dict:
        """Phase 2: Strategic Filtering + Entity Extraction"""
        if not self.config.phase_2_filter_enabled:
            return {"status": "skipped", "reason": "disabled"}

        logger.info("=== PHASE 2: STRATEGIC FILTERING ===")
        self.log_status("2_filter", "running")

        try:
            # Run enhanced gate subprocess
            cmd = [sys.executable, "-m", "apps.filter.run_enhanced_gate"]

            if (
                hasattr(self.config, "phase_2_max_titles")
                and self.config.phase_2_max_titles
            ):
                cmd.extend(["--max-titles", str(self.config.phase_2_max_titles)])

            if (
                hasattr(self.config, "processing_window_hours")
                and self.config.processing_window_hours
            ):
                cmd.extend(["--hours", str(self.config.processing_window_hours)])

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"Enhanced gate failed: {stderr.decode()}")

            result = {"stdout": stdout.decode(), "stderr": stderr.decode()}

            self.log_status("2_filter", "completed", {"result": result})
            logger.info(f"Phase 2 completed: {result}")
            return {"status": "success", "result": result}

        except Exception as e:
            self.error_count += 1
            self.status["errors"].append(
                {
                    "phase": "2_filter",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self.log_status("2_filter", "error", {"error": str(e)})
            logger.error(f"Phase 2 failed: {e}")
            return {"status": "error", "error": str(e)}

    async def run_phase_3_generate(self) -> Dict:
        """Phase 3: Event Family Generation via MAP/REDUCE"""
        if not self.config.phase_3_generate_enabled:
            return {"status": "skipped", "reason": "disabled"}

        logger.info("=== PHASE 3: EVENT FAMILY GENERATION (MAP/REDUCE) ===")
        self.log_status("3_generate", "running")

        try:
            # Run MAP/REDUCE processor subprocess
            max_titles = getattr(self.config, "phase_3_max_titles", 500)

            logger.info(f"Phase 3: MAP/REDUCE EF Generation (max {max_titles} titles)")
            cmd = [
                sys.executable,
                "-m",
                "apps.generate.mapreduce_processor",
                str(max_titles),
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"MAP/REDUCE processing failed: {stderr.decode()}")

            result = {
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "processing_method": "MAP/REDUCE",
            }

            self.log_status("3_generate", "completed", {"result": result})
            logger.info("Phase 3 (MAP/REDUCE) completed successfully")
            return {"status": "success", "result": result}

        except Exception as e:
            self.error_count += 1
            self.status["errors"].append(
                {
                    "phase": "3_generate",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self.log_status("3_generate", "error", {"error": str(e)})
            logger.error(f"Phase 3 failed: {e}")
            return {"status": "error", "error": str(e)}

    async def run_single_cycle(self) -> Dict:
        """Execute one complete pipeline cycle"""
        self.cycle_count += 1
        cycle_start = datetime.now()

        logger.info(f"=== PIPELINE CYCLE {self.cycle_count} START ===")
        self.log_status("cycle", "starting")

        results = {}

        # Execute phases sequentially
        if self.config.phase_1_ingest_enabled:
            results["phase_1"] = await self.run_phase_1_ingest()

        if self.config.phase_2_filter_enabled:
            results["phase_2"] = await self.run_phase_2_filter()

        if self.config.phase_3_generate_enabled:
            results["phase_3"] = await self.run_phase_3_generate()

        # Calculate cycle metrics
        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        cycle_summary = {
            "cycle": self.cycle_count,
            "duration_seconds": cycle_duration,
            "results": results,
            "error_count": self.error_count,
            "timestamp": datetime.now().isoformat(),
        }

        self.log_status("cycle", "completed", cycle_summary)

        # Check error threshold
        if self.error_count >= self.config.pipeline_error_threshold:
            logger.error(f"Error threshold reached: {self.error_count}")
            raise Exception(f"Too many errors: {self.error_count}")

        logger.info(
            f"=== CYCLE {self.cycle_count} COMPLETED in {cycle_duration:.1f}s ==="
        )
        return cycle_summary

    async def run_daemon(self):
        """Run pipeline in daemon mode with interval"""
        logger.info("=== STARTING PIPELINE DAEMON ===")
        logger.info(f"Interval: {self.config.pipeline_interval_minutes} minutes")
        logger.info(f"Max cycles: {self.config.pipeline_max_cycles or 'unlimited'}")

        while True:
            try:
                # Run cycle
                await self.run_single_cycle()

                # Check max cycles limit
                if (
                    self.config.pipeline_max_cycles
                    and self.cycle_count >= self.config.pipeline_max_cycles
                ):
                    logger.info(f"Max cycles reached: {self.cycle_count}")
                    break

                # Wait for next cycle
                if self.config.pipeline_daemon_mode:
                    wait_minutes = self.config.pipeline_interval_minutes
                    logger.info(f"Waiting {wait_minutes} minutes until next cycle...")
                    await asyncio.sleep(wait_minutes * 60)
                else:
                    # Single run mode
                    break

            except KeyboardInterrupt:
                logger.info("Pipeline stopped by user")
                break
            except Exception as e:
                logger.error(f"Pipeline cycle failed: {e}")
                if self.error_count >= self.config.pipeline_error_threshold:
                    logger.error("Error threshold exceeded, stopping pipeline")
                    break
                # Wait before retry
                logger.info("Waiting 5 minutes before retry...")
                await asyncio.sleep(300)


# CLI Commands


@app.command()
def run(
    daemon: bool = typer.Option(False, "--daemon", help="Run in daemon mode"),
    cycles: Optional[int] = typer.Option(
        None, "--max-cycles", help="Maximum cycles to run"
    ),
    interval: Optional[int] = typer.Option(
        None, "--interval", help="Minutes between cycles"
    ),
):
    """Run the complete SNI pipeline"""

    # Override config with CLI parameters
    if daemon is not None:
        config.pipeline_daemon_mode = daemon
    if cycles is not None:
        config.pipeline_max_cycles = cycles
    if interval is not None:
        config.pipeline_interval_minutes = interval

    logger.info("=== SNI-v2 PIPELINE ORCHESTRATOR ===")
    logger.info(f"Daemon mode: {config.pipeline_daemon_mode}")
    logger.info(f"Interval: {config.pipeline_interval_minutes} minutes")
    logger.info(f"Max cycles: {config.pipeline_max_cycles or 'unlimited'}")

    # Create and run orchestrator
    orchestrator = PipelineOrchestrator()

    try:
        asyncio.run(orchestrator.run_daemon())
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


@app.command()
def status():
    """Show pipeline status"""
    status_file = Path(config.pipeline_status_file)
    heartbeat_file = Path(config.pipeline_heartbeat_file)

    print("=== PIPELINE STATUS ===")

    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)

        print(f"Phase: {status.get('phase', 'unknown')}")
        print(f"Status: {status.get('status', 'unknown')}")
        print(f"Cycle: {status.get('cycle', 0)}")
        print(f"Last Update: {status.get('last_update', 'never')}")

        if status.get("errors"):
            print(f"Recent Errors: {len(status['errors'])}")
            for error in status["errors"][-3:]:
                print(f"  {error['timestamp']}: {error['error']}")
    else:
        print("No status file found")

    print()

    if heartbeat_file.exists():
        with open(heartbeat_file) as f:
            heartbeat = json.load(f)

        print("=== HEARTBEAT ===")
        print(f"Last Heartbeat: {heartbeat.get('timestamp', 'never')}")
        print(f"Uptime: {heartbeat.get('uptime_minutes', 0):.1f} minutes")
        print(f"Cycles Completed: {heartbeat.get('cycle', 0)}")
    else:
        print("No heartbeat file found")


@app.command()
def phase1(
    max_feeds: Optional[int] = typer.Option(None, help="Maximum feeds to process")
):
    """Run Phase 1: RSS Ingestion only"""

    async def run_phase1():
        orchestrator = PipelineOrchestrator()
        if max_feeds:
            orchestrator.config.phase_1_max_feeds = max_feeds
        result = await orchestrator.run_phase_1_ingest()
        print(f"Phase 1 result: {result}")

    asyncio.run(run_phase1())


@app.command()
def phase2(
    max_titles: Optional[int] = typer.Option(None, help="Maximum titles to process"),
    hours: Optional[int] = typer.Option(None, help="Processing window in hours"),
):
    """Run Phase 2: Strategic Filtering only"""

    async def run_phase2():
        orchestrator = PipelineOrchestrator()
        if max_titles:
            orchestrator.config.phase_2_max_titles = max_titles
        if hours:
            orchestrator.config.processing_window_hours = hours
        result = await orchestrator.run_phase_2_filter()
        print(f"Phase 2 result: {result}")

    asyncio.run(run_phase2())


@app.command()
def phase3(
    max_titles: Optional[int] = typer.Option(None, help="Maximum titles to process"),
    pass_only: Optional[str] = typer.Option(None, help="Run only 'pass1' or 'pass2'"),
):
    """Run Phase 3: Event Family Generation only"""

    async def run_phase3():
        orchestrator = PipelineOrchestrator()
        if max_titles:
            orchestrator.config.phase_3_max_titles = max_titles

        if pass_only:
            # Legacy pass system deprecated - use MAP/REDUCE instead
            logger.warning(
                f"Pass '{pass_only}' deprecated. Running MAP/REDUCE instead."
            )
            cmd = [sys.executable, "-m", "apps.generate.mapreduce_processor"]
            if max_titles:
                cmd.append(str(max_titles))

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                result = {"status": "error", "error": stderr.decode()}
            else:
                result = {
                    "status": "success",
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "method": "MAP/REDUCE",
                }

            print(f"Phase 3 {pass_only} result: {result}")
        else:
            result = await orchestrator.run_phase_3_generate()
            print(f"Phase 3 result: {result}")

    asyncio.run(run_phase3())


@app.command()
def phase3_mapreduce(
    max_titles: int = typer.Option(1000, help="Maximum titles to process"),
    dry_run: bool = typer.Option(False, help="Dry run mode (no database writes)"),
):
    """Phase 3: MAP/REDUCE Event Family Generation (Alternative Implementation)"""

    async def run_mapreduce():
        try:
            config = get_config()
            if not getattr(
                config, "mapreduce_enabled", True
            ):  # Default enabled for testing
                logger.warning(
                    "MAP/REDUCE processing may be disabled in config. Set MAPREDUCE_ENABLED=true to enable."
                )

            from apps.generate.mapreduce_processor import MapReduceProcessor

            processor = MapReduceProcessor()

            if dry_run:
                logger.info("DRY RUN MODE: No database writes will be performed")
                return

            logger.info(
                f"Starting MAP/REDUCE processing for up to {max_titles} titles..."
            )
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

            if result.total_seconds <= 180:  # 3 minutes
                logger.info("✓ Performance target achieved: ≤3 minutes")
            else:
                logger.warning(
                    f"✗ Performance target missed: {result.total_seconds:.1f}s > 180s"
                )

        except Exception as e:
            logger.error(f"MAP/REDUCE processing failed: {e}")
            raise typer.Exit(1)

    asyncio.run(run_mapreduce())


if __name__ == "__main__":
    app()
