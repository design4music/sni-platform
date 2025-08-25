#!/usr/bin/env python3
"""
Strategic Filtering KPI Check
Validates CLUST-0 system performance metrics
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def main():
    """Execute KPI measurements for strategic filtering system"""

    try:
        # Initialize database
        config = get_config()
        initialize_database(config.database)

        print("=== STRATEGIC FILTERING KPI ANALYSIS ===")
        print(f"Analysis timestamp: {datetime.now()}")
        print()

        with get_db_session() as session:

            # KPI 1: pct_candidates_over_all (EN, 300h): aim 35-55%
            print("KPI 1: Strategic Candidate Filtering Rate")
            print("Target: 35-55% of articles should be strategic candidates")

            kpi1_query = text(
                """
                WITH stats AS (
                  SELECT 
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '300 hours') AS total_articles_300h,
                    (SELECT COUNT(*) FROM strategic_candidates_300h) AS strategic_candidates
                  FROM articles
                  WHERE language = 'EN'
                )
                SELECT 
                  total_articles_300h,
                  strategic_candidates
                FROM stats;
            """
            )

            result = session.execute(kpi1_query).fetchone()
            if result:
                total_articles, strategic_candidates = result

                # Calculate percentage in Python
                if total_articles > 0:
                    pct_candidates = round(
                        (strategic_candidates / total_articles) * 100, 1
                    )
                else:
                    pct_candidates = 0.0

                print(f"  Total EN articles (300h): {total_articles:,}")
                print(f"  Strategic candidates: {strategic_candidates:,}")
                print(f"  Filtering rate: {pct_candidates}%")

                # Evaluation
                if 35 <= pct_candidates <= 55:
                    print(f"  PASS - Within target range (35-55%)")
                elif pct_candidates < 35:
                    print(f"  LOW - Below target (need more strategic content)")
                else:
                    print(f"  HIGH - Above target (filtering may be too permissive)")

                print()

            # KPI 2: pct_clustered_over_candidates: aim 35-55%
            print("KPI 2: Strategic Clustering Success Rate")
            print("Target: 35-55% of strategic candidates should get clustered")

            kpi2_query = text(
                """
                WITH stats AS (
                  SELECT 
                    (SELECT COUNT(*) FROM strategic_candidates_300h) AS strategic_candidates,
                    COUNT(*) AS clustered_articles
                  FROM strategic_candidates_300h sc
                  INNER JOIN article_cluster_members acm ON acm.article_id = sc.article_id
                  INNER JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
                  WHERE ac.created_at >= NOW() - INTERVAL '300 hours'
                )
                SELECT 
                  strategic_candidates,
                  clustered_articles
                FROM stats;
            """
            )

            result = session.execute(kpi2_query).fetchone()
            if result:
                strategic_candidates, clustered_articles = result

                # Calculate percentage in Python
                if strategic_candidates > 0:
                    pct_clustered = round(
                        (clustered_articles / strategic_candidates) * 100, 1
                    )
                else:
                    pct_clustered = 0.0

                print(f"  Strategic candidates: {strategic_candidates:,}")
                print(f"  Successfully clustered: {clustered_articles:,}")
                print(f"  Clustering success rate: {pct_clustered}%")

                # Evaluation
                if 35 <= pct_clustered <= 55:
                    print(f"  PASS - Within target range (35-55%)")
                elif pct_clustered < 35:
                    print(f"  LOW - Clustering may be too strict")
                else:
                    print(f"  HIGH - Clustering may be too permissive")

                print()

            # Additional diagnostics
            print("System Diagnostics")

            # Check recent ingestion
            ingestion_query = text(
                """
                SELECT 
                  DATE_TRUNC('hour', created_at) as hour,
                  COUNT(*) as articles
                FROM articles 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                  AND language = 'EN'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour DESC
                LIMIT 5;
            """
            )

            print("Recent ingestion (last 5 hours):")
            results = session.execute(ingestion_query).fetchall()
            for hour, count in results:
                print(f"  {hour}: {count} articles")

            print()

            # Strategic filtering summary (simplified)
            print("Strategic filtering summary:")
            print(f"  Total strategic candidates: {strategic_candidates:,}")
            if total_articles > 0:
                filter_rate = (strategic_candidates / total_articles) * 100
                print(f"  Filtering rate: {filter_rate:.1f}%")

            print()

            # Performance summary
            print("=== SYSTEM PERFORMANCE SUMMARY ===")

            summary_query = text(
                """
                SELECT 
                  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') AS articles_24h,
                  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '300 hours') AS articles_300h,
                  (SELECT COUNT(*) FROM strategic_candidates_300h) AS strategic_candidates,
                  (SELECT COUNT(*) FROM article_cluster_members acm 
                   JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id 
                   WHERE ac.created_at >= NOW() - INTERVAL '24 hours') AS clustered_24h
                FROM articles a
                WHERE a.language = 'EN';
            """
            )

            result = session.execute(summary_query).fetchone()
            if result:
                articles_24h, articles_300h, strategic_candidates, clustered_24h = (
                    result
                )

                print(f"Articles ingested (24h): {articles_24h:,}")
                print(f"Articles ingested (300h): {articles_300h:,}")
                print(f"Strategic candidates (300h): {strategic_candidates:,}")
                print(f"Articles clustered (24h): {clustered_24h:,}")

                if articles_300h > 0:
                    strategic_rate = (strategic_candidates / articles_300h) * 100
                    print(f"Strategic filtering rate: {strategic_rate:.1f}%")

        print()
        print("KPI analysis completed successfully")

    except Exception as e:
        print(f"Error during KPI analysis: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
