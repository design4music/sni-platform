#!/usr/bin/env python3
"""
CLUST-2 Smoke Test: Conservative settings, one level, draft status
Test narrative generation on final clusters only
"""

import argparse
import logging
import os
import subprocess
import sys
import time

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


def get_final_clusters_for_clust2(conn, window=72, min_size=4, min_sources=2):
    """Get final clusters suitable for CLUST-2 processing."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT 
                ac.cluster_id,
                ac.top_topics,
                ac.size,
                COUNT(DISTINCT a.source_name) as source_count,
                array_agg(DISTINCT a.source_name) as sources
            FROM article_clusters ac
            JOIN article_cluster_members acm ON acm.cluster_id = ac.cluster_id
            JOIN articles a ON a.id = acm.article_id
            WHERE ac.created_at >= NOW() - INTERVAL %s
              AND ac.cluster_type = 'final'
              AND ac.size >= %s
            GROUP BY ac.cluster_id, ac.top_topics, ac.size
            HAVING COUNT(DISTINCT a.source_name) >= %s
            ORDER BY ac.size DESC
        """,
            (f"{window} hours", min_size, min_sources),
        )

        clusters = cur.fetchall()
        logger.info(f"Found {len(clusters)} final clusters suitable for CLUST-2")

        for cluster_id, topics, size, source_count, sources in clusters[:5]:
            logger.info(f"  {topics} ({size} articles, {source_count} sources)")

        return clusters

    finally:
        cur.close()


def run_clust2_conservative(window=72):
    """Run CLUST-2 with conservative settings."""
    logger.info("Running CLUST-2 interpretive clustering (conservative mode)")

    # Conservative parameters for smoke test
    conservative_args = [
        "--min_cluster_size",
        "4",  # Minimum cluster size
        "--min_sources",
        "3",  # Minimum source diversity
        "--child_min_size",
        "3",  # Minimum child cluster size
        "--child_min_sources",
        "2",  # Minimum child source diversity
        "--anchor_lift_min",
        "2.0",  # Anchor lift threshold
        "--distinctiveness_max_cosine_to_parent",
        "0.90",  # Parent-child distinctiveness
        "--max_children",
        "2",  # Maximum children per parent
        "--max_depth",
        "1",  # Single level only
        "--require_event_signal",
        "1",  # Require event signals
        "--persist_status",
        "draft",  # Draft status for testing
        "--window",
        str(window),
    ]

    cmd = [
        "python",
        "etl_pipeline/clustering/clust2_interpretive_clustering.py",
    ] + conservative_args

    logger.info(f"CLUST-2 command: {' '.join(cmd[1:])}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        if result.returncode != 0:
            logger.error(f"CLUST-2 failed: {result.stderr}")
            return False

        logger.info("✓ CLUST-2 completed successfully")

        # Log key outputs
        for line in result.stdout.split("\n"):
            if any(
                keyword in line.lower()
                for keyword in ["parent", "child", "narrative", "segment"]
            ):
                logger.info(f"  {line.strip()}")

        return True

    except Exception as e:
        logger.error(f"Failed to run CLUST-2: {e}")
        return False


def get_clust2_results(conn):
    """Get CLUST-2 results for verification."""
    cur = conn.cursor()
    try:
        # Check if narrative tables exist
        cur.execute(
            """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name LIKE '%narrative%'
            ORDER BY table_name
        """
        )
        narrative_tables = [row[0] for row in cur.fetchall()]

        logger.info(f"Available narrative tables: {narrative_tables}")

        if not narrative_tables:
            logger.warning("No narrative tables found - CLUST-2 may not have run yet")
            return None

        # Try to get basic counts from main narrative table
        for table in ["narratives", "article_narratives", "narrative_clusters"]:
            if table in narrative_tables:
                try:
                    cur.execute(
                        f"""
                        SELECT 
                            COUNT(*) as total_narratives,
                            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '2 hours') as recent_narratives
                        FROM {table}
                    """
                    )
                    counts = cur.fetchone()
                    logger.info(
                        f"{table}: {counts[1]} recent narratives ({counts[0]} total)"
                    )
                    return counts
                except Exception as e:
                    logger.warning(f"Could not query {table}: {e}")
                    continue

        return None

    finally:
        cur.close()


def main():
    """Run CLUST-2 smoke test with conservative settings."""
    parser = argparse.ArgumentParser(description="CLUST-2 smoke test")
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=4,
        help="Minimum cluster size (default: 4)",
    )
    parser.add_argument(
        "--min-sources", type=int, default=3, help="Minimum source count (default: 3)"
    )

    args = parser.parse_args()

    logger.info(f"Starting CLUST-2 smoke test (window: {args.window}h)")

    try:
        conn = get_db_connection()

        # Step 1: Check available final clusters
        logger.info("Step 1: Checking available final clusters...")
        clusters = get_final_clusters_for_clust2(
            conn, args.window, args.min_cluster_size, args.min_sources
        )

        if not clusters:
            logger.warning("No suitable final clusters found for CLUST-2")
            return False

        logger.info(f"Found {len(clusters)} clusters suitable for narrative generation")

        # Step 2: Run CLUST-2 with conservative settings
        logger.info("Step 2: Running CLUST-2 interpretive clustering...")
        if not run_clust2_conservative(args.window):
            logger.error("CLUST-2 smoke test failed")
            return False

        # Step 3: Verify results
        logger.info("Step 3: Verifying CLUST-2 results...")
        results = get_clust2_results(conn)

        if results:
            recent_count = results[1]
            logger.info(
                f"✓ CLUST-2 smoke test successful: {recent_count} recent narratives generated"
            )

            # Acceptance criteria
            if recent_count > 0:
                logger.info("✅ ACCEPTANCE: Narratives generated successfully")
                return True
            else:
                logger.warning("⚠️  No recent narratives found")
                return False
        else:
            logger.warning("Could not verify CLUST-2 results")
            return False

    except Exception as e:
        logger.error(f"CLUST-2 smoke test failed: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
