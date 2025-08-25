#!/usr/bin/env python3
"""
Quick database connection and data availability test for narrative granularity analysis
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import DictCursor

# Fix Windows Unicode encoding
if sys.platform.startswith("win"):
    import io

    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

logging.basicConfig(level=logging.INFO)
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


def test_data_availability():
    """Test what data is available for analysis."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)

    cutoff_72h = datetime.now() - timedelta(hours=72)
    cutoff_7d = datetime.now() - timedelta(days=7)

    try:
        logger.info("=== Database Connection Test ===")

        # Test basic connection
        cur.execute("SELECT version()")
        version = cur.fetchone()
        logger.info(f"PostgreSQL version: {version[0]}")

        # Check available tables
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_name IN ('articles', 'article_clusters', 'narratives', 'article_cluster_members')
            ORDER BY table_name
        """
        )
        available_tables = [row[0] for row in cur.fetchall()]
        logger.info(f"Available tables: {available_tables}")

        # Check articles data
        if "articles" in available_tables:
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(*) FILTER (WHERE published_at >= %s) as articles_72h,
                    COUNT(*) FILTER (WHERE published_at >= %s) as articles_7d,
                    COUNT(DISTINCT source_name) as total_sources,
                    MIN(published_at) as earliest_article,
                    MAX(published_at) as latest_article
                FROM articles
            """,
                (cutoff_72h, cutoff_7d),
            )

            articles_stats = cur.fetchone()
            logger.info("--- Articles Data ---")
            logger.info(f"Total articles: {articles_stats['total_articles']}")
            logger.info(f"Articles (72h): {articles_stats['articles_72h']}")
            logger.info(f"Articles (7d): {articles_stats['articles_7d']}")
            logger.info(f"Total sources: {articles_stats['total_sources']}")
            logger.info(
                f"Date range: {articles_stats['earliest_article']} to {articles_stats['latest_article']}"
            )

        # Check clusters data
        if "article_clusters" in available_tables:
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total_clusters,
                    COUNT(*) FILTER (WHERE created_at >= %s) as clusters_72h,
                    COUNT(*) FILTER (WHERE created_at >= %s) as clusters_7d,
                    AVG(size) as avg_cluster_size,
                    MIN(created_at) as earliest_cluster,
                    MAX(created_at) as latest_cluster
                FROM article_clusters
            """,
                (cutoff_72h, cutoff_7d),
            )

            clusters_stats = cur.fetchone()
            logger.info("--- Clusters Data ---")
            logger.info(f"Total clusters: {clusters_stats['total_clusters']}")
            logger.info(f"Clusters (72h): {clusters_stats['clusters_72h']}")
            logger.info(f"Clusters (7d): {clusters_stats['clusters_7d']}")
            logger.info(f"Avg cluster size: {clusters_stats['avg_cluster_size']:.1f}")
            logger.info(
                f"Date range: {clusters_stats['earliest_cluster']} to {clusters_stats['latest_cluster']}"
            )

        # Check narratives data
        if "narratives" in available_tables:
            cur.execute(
                """
                SELECT 
                    COUNT(*) as total_narratives,
                    COUNT(*) FILTER (WHERE created_at >= %s) as narratives_72h,
                    COUNT(*) FILTER (WHERE created_at >= %s) as narratives_7d,
                    COUNT(*) FILTER (WHERE nested_within IS NOT NULL AND jsonb_array_length(nested_within) > 0) as child_narratives,
                    MIN(created_at) as earliest_narrative,
                    MAX(created_at) as latest_narrative
                FROM narratives
            """,
                (cutoff_72h, cutoff_7d),
            )

            narratives_stats = cur.fetchone()
            logger.info("--- Narratives Data ---")
            logger.info(f"Total narratives: {narratives_stats['total_narratives']}")
            logger.info(f"Narratives (72h): {narratives_stats['narratives_72h']}")
            logger.info(f"Narratives (7d): {narratives_stats['narratives_7d']}")
            logger.info(f"Child narratives: {narratives_stats['child_narratives']}")
            if narratives_stats["earliest_narrative"]:
                logger.info(
                    f"Date range: {narratives_stats['earliest_narrative']} to {narratives_stats['latest_narrative']}"
                )

        # Check materialized views
        cur.execute(
            """
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public' 
              AND table_name LIKE '%strategic%' OR table_name LIKE '%event%'
            ORDER BY table_name
        """
        )
        views = [row[0] for row in cur.fetchall()]
        if views:
            logger.info(f"Strategic views available: {views}")

        # Sample recent cluster data
        if (
            "article_clusters" in available_tables
            and clusters_stats["clusters_72h"] > 0
        ):
            cur.execute(
                """
                SELECT cluster_id, label, top_topics, size, created_at
                FROM article_clusters
                WHERE created_at >= %s
                ORDER BY created_at DESC, size DESC
                LIMIT 5
            """,
                (cutoff_72h,),
            )

            sample_clusters = cur.fetchall()
            logger.info("--- Sample Recent Clusters ---")
            for cluster in sample_clusters:
                logger.info(
                    f"  {cluster['label']} ({cluster['size']} articles) - {cluster['top_topics']}"
                )

        logger.info("=== Connection Test Successful ===")
        return True

    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    success = test_data_availability()
    if success:
        logger.info("✓ Ready to run full narrative granularity analysis")
        logger.info("Run: python analyze_narrative_granularity.py --window 72")
    else:
        logger.error("✗ Database connection or data issues detected")

    sys.exit(0 if success else 1)
