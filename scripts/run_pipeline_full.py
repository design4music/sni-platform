#!/usr/bin/env python3
"""
Complete SNI Pipeline Runner
Executes the full 12-step Strategic Narrative Intelligence pipeline in the correct order:
RSS -> Full-text -> Keywords -> Canonicalize -> CLUST-0 -> CLUST-1 -> CLUST-2 -> CLUST-3 -> GEN-1 -> GEN-2 -> GEN-3 -> Publisher

Fixed with asyncio-based execution to prevent subprocess hanging issues.
"""

import argparse
import asyncio
import datetime
import os
import shlex
import sys
from pathlib import Path

# Add project root to path for pipeline config
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from etl_pipeline.core.pipeline_config import (get, get_window_config,
                                               get_windows_summary)


def display_pipeline_configuration(verbose=True):
    """Display current pipeline window configuration"""
    if not verbose:
        return

    print("=" * 60)
    print("PIPELINE WINDOW CONFIGURATION")
    print("=" * 60)

    # Load configuration summary
    summary = get_windows_summary()

    print(f"Environment: {summary.get('environment', 'unknown')}")
    print()
    print("STAGE WINDOWS:")
    print(f"  Keywords:          {summary.get('keywords_window_hours', 'N/A')}h")
    print(f"  CLUST-1:          {summary.get('clust1_window_hours', 'N/A')}h")
    print(f"  CLUST-2:          {summary.get('clust2_window_hours', 'N/A')}h")
    print(f"  CLUST-3:          {summary.get('clust3_candidate_window_hours', 'N/A')}h")
    print(f"  Library:          {summary.get('library_lib_window_days', 'N/A')} days")
    print(f"  Strategic Filter: {summary.get('strategic_filter_window_hours', 'N/A')}h")
    print(f"  Publisher Evidence: {summary.get('publisher_evidence_days', 'N/A')} days")
    print(f"  Publisher Parent: {summary.get('publisher_parent_days', 'N/A')} days")
    print()
    print("STAGE LIMITS:")
    print(f"  CLUST-2:          {get('clust2.limit', 10)} narratives")
    print(
        f"  GEN-1:            {get('gen1.limit', 10)} limit ({'enabled' if get('gen1.enabled', True) else 'disabled'})"
    )
    print(
        f"  GEN-2:            {get('gen2.limit', 10)} limit ({'enabled' if get('gen2.enabled', True) else 'disabled'})"
    )
    print(
        f"  GEN-3:            {get('gen3.limit', 10)} limit ({'enabled' if get('gen3.enabled', True) else 'disabled'})"
    )
    print()


# Load environment variables from .env file
def load_dotenv():
    """Load environment variables from .env file"""
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_pipeline_steps():
    """Generate pipeline steps using centralized configuration"""
    return [
        ("RSS_INGESTION", "python rss_ingestion.py --incremental"),
        (
            "FULLTEXT_ENHANCEMENT",
            "python etl_pipeline/ingestion/fetch_fulltext.py --window 0",
        ),
        (
            "KEYWORD_EXTRACTION",
            f"python etl_pipeline/keywords/extract_keywords.py --window {get('keywords.window_hours', 72)} --mode {get('keywords.mode', 'auto')}",
        ),
        (
            "CANONICALIZATION",
            "python etl_pipeline/keywords/update_keyword_canon_from_db.py",
        ),
        ("CLUST0_REFRESH", "python scripts/refresh_event_signals_pipeline.py"),
        (
            "CLUST1_CLUSTERING",
            f"python etl_pipeline/clustering/clust1_taxonomy_graph.py --mode pipeline --window {get('clust1.window_hours', 72)} --profile {get('clust1.profile', 'strict')} --use_hub_assist {int(get('clust1.use_hub_assist', True))} --hub_pair_cos {get('clust1.hub_pair_cos', 0.90)} --macro_enable 1",
        ),
        (
            "CLUST2_NARRATIVES",
            f"python etl_pipeline/clustering/clust2_interpretive_clustering.py --limit {get('clust2.limit', 10)}",
        ),
        (
            "CLUST3_CONSOLIDATION",
            f"python etl_pipeline/clust3_consolidate.py --window-days {get('clust3.candidate_window_hours', 72) // 24} --library-days {get('clust3.library_days', 90)} --cos-min {get('clust3.similarity_threshold', 0.82)} --tok-jacc-min {get('clust3.jaccard_threshold', 0.40)}",
        ),
        (
            "GEN1_CARD_GENERATION",
            (
                f"python etl_pipeline/generation/gen1_card.py --limit {get('gen1.limit', 10)}"
                if get("gen1.enabled", True)
                else None
            ),
        ),
        (
            "GEN2_ENRICHMENT",
            (
                f"python etl_pipeline/generation/gen2_enrichment.py --limit {get('gen2.limit', 10)}"
                if get("gen2.enabled", True)
                else None
            ),
        ),
        (
            "GEN3_RAI_OVERLAY",
            (
                f"python etl_pipeline/generation/gen3_rai_overlay.py --limit {get('gen3.limit', 10)}"
                if get("gen3.enabled", True)
                else None
            ),
        ),
        (
            "PUBLISHER",
            f"python generation/publisher.py --evidence-days {get('publisher.evidence_days', 7)} --parent-days {get('publisher.parent_days', 14)} --min-articles {get('publisher.min_articles', 4)} --min-sources {get('publisher.min_sources', 3)} --entropy-max {get('publisher.entropy_max', 2.40)}",
        ),
    ]


async def run_step(cmd, name, timeout=1800, verbose=True):
    """Run a single pipeline step with streaming output and timeout"""
    if verbose:
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting {name}: {cmd}",
            flush=True,
        )

    start_time = datetime.datetime.now()

    try:
        # Create subprocess with asyncio
        proc = await asyncio.create_subprocess_exec(
            *shlex.split(cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ.copy(),
        )

        # Stream output without readline timeout - let process complete naturally
        async def stream_output():
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                if verbose:
                    sys.stdout.write(line.decode(errors="ignore"))
                    sys.stdout.flush()

        # Run output streaming and process together with overall timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(stream_output(), proc.wait()), timeout=timeout
            )
        except asyncio.TimeoutError:
            # Only kill process if it exceeds the full step timeout
            proc.kill()
            await proc.wait()
            duration = datetime.datetime.now() - start_time
            raise RuntimeError(
                f"{name} timed out after {duration.total_seconds():.1f}s"
            )

        # Get process exit code and duration
        rc = proc.returncode
        duration = datetime.datetime.now() - start_time

        if rc != 0:
            raise RuntimeError(
                f"{name} failed with exit code {rc} after {duration.total_seconds():.1f}s"
            )

        if verbose:
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {name} completed successfully in {duration.total_seconds():.1f}s",
                flush=True,
            )

        return True, duration.total_seconds()

    except Exception as e:
        duration = datetime.datetime.now() - start_time
        if verbose:
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {name} FAILED: {e}",
                flush=True,
            )
        return False, duration.total_seconds()


async def run_complete_pipeline(auto_mode=True, verbose=True):
    """Execute the complete 12-step SNI pipeline with asyncio"""

    # Get pipeline steps with configuration
    steps = [(name, cmd) for name, cmd in get_pipeline_steps() if cmd is not None]

    if verbose:
        # Display configuration before starting
        display_pipeline_configuration(verbose)

        print("=" * 60)
        print("STARTING COMPLETE SNI PIPELINE")
        print("=" * 60)
        print(f"Timestamp: {datetime.datetime.now()}")
        print(
            f"Mode: {'AUTO (continue on errors)' if auto_mode else 'MANUAL (stop on first error)'}"
        )
        print(f"Total steps: {len(steps)}")
        print()

    start_time = datetime.datetime.now()
    success_count = 0
    results = {}

    for step_num, (name, cmd) in enumerate(steps, 1):
        if verbose:
            print(f"{'='*20} STEP {step_num}/{len(steps)}: {name} {'='*20}")

        try:
            # Set appropriate timeout for each step type
            step_timeout = 1800  # 30 minutes default
            if "KEYWORD_EXTRACTION" in name:
                step_timeout = 2400  # 40 minutes for keyword extraction
            elif "GEN" in name:
                step_timeout = 1200  # 20 minutes for generation steps
            elif "CLUST" in name:
                step_timeout = 1800  # 30 minutes for clustering

            success, duration = await run_step(
                cmd, name, timeout=step_timeout, verbose=verbose
            )
            results[name] = {
                "status": "SUCCESS" if success else "FAILED",
                "duration": duration,
            }

            if success:
                success_count += 1
                if verbose:
                    print(
                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step {step_num} SUCCESS: {name}"
                    )
            else:
                if not auto_mode:
                    if verbose:
                        print(f"Manual mode: Stopping pipeline due to {name} failure")
                    break
                if verbose:
                    print(
                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step {step_num} FAILED: {name} (continuing in auto mode)"
                    )

        except Exception as e:
            results[name] = {"status": "ERROR", "duration": 0, "error": str(e)}
            if verbose:
                print(
                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step {step_num} ERROR: {name}: {e}"
                )

            if not auto_mode:
                if verbose:
                    print(f"Manual mode: Stopping pipeline due to {name} error")
                break
            if verbose:
                print(f"Auto mode: Continuing despite {name} error")

    # Final summary
    total_time = datetime.datetime.now() - start_time

    if verbose:
        print()
        print("=" * 60)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total execution time: {total_time.total_seconds()/60:.1f} minutes")
        print(f"Steps completed successfully: {success_count}/{len(steps)}")
        print(f"Success rate: {success_count/len(steps)*100:.1f}%")
        print()
        print("Step-by-step results:")
        for step_name, result in results.items():
            status = result["status"]
            duration = result.get("duration", 0)
            print(f"  {step_name}: {status} ({duration:.1f}s)")
        print()

        if success_count == len(steps):
            print("PIPELINE COMPLETED SUCCESSFULLY!")
        elif success_count > 0:
            print(
                f"PIPELINE PARTIALLY COMPLETED: {success_count}/{len(steps)} steps successful"
            )
        else:
            print("PIPELINE FAILED: No steps completed successfully")

    return success_count > 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Complete 12-Step SNI Pipeline Runner (Asyncio-based)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    parser.add_argument(
        "--auto", action="store_true", help="Run in automatic mode (continue on errors)"
    )

    parser.add_argument(
        "--manual", action="store_true", help="Run in manual mode (stop on first error)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Determine mode
    auto_mode = args.auto or not args.manual  # Default to auto mode
    verbose = not args.quiet

    # Run complete pipeline using asyncio
    try:
        success = asyncio.run(
            run_complete_pipeline(auto_mode=auto_mode, verbose=verbose)
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
