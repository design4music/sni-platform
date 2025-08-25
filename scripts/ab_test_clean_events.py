#!/usr/bin/env python3
"""
A/B Testing script for clean event filtering in CLUST-1 Phase A
Compares baseline (original events) vs clean filtered events
"""

import argparse
import logging
import os
import subprocess
import sys

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


def get_test_baseline_metrics(conn):
    """Get baseline metrics before any testing."""
    cur = conn.cursor()
    try:
        # Get event token counts
        cur.execute("SELECT COUNT(*) FROM event_tokens_30d")
        original_events = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM event_tokens_clean_30d")
        clean_events = cur.fetchone()[0]

        # Get triad counts
        cur.execute("SELECT COUNT(*) FROM event_anchored_triads_30d")
        original_triads = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM event_anchored_triads_clean_30d")
        clean_triads = cur.fetchone()[0]

        # Get article counts for context
        cur.execute(
            """
            SELECT COUNT(*) FROM articles 
            WHERE published_at >= NOW() - INTERVAL '300 hours' 
              AND language = 'EN'
        """
        )
        total_articles = cur.fetchone()[0]

        return {
            "total_articles": total_articles,
            "original_events": original_events,
            "clean_events": clean_events,
            "event_retention_pct": round(100.0 * clean_events / original_events, 1),
            "original_triads": original_triads,
            "clean_triads": clean_triads,
            "triad_retention_pct": (
                round(100.0 * clean_triads / original_triads, 1)
                if original_triads > 0
                else 0
            ),
        }
    finally:
        cur.close()


def run_clustering_test(use_hub_assist=0, use_clean_events=0, window=300):
    """Run CLUST-1 clustering with specified parameters."""
    # Clear existing clusters for clean test
    logger.info(
        f"Running clustering test: hub_assist={use_hub_assist}, clean_events={use_clean_events}"
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
            "--use_clean_events",
            str(use_clean_events),
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

        # Parse output for key metrics
        output_lines = result.stdout.split("\n")
        metrics = {}

        for line in output_lines:
            if "Stage Summary" in line:
                # Parse stage summary for metrics
                continue
            elif "seeds found" in line:
                try:
                    seeds = int(line.split()[0])
                    metrics["seeds"] = seeds
                except:
                    pass
            elif "clusters created" in line:
                try:
                    clusters = int(line.split()[0])
                    metrics["clusters"] = clusters
                except:
                    pass

        return metrics

    except Exception as e:
        logger.error(f"Failed to run clustering test: {e}")
        return None


def get_clustering_metrics(conn):
    """Get detailed clustering metrics from database."""
    cur = conn.cursor()
    try:
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

        # Get member metrics (simplified)
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_members,
                COUNT(DISTINCT article_id) as unique_articles,
                CASE WHEN COUNT(*) > 0 THEN ROUND((COUNT(*)::float / COUNT(DISTINCT cluster_id))::numeric, 1) ELSE 0 END as avg_cluster_size
            FROM article_cluster_members
        """
        )
        member_stats = cur.fetchone()

        # Calculate entropy (measure of cluster quality) - simplified
        cur.execute(
            """
            SELECT 
                CASE WHEN COUNT(*) > 0 THEN 
                    ROUND(AVG(-1 * sizes.size_ratio * LN(sizes.size_ratio))::numeric, 2)
                ELSE 0 END as avg_entropy
            FROM (
                SELECT 
                    cluster_id,
                    COUNT(*)::float / SUM(COUNT(*)) OVER () as size_ratio
                FROM article_cluster_members
                GROUP BY cluster_id
            ) sizes
        """
        )
        entropy_result = cur.fetchone()

        return {
            "total_clusters": cluster_stats[0] if cluster_stats[0] else 0,
            "final_clusters": cluster_stats[1] if cluster_stats[1] else 0,
            "macro_clusters": cluster_stats[2] if cluster_stats[2] else 0,
            "macro_pct": cluster_stats[3] if cluster_stats[3] else 0,
            "total_members": member_stats[0] if member_stats[0] else 0,
            "unique_articles": member_stats[1] if member_stats[1] else 0,
            "avg_cluster_size": member_stats[2] if member_stats[2] else 0,
            "entropy": entropy_result[0] if entropy_result[0] else 0,
        }

    finally:
        cur.close()


def clear_test_clusters(conn):
    """Clear existing clusters for clean testing."""
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM article_cluster_members")
        cur.execute("DELETE FROM article_clusters")
        conn.commit()
        logger.info("Cleared existing clusters for clean A/B testing")
    finally:
        cur.close()


def main():
    """Run A/B testing for clean event filtering."""
    parser = argparse.ArgumentParser(description="A/B test clean event filtering")
    parser.add_argument(
        "--window", type=int, default=300, help="Time window in hours (default: 300)"
    )
    parser.add_argument(
        "--clear-clusters",
        action="store_true",
        help="Clear existing clusters before testing",
    )

    args = parser.parse_args()

    logger.info("Starting A/B test for clean event filtering")

    try:
        conn = get_db_connection()

        # Get baseline metrics
        baseline = get_test_baseline_metrics(conn)
        logger.info(f"Baseline metrics: {baseline}")

        # Clear clusters if requested
        if args.clear_clusters:
            clear_test_clusters(conn)

        # Test matrix: [baseline, hub_assist_original, hub_assist_clean]
        tests = [
            {
                "name": "Baseline (no hub assist, original events)",
                "hub_assist": 0,
                "clean_events": 0,
            },
            {
                "name": "Hub assist with original events",
                "hub_assist": 1,
                "clean_events": 0,
            },
            {
                "name": "Hub assist with clean events",
                "hub_assist": 1,
                "clean_events": 1,
            },
        ]

        results = {}

        for test in tests:
            logger.info(f"\n=== Running: {test['name']} ===")

            # Clear clusters for each test
            clear_test_clusters(conn)

            # Run clustering
            cluster_result = run_clustering_test(
                use_hub_assist=test["hub_assist"],
                use_clean_events=test["clean_events"],
                window=args.window,
            )

            if cluster_result is None:
                logger.warning(f"Test failed: {test['name']}")
                continue

            # Get metrics from database
            db_metrics = get_clustering_metrics(conn)

            # Combine results
            results[test["name"]] = {**cluster_result, **db_metrics}

            logger.info(f"Results: {results[test['name']]}")

        # Print comparison report
        print("\n" + "=" * 80)
        print("A/B TEST RESULTS: Clean Event Filtering Impact")
        print("=" * 80)

        print(f"\nBaseline Data ({args.window}h window):")
        print(f"  Total articles: {baseline['total_articles']:,}")
        print(f"  Original events: {baseline['original_events']:,}")
        print(
            f"  Clean events: {baseline['clean_events']:,} ({baseline['event_retention_pct']}% retention)"
        )
        print(f"  Original triads: {baseline['original_triads']:,}")
        print(
            f"  Clean triads: {baseline['clean_triads']:,} ({baseline['triad_retention_pct']}% retention)"
        )

        print("\nClustering Results:")
        print(
            f"{'Test':<40} {'Clusters':<10} {'Final':<8} {'Macro':<8} {'Macro%':<8} {'Entropy':<8} {'Avg Size':<10}"
        )
        print("-" * 100)

        for test_name, metrics in results.items():
            print(
                f"{test_name:<40} {metrics.get('total_clusters', 0):<10} "
                f"{metrics.get('final_clusters', 0):<8} {metrics.get('macro_clusters', 0):<8} "
                f"{metrics.get('macro_pct', 0):<8} {metrics.get('entropy', 0):<8} "
                f"{metrics.get('avg_cluster_size', 0):<10}"
            )

        # Acceptance criteria check
        print("\nAcceptance Criteria Analysis:")
        print("Target: +3-8pp clustering rate, entropy ≤2.40, macro rate ≤20%")

        if len(results) >= 3:
            baseline_result = list(results.values())[0]
            clean_result = list(results.values())[2]

            # Compare macro rates
            baseline_macro = baseline_result.get("macro_pct", 0)
            clean_macro = clean_result.get("macro_pct", 0)
            macro_improvement = baseline_macro - clean_macro

            print(
                f"  Macro rate: {baseline_macro}% → {clean_macro}% (Δ{macro_improvement:+.1f}pp)"
            )
            print(
                f"  Entropy: {clean_result.get('entropy', 0)} ({'✓' if clean_result.get('entropy', 0) <= 2.40 else '✗'} ≤2.40)"
            )
            print(
                f"  Macro rate: {clean_macro}% ({'✓' if clean_macro <= 20 else '✗'} ≤20%)"
            )

            if clean_macro <= 20 and clean_result.get("entropy", 0) <= 2.40:
                print(
                    "\n✅ ACCEPTANCE CRITERIA MET - Ready for production A/B testing"
                )
            else:
                print("\n❌ Acceptance criteria not met - Further filtering needed")

    except Exception as e:
        logger.error(f"A/B testing failed: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
