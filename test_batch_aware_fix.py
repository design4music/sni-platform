#!/usr/bin/env python3
"""
Test the batch-aware fix by comparing before/after clustering metrics.
"""

import os
import subprocess
from datetime import datetime

import psycopg2


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def capture_current_metrics():
    """Capture current clustering metrics before clearing."""
    conn = get_db_connection()
    cur = conn.cursor()

    print("=== BEFORE Batch-Aware Fix (Current State) ===")

    # Total English articles in 300h window
    cur.execute(
        """
        SELECT COUNT(*) 
        FROM articles a 
        WHERE a.language='EN' AND a.published_at >= now()-interval '300 hours'
    """
    )
    total_articles = cur.fetchone()[0]

    # Articles with 3+ core keywords (eligible for clustering)
    cur.execute(
        """
        SELECT COUNT(DISTINCT a.id) 
        FROM articles a 
        JOIN article_core_keywords ck ON a.id = ck.article_id 
        WHERE a.language='EN' AND a.published_at >= now()-interval '300 hours'
        GROUP BY a.id
        HAVING COUNT(ck.token) >= 3
    """
    )
    eligible_articles = len(cur.fetchall())

    # Current clusters (from last run)
    cur.execute("SELECT COUNT(*) FROM article_clusters")
    total_clusters = cur.fetchone()[0]

    # Currently clustered articles
    cur.execute("SELECT COUNT(DISTINCT article_id) FROM article_cluster_members")
    clustered_articles = cur.fetchone()[0]

    # Get some example cluster labels
    cur.execute(
        """
        SELECT label, size, cohesion 
        FROM article_clusters 
        ORDER BY size DESC 
        LIMIT 10
    """
    )
    top_clusters = cur.fetchall()

    metrics = {
        "total_articles": total_articles,
        "eligible_articles": eligible_articles,
        "total_clusters": total_clusters,
        "clustered_articles": clustered_articles,
        "recall": (
            (clustered_articles / eligible_articles * 100)
            if eligible_articles > 0
            else 0
        ),
        "coverage": (
            (eligible_articles / total_articles * 100) if total_articles > 0 else 0
        ),
        "top_clusters": top_clusters,
    }

    print(f"Total articles (300h): {total_articles}")
    print(f"Eligible articles (3+ keywords): {eligible_articles}")
    print(f"Coverage: {metrics['coverage']:.1f}%")
    print(f"Total clusters: {total_clusters}")
    print(f"Clustered articles: {clustered_articles}")
    print(f"Recall: {metrics['recall']:.1f}%")

    if top_clusters:
        print("\nTop clusters by size:")
        for label, size, cohesion in top_clusters[:5]:
            print(f"  - {label}: {size} articles, cohesion {cohesion:.3f}")

    cur.close()
    conn.close()
    return metrics


def clear_clustering_results():
    """Clear existing clustering results."""
    conn = get_db_connection()
    cur = conn.cursor()

    print("\n=== Clearing Existing Clustering Results ===")

    try:
        # Clear in correct order due to foreign keys
        cur.execute("DELETE FROM article_cluster_members")
        deleted_members = cur.rowcount

        cur.execute("DELETE FROM article_clusters")
        deleted_clusters = cur.rowcount

        conn.commit()

        print(
            f"Cleared {deleted_clusters} clusters and {deleted_members} cluster memberships"
        )
        return True

    except Exception as e:
        print(f"Error clearing clustering results: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def run_full_clustering_pipeline():
    """Run the complete CLUST-1 pipeline."""
    print("\n=== Running Fresh CLUST-1 Pipeline ===")

    clustering_script = "etl_pipeline/clustering/clust1_taxonomy_graph.py"

    stages = [
        [
            "python",
            clustering_script,
            "--stage",
            "seed",
            "--window",
            "300",
            "--lang",
            "EN",
        ],
        [
            "python",
            clustering_script,
            "--stage",
            "densify",
            "--window",
            "300",
            "--cos",
            "0.88",
            "--lang",
            "EN",
        ],
        ["python", clustering_script, "--stage", "persist", "--lang", "EN"],
    ]

    for stage_cmd in stages:
        print(f"Running: {' '.join(stage_cmd)}")
        try:
            # Set environment to handle Unicode properly on Windows
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                stage_cmd,
                capture_output=True,
                text=True,
                env=env,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                print(f"Error in clustering stage: {result.stderr}")
                return False
            else:
                print(f"✓ Completed stage: {stage_cmd[3]}")
                # Print key output lines
                for line in result.stdout.split("\n"):
                    if (
                        "clusters created" in line.lower()
                        or "articles clustered" in line.lower()
                    ):
                        print(f"  {line.strip()}")
        except Exception as e:
            print(f"Exception running clustering stage: {e}")
            return False

    return True


def capture_new_metrics():
    """Capture metrics after applying the batch-aware fix."""
    conn = get_db_connection()
    cur = conn.cursor()

    print("\n=== AFTER Batch-Aware Fix (New Results) ===")

    # Total English articles in 300h window
    cur.execute(
        """
        SELECT COUNT(*) 
        FROM articles a 
        WHERE a.language='EN' AND a.published_at >= now()-interval '300 hours'
    """
    )
    total_articles = cur.fetchone()[0]

    # Articles with 3+ core keywords (eligible for clustering)
    cur.execute(
        """
        SELECT COUNT(DISTINCT a.id) 
        FROM articles a 
        JOIN article_core_keywords ck ON a.id = ck.article_id 
        WHERE a.language='EN' AND a.published_at >= now()-interval '300 hours'
        GROUP BY a.id
        HAVING COUNT(ck.token) >= 3
    """
    )
    eligible_articles = len(cur.fetchall())

    # New clusters
    cur.execute("SELECT COUNT(*) FROM article_clusters")
    total_clusters = cur.fetchone()[0]

    # Newly clustered articles
    cur.execute("SELECT COUNT(DISTINCT article_id) FROM article_cluster_members")
    clustered_articles = cur.fetchone()[0]

    # Get average cohesion
    cur.execute("SELECT AVG(cohesion) FROM article_clusters WHERE cohesion IS NOT NULL")
    avg_cohesion = cur.fetchone()[0] or 0

    # Get some example cluster labels
    cur.execute(
        """
        SELECT label, size, cohesion 
        FROM article_clusters 
        ORDER BY size DESC 
        LIMIT 10
    """
    )
    top_clusters = cur.fetchall()

    metrics = {
        "total_articles": total_articles,
        "eligible_articles": eligible_articles,
        "total_clusters": total_clusters,
        "clustered_articles": clustered_articles,
        "recall": (
            (clustered_articles / eligible_articles * 100)
            if eligible_articles > 0
            else 0
        ),
        "coverage": (
            (eligible_articles / total_articles * 100) if total_articles > 0 else 0
        ),
        "avg_cohesion": avg_cohesion,
        "top_clusters": top_clusters,
    }

    print(f"Total articles (300h): {total_articles}")
    print(f"Eligible articles (3+ keywords): {eligible_articles}")
    print(f"Coverage: {metrics['coverage']:.1f}%")
    print(f"Total clusters: {total_clusters}")
    print(f"Clustered articles: {clustered_articles}")
    print(f"Recall: {metrics['recall']:.1f}%")
    print(f"Average cohesion: {avg_cohesion:.3f}")

    if top_clusters:
        print("\nTop clusters by size:")
        for label, size, cohesion in top_clusters[:5]:
            print(f"  - {label}: {size} articles, cohesion {cohesion:.3f}")

    cur.close()
    conn.close()
    return metrics


def compare_metrics(before, after):
    """Compare before and after metrics."""
    print("\n=== COMPARISON RESULTS ===")

    # Coverage comparison
    coverage_change = after["coverage"] - before["coverage"]
    print(
        f"Coverage: {before['coverage']:.1f}% → {after['coverage']:.1f}% ({coverage_change:+.1f}%)"
    )

    # Recall comparison
    recall_change = after["recall"] - before["recall"]
    recall_improvement = (
        ((after["recall"] - before["recall"]) / before["recall"] * 100)
        if before["recall"] > 0
        else 0
    )
    print(
        f"Recall: {before['recall']:.1f}% → {after['recall']:.1f}% ({recall_change:+.1f}pp, {recall_improvement:+.0f}% improvement)"
    )

    # Cluster count comparison
    cluster_change = after["total_clusters"] - before["total_clusters"]
    print(
        f"Total clusters: {before['total_clusters']} → {after['total_clusters']} ({cluster_change:+d})"
    )

    # Clustered articles comparison
    clustered_change = after["clustered_articles"] - before["clustered_articles"]
    print(
        f"Clustered articles: {before['clustered_articles']} → {after['clustered_articles']} ({clustered_change:+d})"
    )

    # Quality comparison (if available)
    if "avg_cohesion" in after:
        print(f"Average cohesion: {after['avg_cohesion']:.3f}")

    # Summary
    print("\n=== BATCH-AWARE FIX IMPACT ===")
    if coverage_change > 0:
        print(f"✓ Coverage improved by {coverage_change:.1f}pp - batch bias reduced!")
    else:
        print(f"- Coverage changed by {coverage_change:.1f}pp")

    if recall_change > 0:
        print(
            f"✓ Recall improved by {recall_change:.1f}pp ({recall_improvement:+.0f}% improvement)"
        )
        print("  → More articles successfully clustered with batch-aware library")
    else:
        print(f"- Recall changed by {recall_change:.1f}pp")

    if cluster_change > 0:
        print(f"✓ Created {cluster_change} additional clusters")
        print("  → Previously filtered topics now emerging")

    # Look for specific expected topics in new clusters
    expected_topics = ["tariff", "sanction", "ukraine", "india", "oil", "trade"]
    new_cluster_labels = [cluster[0].lower() for cluster in after["top_clusters"]]

    found_topics = []
    for topic in expected_topics:
        for label in new_cluster_labels:
            if topic in label:
                found_topics.append(topic)
                break

    if found_topics:
        print(f"✓ Recovered expected topics: {', '.join(found_topics)}")

    return {
        "coverage_change": coverage_change,
        "recall_change": recall_change,
        "recall_improvement": recall_improvement,
        "cluster_change": cluster_change,
        "clustered_change": clustered_change,
    }


def main():
    """Main test execution."""
    print("=== Testing Batch-Aware Fix Impact ===")
    print(f"Started at: {datetime.now()}")

    # Step 1: Capture current state
    before_metrics = capture_current_metrics()

    # Step 2: Clear clustering results
    if not clear_clustering_results():
        print("Failed to clear clustering results")
        return 1

    # Step 3: Run fresh clustering pipeline
    if not run_full_clustering_pipeline():
        print("Failed to run clustering pipeline")
        return 1

    # Step 4: Capture new results
    after_metrics = capture_new_metrics()

    # Step 5: Compare and summarize
    comparison = compare_metrics(before_metrics, after_metrics)

    print(f"\nCompleted at: {datetime.now()}")

    return 0


if __name__ == "__main__":
    exit(main())
