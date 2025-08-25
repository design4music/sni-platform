#!/usr/bin/env python3
"""
Test script for 72h window comparison with event signals enhancement
Control vs Treatment testing for Phase A + Event Signals
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def clear_clusters(conn):
    """Clear existing clusters for clean testing."""
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM article_cluster_members")
        cur.execute("DELETE FROM article_clusters")
        conn.commit()
        logger.info("Cleared existing clusters for clean testing")
    finally:
        cur.close()


def run_clustering(use_hub_assist=0, window=72, hub_pair_cos=0.92):
    """Run CLUST-1 clustering with specified parameters."""
    logger.info(
        f"Running clustering: hub_assist={use_hub_assist}, window={window}h, hub_pair_cos={hub_pair_cos}"
    )

    try:
        # Run the clustering pipeline
        cmd = [
            "python",
            "etl_pipeline/clustering/clust1_taxonomy_graph.py",
            "--stage",
            "persist",
            "--window",
            str(window),
            "--cos",
            "0.86",
            "--lang",
            "EN",
            "--use_hub_assist",
            str(use_hub_assist),
            "--macro_enable",
            "1",
            "--hub_pair_cos",
            str(hub_pair_cos),
            "--hub_only_cap",
            "0.25",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode != 0:
            logger.error(f"Clustering failed: {result.stderr}")
            return None

        logger.info("Clustering completed successfully")
        return result.stdout

    except Exception as e:
        logger.error(f"Failed to run clustering: {e}")
        return None


def get_clustering_metrics(conn):
    """Get detailed clustering metrics from database."""
    cur = conn.cursor()
    try:
        # Get strategic candidate count for context (estimate from articles)
        cur.execute(
            """
            SELECT COUNT(DISTINCT a.id) 
            FROM articles a
            WHERE a.language = 'EN' 
              AND a.published_at >= NOW() - INTERVAL '72 hours'
        """
        )
        strategic_candidates = cur.fetchone()[0] or 0

        # Get cluster metrics
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_clusters,
                COUNT(*) FILTER (WHERE cluster_type = 'final') as final_clusters,
                COUNT(*) FILTER (WHERE cluster_type = 'macro') as macro_clusters,
                ROUND((100.0 * COUNT(*) FILTER (WHERE cluster_type = 'macro') / GREATEST(COUNT(*), 1))::numeric, 1) as macro_pct
            FROM article_clusters
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """
        )
        cluster_stats = cur.fetchone()

        # Get member metrics (simplified for recent clusters)
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_members,
                COUNT(DISTINCT article_id) as unique_articles,
                CASE WHEN COUNT(*) > 0 THEN ROUND((COUNT(*)::float / COUNT(DISTINCT cluster_id))::numeric, 1) ELSE 0 END as avg_cluster_size
            FROM article_cluster_members acm
            WHERE acm.cluster_id IN (
                SELECT cluster_id FROM article_clusters 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            )
        """
        )
        member_stats = cur.fetchone()

        # Calculate clustering percentage over strategic candidates
        clustered_pct = 0
        if strategic_candidates > 0 and member_stats and member_stats[1]:
            clustered_pct = round(100.0 * member_stats[1] / strategic_candidates, 1)

        # Calculate entropy for final clusters only (simplified)
        cur.execute(
            """
            SELECT 
                CASE WHEN COUNT(*) > 0 THEN 
                    ROUND(AVG(-1 * sizes.size_ratio * LN(sizes.size_ratio))::numeric, 2)
                ELSE 0 END as final_entropy
            FROM (
                SELECT 
                    acm.cluster_id,
                    COUNT(*)::float / SUM(COUNT(*)) OVER () as size_ratio
                FROM article_cluster_members acm
                WHERE acm.cluster_id IN (
                    SELECT cluster_id FROM article_clusters 
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                      AND cluster_type = 'final'
                )
                GROUP BY acm.cluster_id
            ) sizes
        """
        )
        entropy_result = cur.fetchone()

        return {
            "strategic_candidates": strategic_candidates,
            "total_clusters": cluster_stats[0] if cluster_stats[0] else 0,
            "final_clusters": cluster_stats[1] if cluster_stats[1] else 0,
            "macro_clusters": cluster_stats[2] if cluster_stats[2] else 0,
            "macro_pct": float(cluster_stats[3]) if cluster_stats[3] else 0,
            "total_members": member_stats[0] if member_stats[0] else 0,
            "unique_articles": member_stats[1] if member_stats[1] else 0,
            "avg_cluster_size": float(member_stats[2]) if member_stats[2] else 0,
            "clustered_pct": clustered_pct,
            "final_entropy": float(entropy_result[0]) if entropy_result[0] else 0,
        }

    finally:
        cur.close()


def main():
    """Run 72h window test comparison."""
    parser = argparse.ArgumentParser(description="Test 72h window with event signals")
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument(
        "--hub-pair-cos",
        type=float,
        default=0.92,
        help="Hub pair cosine threshold (default: 0.92)",
    )

    args = parser.parse_args()

    logger.info("Starting 72h window test: Control vs Treatment")

    try:
        conn = get_db_connection()

        # Test configurations
        tests = [
            {"name": "Control (Strict)", "hub_assist": 0},
            {"name": "Treatment (Hub-Assist + Event Signals)", "hub_assist": 1},
        ]

        results = {}

        for test in tests:
            logger.info(f"\n=== Running: {test['name']} ===")

            # Clear clusters for each test
            clear_clusters(conn)

            # Small delay to ensure clean state
            time.sleep(2)

            # Run clustering
            output = run_clustering(
                use_hub_assist=test["hub_assist"],
                window=args.window,
                hub_pair_cos=args.hub_pair_cos,
            )

            if output is None:
                logger.warning(f"Test failed: {test['name']}")
                continue

            # Get metrics from database
            metrics = get_clustering_metrics(conn)
            results[test["name"]] = metrics

            logger.info(f"Results: {metrics}")

        # Print comparison report
        print("\n" + "=" * 80)
        print(f"72H WINDOW TEST RESULTS: Event Signals Enhancement")
        print("=" * 80)

        if len(results) >= 2:
            control = list(results.values())[0]
            treatment = list(results.values())[1]

            print(f"\nBaseline Data ({args.window}h window):")
            print(f"  Strategic candidates: {control['strategic_candidates']:,}")

            print(f"\nClustering Results:")
            print(f"{'Metric':<25} {'Control':<15} {'Treatment':<15} {'Delta':<15}")
            print("-" * 70)

            # Key metrics
            metrics_to_compare = [
                ("Final clusters", "final_clusters"),
                ("Macro clusters", "macro_clusters"),
                ("Macro %", "macro_pct"),
                ("Unique articles", "unique_articles"),
                ("Clustered %", "clustered_pct"),
                ("Final entropy", "final_entropy"),
                ("Avg cluster size", "avg_cluster_size"),
            ]

            for label, key in metrics_to_compare:
                control_val = control[key]
                treatment_val = treatment[key]

                if key in ["macro_pct", "clustered_pct", "final_entropy"]:
                    delta = f"{treatment_val - control_val:+.1f}"
                else:
                    delta = f"{treatment_val - control_val:+.0f}"

                print(
                    f"{label:<25} {control_val:<15.1f} {treatment_val:<15.1f} {delta:<15}"
                )

            # Acceptance criteria check
            print(f"\nAcceptance Criteria Analysis:")
            print(f"Target: +3-8pp clustering rate, entropy ≤2.40, macro ≤20-30%")

            clustering_boost = treatment["clustered_pct"] - control["clustered_pct"]
            entropy_ok = treatment["final_entropy"] <= 2.40
            macro_ok = treatment["macro_pct"] <= 30.0

            print(
                f"  Clustering rate: {control['clustered_pct']:.1f}% → {treatment['clustered_pct']:.1f}% (Δ{clustering_boost:+.1f}pp) {'✓' if clustering_boost >= 3 else '✗'}"
            )
            print(
                f"  Final entropy: {treatment['final_entropy']:.2f} {'✓' if entropy_ok else '✗'} ≤2.40"
            )
            print(
                f"  Macro rate: {treatment['macro_pct']:.1f}% {'✓' if macro_ok else '✗'} ≤30%"
            )

            if clustering_boost >= 3 and entropy_ok and macro_ok:
                print(
                    f"\n✅ ACCEPTANCE CRITERIA MET - Event signals enhancement working!"
                )
            else:
                print(f"\n❌ Acceptance criteria not yet met - Need further refinement")

    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
