#!/usr/bin/env python3
"""
Clean Old Clusters
Remove old biased clusters before running new CLUST-1
"""

import sys

# Add project root to path
sys.path.append(".")

import psycopg2
from etl_pipeline.core.config import get_config


def clean_old_clusters():
    """Clean article_clusters table for fresh clustering"""

    print("CLEANING OLD BIASED CLUSTERS")
    print("=" * 50)

    config = get_config()
    conn = psycopg2.connect(
        host=config.database.host,
        database=config.database.database,
        user=config.database.username,
        password=config.database.password,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Check current state
    cur.execute("SELECT COUNT(*) FROM article_clusters")
    old_count = cur.fetchone()[0]

    cur.execute(
        "SELECT cluster_algorithm, COUNT(*) FROM article_clusters GROUP BY cluster_algorithm"
    )
    algorithms = cur.fetchall()

    print("CURRENT STATE:")
    print(f"  Total cluster assignments: {old_count:,}")
    for alg, count in algorithms:
        print(f"  {alg}: {count:,} assignments")

    # Show sample of old clusters to confirm bias issue
    print("\nSAMPLE OF OLD CLUSTERS (checking for source bias):")
    cur.execute(
        """
        SELECT ac.cluster_id, a.source_name, COUNT(*) as count
        FROM article_clusters ac
        JOIN articles a ON ac.article_id = a.id
        WHERE ac.cluster_algorithm = 'CLUST-1'
        GROUP BY ac.cluster_id, a.source_name
        ORDER BY ac.cluster_id, count DESC
        LIMIT 10
    """
    )

    current_cluster = None
    for cluster_id, source, count in cur.fetchall():
        if cluster_id != current_cluster:
            if current_cluster:
                print()
            print(f"  {cluster_id[-12:]}:")
            current_cluster = cluster_id
        source_name = source or "Unknown"
        print(f"    {source_name}: {count} articles")

    # Clear all old clusters
    print("\nCLEARING OLD CLUSTERS...")
    cur.execute("DELETE FROM article_clusters")
    removed_count = cur.rowcount

    print(f"Removed {removed_count:,} old cluster assignments")
    print("[OK] Database ready for new keyword-based clustering!")

    cur.close()
    conn.close()

    return removed_count


if __name__ == "__main__":
    clean_old_clusters()
