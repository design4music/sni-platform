#!/usr/bin/env python3
"""
Apply batch-aware library fix to address unfair token frequency calculations.
This script executes the SQL updates and reruns CLUST-1 pipeline.
"""

import os
import subprocess
import sys
from pathlib import Path

import psycopg2


def get_db_connection():
    """Get database connection using environment variables (same as existing scripts)."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def execute_sql_statements(statements):
    """Execute SQL statements."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        for statement in statements:
            print(f"Executing: {statement[:100]}...")
            cur.execute(statement)

        conn.commit()
        print("SQL statements executed successfully")
        return True

    except Exception as e:
        print(f"Error executing SQL: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def create_batch_aware_library():
    """Create the batch-aware normalized library."""
    sql_statements = [
        "DROP MATERIALIZED VIEW IF EXISTS shared_keywords_lib_norm_30d CASCADE;",
        """
        CREATE MATERIALIZED VIEW shared_keywords_lib_norm_30d AS
        WITH days AS (
          SELECT date_trunc('day', a.published_at) AS d, COUNT(*) AS n
          FROM articles a
          WHERE a.language='EN' AND a.published_at >= now()-interval '30 days'
          GROUP BY 1
        ),
        thr AS (
          SELECT GREATEST(30, COALESCE(PERCENTILE_CONT(0.4) WITHIN GROUP (ORDER BY n) FILTER (WHERE n>0),0)) AS min_n
          FROM days
        ),
        active_days AS (
          SELECT d FROM days, thr WHERE n >= thr.min_n
        ),
        ak AS (
          SELECT
            a.id AS article_id,
            COALESCE(m.canon_text, LOWER(k.keyword)) AS tok,
            date_trunc('day', a.published_at) AS d
          FROM article_keywords ak
          JOIN keywords k ON k.id=ak.keyword_id
          JOIN articles a ON a.id=ak.article_id
          LEFT JOIN keyword_canon_map m ON m.token_norm=LOWER(k.keyword)
          WHERE a.language='EN' AND a.published_at >= now()-interval '30 days'
        ),
        stats AS (
          SELECT
            tok,
            COUNT(DISTINCT article_id) AS doc_freq,
            COUNT(DISTINCT d) AS days_present,
            COUNT(DISTINCT d) FILTER (WHERE d IN (SELECT d FROM active_days)) AS active_days_present
          FROM ak GROUP BY tok
        )
        SELECT tok, doc_freq, days_present, active_days_present
        FROM stats
        WHERE active_days_present >= 2 OR doc_freq >= 12;
        """,
    ]

    return execute_sql_statements(sql_statements)


def update_core_keywords():
    """Update core keywords to use normalized library."""
    sql_statements = [
        "TRUNCATE article_core_keywords;",
        """
        INSERT INTO article_core_keywords (id, article_id, token, score, doc_freq, created_at)
        WITH base AS (
          SELECT a.id AS article_id,
                 COALESCE(m.canon_text, LOWER(k.keyword)) AS token,
                 ak.strategic_score
          FROM articles a
          JOIN article_keywords ak ON ak.article_id=a.id
          JOIN keywords k ON k.id=ak.keyword_id
          LEFT JOIN keyword_canon_map m ON m.token_norm=LOWER(k.keyword)
          WHERE a.language='EN' AND a.published_at >= now()-interval '300 hours'
        ),
        filtered AS (
          SELECT b.*
          FROM base b
          JOIN shared_keywords_lib_norm_30d s ON s.tok = b.token
        ),
        deduped AS (
          SELECT article_id, token, MAX(strategic_score) as strategic_score
          FROM filtered
          GROUP BY article_id, token
        ),
        ranked AS (
          SELECT *, ROW_NUMBER() OVER (PARTITION BY article_id ORDER BY strategic_score DESC) rnk
          FROM deduped
        )
        SELECT 
          gen_random_uuid() as id,
          article_id, 
          token, 
          strategic_score as score,
          0 as doc_freq,
          now() as created_at
        FROM ranked WHERE rnk <= 8;
        """,
    ]

    return execute_sql_statements(sql_statements)


def update_fair_hubs():
    """Build fair hubs from per-active-day strength."""
    sql_statements = [
        "DROP MATERIALIZED VIEW IF EXISTS keyword_hubs_30d CASCADE;",
        """
        CREATE MATERIALIZED VIEW keyword_hubs_30d AS
        SELECT tok,
               doc_freq::float / NULLIF(active_days_present,0) AS df_per_active_day
        FROM shared_keywords_lib_norm_30d
        ORDER BY df_per_active_day DESC
        LIMIT 12;
        """,
    ]

    return execute_sql_statements(sql_statements)


def run_clustering_pipeline():
    """Run the CLUST-1 pipeline stages."""
    clustering_script = "etl_pipeline/clustering/clust1_taxonomy_graph.py"

    if not Path(clustering_script).exists():
        print(f"Clustering script not found at: {clustering_script}")
        return False

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
            result = subprocess.run(stage_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error in clustering stage: {result.stderr}")
                return False
            else:
                print(f"Successfully completed stage: {stage_cmd[3]}")
                if result.stdout.strip():
                    print(result.stdout)
        except Exception as e:
            print(f"Exception running clustering stage: {e}")
            return False

    return True


def main():
    """Main execution function."""
    print("=== Applying Batch-Aware Library Fix ===")

    # Step 1: Create batch-aware library
    print("\n1. Creating batch-aware normalized library...")
    if not create_batch_aware_library():
        print("Failed to create batch-aware library")
        return 1

    # Step 2: Update core keywords
    print("\n2. Updating core keywords to use normalized library...")
    if not update_core_keywords():
        print("Failed to update core keywords")
        return 1

    # Step 3: Update fair hubs
    print("\n3. Building fair hubs from per-active-day strength...")
    if not update_fair_hubs():
        print("Failed to update fair hubs")
        return 1

    # Step 4: Run clustering pipeline
    print("\n4. Running CLUST-1 pipeline...")
    if not run_clustering_pipeline():
        print("Failed to run clustering pipeline")
        return 1

    print("\n=== Batch-Aware Fix Applied Successfully ===")
    print("Expected improvements:")
    print("- Coverage should climb back (batch bias removed)")
    print("- Missing topics (tariffs/sanctions/Ukraine/India oil) should reappear")
    print("- Tokens spanning multiple active days now fairly weighted")
    print("- Purity should remain ~unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
