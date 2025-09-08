#!/usr/bin/env python3
"""
Complete SNI Pipeline Runner
Executes the Strategic Narrative Intelligence pipeline in the correct order:
RSS -> Full-text -> Keywords -> Canonicalize -> CLUST-0 -> CLUST-1 -> CLUST-2 -> CLUST-3 -> Publisher

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

from etl_pipeline.core.pipeline_config import get, get_windows_summary


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
    print("STAGE WINDOWS (matching operational spec):")
    print(f"  Keywords:          {summary.get('keywords_window_hours', 'N/A')}h")
    print(f"  Library (vocab):   {summary.get('library_lib_window_days', 'N/A')} days")
    print(
        f"  Strategic Filter:  {summary.get('strategic_filter_window_hours', 'N/A')}h"
    )
    print(f"  CLUST-1:          {summary.get('clust1_window_hours', 'N/A')}h")
    print(f"  CLUST-2:          {summary.get('clust2_window_hours', 'N/A')}h")
    print(
        f"  CLUST-3:          {summary.get('clust3_candidate_window_hours', 'N/A')}h (candidates only)"
    )
    print(f"  Publisher Evidence: {summary.get('publisher_evidence_days', 'N/A')} days")
    print(f"  Publisher Parent:  {summary.get('publisher_parent_days', 'N/A')} days")
    print()
    print("GENERATION PIPELINE:")
    print(
        f"  GEN-1:            {'enabled' if get('gen1.enabled', True) else 'disabled'}"
    )
    print(
        f"  GEN-2:            {'enabled' if get('gen2.enabled', True) else 'disabled'}"
    )
    print(
        f"  GEN-3:            {'enabled' if get('gen3.enabled', True) else 'disabled'} (RAI: {'enabled' if get('gen3.rai.enabled', True) else 'disabled'})"
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


# Use existing CLUST-0 refresh script - no need for individual steps

def get_pipeline_steps():
    """Generate pipeline steps according to specification"""
    return [
        (
            "RSS_INGESTION",
            "python rss_ingestion.py --incremental",
        ),
        (
            "FULLTEXT_ENHANCEMENT",
            "python etl_pipeline/ingestion/fetch_fulltext.py --window 0",
        ),
        (
            "KEYWORD_EXTRACTION",
            "python etl_pipeline/keywords/extract_keywords.py --window 72 --mode auto",
        ),
        (
            "CANONICALIZATION",
            "python etl_pipeline/keywords/update_keyword_canon_from_db_v2.py --window 72",
        ),
        (
            "CLUST0_REFRESH",
            "python etl_pipeline/clustering/clust0_refresh_event_signals.py",
        ),
        (
            "CLUST1_CLUSTERING",
            "python etl_pipeline/clustering/clust1_taxonomy_graph.py --mode pipeline --window 72 --profile strict --use_hub_assist 1 --hub_pair_cos 0.90 --macro_enable 1",
        ),
        (
            "CLUST2_NARRATIVES",
            "python etl_pipeline/clustering/clust2_interpretive_clustering.py --window 72 --only_final 1",
        ),
        (
            "CLUST3_CONSOLIDATION",
            "python etl_pipeline/clustering/clust3_consolidate.py --window_days 14 --library_days 90 --cos_min 0.82 --tok_jacc_min 0.40",
        ),
        (
            "GEN1_CARDS",
            "python generation/gen1_card.py --batch 20",
        ),
        (
            "GEN2_ENRICHMENT", 
            "python generation/gen2_enrichment.py --batch 20",
        ),
        (
            "GEN3_RAI_OVERLAY",
            "python generation/gen3_rai_overlay.py --batch 20",
        ),
        (
            "PUBLISHER",
            "python generation/publisher.py --evidence-days 7 --parent-days 14 --min-articles 4 --min-sources 3 --entropy-max 2.40",
        ),
    ]


def extract_kpis_from_output(output: str, step_name: str) -> dict:
    """Extract KPIs from step output"""
    kpis = {}
    
    # Common patterns for different steps
    if "RSS_INGESTION" in step_name:
        # Look for ingestion metrics
        import re
        if match := re.search(r'([0-9,]+) total articles', output):
            kpis['total_articles'] = match.group(1)
        if match := re.search(r'([0-9,]+) new articles added', output):
            kpis['new_articles'] = match.group(1)
            
    elif "KEYWORD_EXTRACTION" in step_name:
        # Look for extraction metrics
        if match := re.search(r'([0-9,]+) articles processed', output):
            kpis['articles_processed'] = match.group(1)
        if match := re.search(r'([0-9,]+) total keywords extracted', output):
            kpis['keywords_extracted'] = match.group(1)
            
    elif "CLUST1" in step_name:
        # Look for clustering metrics
        if match := re.search(r'([0-9,]+) clusters created', output):
            kpis['clusters_created'] = match.group(1)
        if match := re.search(r'([0-9,]+) articles clustered', output):
            kpis['articles_clustered'] = match.group(1)
            
    elif "CLUST2" in step_name:
        # Look for narrative metrics  
        if match := re.search(r'([0-9,]+) narratives generated', output):
            kpis['narratives_generated'] = match.group(1)
            
    elif "CLUST3" in step_name:
        # Look for consolidation metrics
        if match := re.search(r'([0-9,]+) candidates processed', output):
            kpis['candidates_processed'] = match.group(1)
        if match := re.search(r'([0-9,]+) narratives merged', output):
            kpis['narratives_merged'] = match.group(1)
            
    elif "GEN1_CARDS" in step_name:
        # Look for card generation metrics
        if match := re.search(r'Processed: ([0-9,]+) narratives', output):
            kpis['narratives_processed'] = match.group(1)
        if match := re.search(r'Successful: ([0-9,]+) cards generated', output):
            kpis['cards_generated'] = match.group(1)
        if match := re.search(r'Success Rate: ([0-9.]+)%', output):
            kpis['gen1_success_rate'] = match.group(1) + '%'
            
    elif "GEN2_ENRICHMENT" in step_name:
        # Look for enrichment metrics
        if match := re.search(r'Processed: ([0-9,]+) narratives', output):
            kpis['narratives_enriched'] = match.group(1)
        if match := re.search(r'Successful: ([0-9,]+) enrichments', output):
            kpis['enrichments_completed'] = match.group(1)
        if match := re.search(r'Success Rate: ([0-9.]+)%', output):
            kpis['gen2_success_rate'] = match.group(1) + '%'
            
    elif "GEN3_RAI_OVERLAY" in step_name:
        # Look for RAI analysis metrics
        if match := re.search(r'Processed: ([0-9,]+) narratives', output):
            kpis['narratives_analyzed'] = match.group(1)
        if match := re.search(r'Successful: ([0-9,]+) analyses', output):
            kpis['rai_analyses_completed'] = match.group(1)
        if match := re.search(r'Service Unavailable: ([0-9,]+) fallbacks', output):
            kpis['rai_fallbacks'] = match.group(1)
        if match := re.search(r'Success Rate: ([0-9.]+)%', output):
            kpis['gen3_success_rate'] = match.group(1) + '%'
        if match := re.search(r'RAI Service Enabled: (True|False)', output):
            kpis['rai_service_enabled'] = match.group(1)
    
    elif "PUBLISHER" in step_name:
        # Look for publication metrics
        if match := re.search(r'Candidates reviewed: ([0-9,]+)', output):
            kpis['candidates_reviewed'] = match.group(1)
        if match := re.search(r'Promoted to published: ([0-9,]+)', output):
            kpis['published'] = match.group(1)
        if match := re.search(r'Publication success rate: ([0-9.]+)%', output):
            kpis['success_rate'] = match.group(1) + '%'
    
    return kpis

async def run_step(cmd, name, timeout=1800, verbose=True, kpi_only=False):
    """Run a single pipeline step with streaming output, timeout, and KPI extraction"""
    if verbose:
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting {name}: {cmd}",
            flush=True,
        )

    start_time = datetime.datetime.now()
    output_buffer = []

    try:
        # Create subprocess with asyncio
        proc = await asyncio.create_subprocess_exec(
            *shlex.split(cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ.copy(),
        )

        # Stream output and capture for KPI extraction
        async def stream_output():
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                line_str = line.decode(errors="ignore")
                output_buffer.append(line_str)
                if verbose and not kpi_only:
                    sys.stdout.write(line_str)
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

        # Extract KPIs from captured output
        full_output = ''.join(output_buffer)
        kpis = extract_kpis_from_output(full_output, name)
        
        if verbose or kpi_only:
            if kpi_only and kpis:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {name} KPIs: {', '.join(f'{k}={v}' for k, v in kpis.items())}")
            elif verbose:
                print(
                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {name} completed successfully in {duration.total_seconds():.1f}s",
                    flush=True,
                )
                if kpis:
                    print(f"  KPIs: {', '.join(f'{k}={v}' for k, v in kpis.items())}")

        return True, duration.total_seconds(), kpis

    except Exception as e:
        duration = datetime.datetime.now() - start_time
        if verbose and not kpi_only:
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {name} FAILED: {e}",
                flush=True,
            )
        elif kpi_only:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {name} FAILED: {e}")
        return False, duration.total_seconds(), {}


async def run_complete_pipeline(auto_mode=True, verbose=True, kpi_only=False, step_by_step=False, background=False):
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
        print("Pipeline order: RSS -> Full-text -> Keywords -> Canonicalize -> CLUST-0 -> CLUST-1 -> CLUST-2 -> CLUST-3 -> Publisher")
        print()

    start_time = datetime.datetime.now()
    success_count = 0
    results = {}

    for step_num, (name, cmd) in enumerate(steps, 1):
        if verbose:
            print(f"{'='*20} STEP {step_num}/{len(steps)}: {name} {'='*20}")

        # Step-by-step confirmation
        if step_by_step:
            print(f"\nAbout to run: {name}")
            print(f"Command: {cmd}")
            response = input(f"\nProceed with {name}? (y/n/skip): ").strip().lower()
            if response == 'n':
                print("Pipeline stopped by user")
                break
            elif response == 'skip':
                print(f"Skipping {name}")
                continue
            elif response != 'y':
                print("Invalid response, skipping step")
                continue

        try:
            # Set appropriate timeout for each step type
            step_timeout = 1800  # 30 minutes default
            if "KEYWORD_EXTRACTION" in name:
                step_timeout = 2400  # 40 minutes for keyword extraction
            elif "GEN" in name:
                step_timeout = 1200  # 20 minutes for generation steps
            elif "CLUST" in name:
                step_timeout = 1800  # 30 minutes for clustering
            
            # Background mode: increase timeouts significantly to avoid interruptions
            if background:
                step_timeout = step_timeout * 3  # Triple the timeout for background execution
                if verbose:
                    print(f"[BACKGROUND MODE] Extended timeout to {step_timeout//60} minutes")

            success, duration, kpis = await run_step(
                cmd, name, timeout=step_timeout, verbose=verbose, kpi_only=kpi_only
            )
            results[name] = {
                "status": "SUCCESS" if success else "FAILED",
                "duration": duration,
                "kpis": kpis,
            }

            if success:
                success_count += 1
                if verbose and not kpi_only:
                    print(
                        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step {step_num} SUCCESS: {name}"
                    )
                elif kpi_only:
                    status_msg = f"Step {step_num} SUCCESS: {name}"
                    if kpis:
                        status_msg += f" | KPIs: {', '.join(f'{k}={v}' for k, v in kpis.items())}"
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {status_msg}")
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
            results[name] = {"status": "ERROR", "duration": 0, "kpis": {}, "error": str(e)}
            if verbose and not kpi_only:
                print(
                    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step {step_num} ERROR: {name}: {e}"
                )
            elif kpi_only:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step {step_num} ERROR: {name}: {e}")

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
            kpis = result.get("kpis", {})
            kpi_str = f" | KPIs: {', '.join(f'{k}={v}' for k, v in kpis.items())}" if kpis else ""
            print(f"  {step_name}: {status} ({duration:.1f}s){kpi_str}")
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
        description="Complete SNI Pipeline Runner with CLUST-0/1/2/3 (Asyncio-based)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    
    parser.add_argument("--kpi-only", action="store_true", help="Only print KPIs for each step")

    parser.add_argument(
        "--auto", action="store_true", help="Run in automatic mode (continue on errors)"
    )

    parser.add_argument(
        "--manual", action="store_true", help="Run in manual mode (stop on first error)"
    )

    parser.add_argument(
        "--step-by-step", action="store_true", help="Run pipeline step-by-step with user confirmation"
    )

    parser.add_argument(
        "--background", action="store_true", help="Run long-running steps in background to avoid timeouts"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Determine mode
    auto_mode = args.auto or not args.manual  # Default to auto mode
    verbose = not args.quiet
    kpi_only = args.kpi_only
    step_by_step = args.step_by_step
    background = args.background

    # Run complete pipeline using asyncio
    try:
        success = asyncio.run(
            run_complete_pipeline(
                auto_mode=auto_mode, 
                verbose=verbose, 
                kpi_only=kpi_only,
                step_by_step=step_by_step,
                background=background
            )
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
