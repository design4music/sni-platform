#!/usr/bin/env python3
"""
Apply batch-aware library fix to address unfair token frequency calculations.
This script executes the SQL updates and reruns CLUST-1 pipeline.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_sql_file(sql_file):
    """Execute a SQL file using psql command."""
    cmd = f"psql narrative_intelligence -f {sql_file}"
    print(f"Executing: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error executing {sql_file}:")
            print(result.stderr)
            return False
        else:
            print(f"Successfully executed {sql_file}")
            return True
    except Exception as e:
        print(f"Exception running {sql_file}: {e}")
        return False


def refresh_materialized_views():
    """Refresh the materialized views."""
    views = [
        "shared_keywords_lib_norm_30d",
        "article_core_keywords",
        "keyword_hubs_30d",
    ]

    for view in views:
        cmd = f'psql narrative_intelligence -c "REFRESH MATERIALIZED VIEW {view};"'
        print(f"Refreshing {view}...")

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error refreshing {view}: {result.stderr}")
                return False
            else:
                print(f"Successfully refreshed {view}")
        except Exception as e:
            print(f"Exception refreshing {view}: {e}")
            return False

    return True


def run_clustering_pipeline():
    """Run the CLUST-1 pipeline stages."""
    scripts_dir = Path(__file__).parent.parent
    clustering_script = (
        scripts_dir / "etl_pipeline" / "clustering" / "clust1_taxonomy_graph.py"
    )

    if not clustering_script.exists():
        print(f"Clustering script not found at: {clustering_script}")
        return False

    stages = [
        [
            "python",
            str(clustering_script),
            "--stage",
            "seed",
            "--window",
            "300",
            "--min_size",
            "3",
            "--min_sources",
            "2",
        ],
        [
            "python",
            str(clustering_script),
            "--stage",
            "densify",
            "--window",
            "300",
            "--cos",
            "0.88",
            "--min_shared",
            "2",
            "--alt_rule",
            "1_shared+cos>=0.88",
        ],
        ["python", str(clustering_script), "--stage", "persist"],
    ]

    for stage_cmd in stages:
        print(f"Running: {' '.join(stage_cmd)}")
        try:
            result = subprocess.run(stage_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error in clustering stage: {result.stderr}")
                return False
            else:
                print(f"Successfully completed stage: {stage_cmd[3]}")
                print(result.stdout)
        except Exception as e:
            print(f"Exception running clustering stage: {e}")
            return False

    return True


def main():
    """Main execution function."""
    scripts_dir = Path(__file__).parent

    sql_files = [
        scripts_dir / "create_batch_aware_library.sql",
        scripts_dir / "update_core_keywords_normalized.sql",
        scripts_dir / "update_fair_hubs.sql",
    ]

    print("=== Applying Batch-Aware Library Fix ===")

    # Step 1: Execute SQL files
    print("\n1. Creating batch-aware materialized views...")
    for sql_file in sql_files:
        if not sql_file.exists():
            print(f"SQL file not found: {sql_file}")
            return 1

        if not run_sql_file(sql_file):
            print(f"Failed to execute {sql_file}")
            return 1

    # Step 2: Refresh materialized views
    print("\n2. Refreshing materialized views...")
    if not refresh_materialized_views():
        print("Failed to refresh materialized views")
        return 1

    # Step 3: Run clustering pipeline
    print("\n3. Running CLUST-1 pipeline...")
    if not run_clustering_pipeline():
        print("Failed to run clustering pipeline")
        return 1

    print("\n=== Batch-Aware Fix Applied Successfully ===")
    print("Expected improvements:")
    print("- Coverage should climb back (batch bias removed)")
    print("- Missing topics (tariffs/sanctions/Ukraine/India oil) should reappear")
    print("- Purity should remain ~unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
