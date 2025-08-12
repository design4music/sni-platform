#!/usr/bin/env python3
"""
Update materialized views for recall improvement tweaks
"""

import psycopg2


def main():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="narrative_intelligence",
        user="postgres",
        password="postgres",
    )

    cur = conn.cursor()

    print("Dropping and recreating materialized views...")

    # Drop all dependent views
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS keyword_hubs_30d CASCADE")
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS keyword_specificity_30d CASCADE")
    cur.execute("DROP MATERIALIZED VIEW IF EXISTS shared_keywords_lib_30d CASCADE")

    # Recreate shared_keywords_lib_30d with df >= 2 (was 3)
    cur.execute(
        """
        CREATE MATERIALIZED VIEW shared_keywords_lib_30d AS
        WITH token_stats AS (
            SELECT 
                kcm.canon_text as tok,
                COUNT(DISTINCT ak.article_id) as doc_freq,
                AVG(ak.strategic_score) as avg_score
            FROM article_keywords ak
            JOIN keywords k ON ak.keyword_id = k.id
            JOIN keyword_canon_map kcm ON kcm.token_norm = LOWER(TRIM(k.keyword))
            JOIN articles a ON ak.article_id = a.id
            WHERE (a.language = 'EN' OR a.language IS NULL)
              AND kcm.canon_text != ''
              AND a.published_at >= NOW() - INTERVAL '30 days'
            GROUP BY kcm.canon_text
            HAVING COUNT(DISTINCT ak.article_id) BETWEEN 2 AND 600
        )
        SELECT tok, doc_freq, avg_score
        FROM token_stats
        ORDER BY doc_freq DESC
    """
    )

    # Recreate keyword_hubs_30d (top-12 instead of 30)
    cur.execute(
        """
        CREATE MATERIALIZED VIEW keyword_hubs_30d AS
        SELECT tok, doc_freq FROM shared_keywords_lib_30d
        ORDER BY doc_freq DESC LIMIT 12
    """
    )

    # Recreate keyword_specificity_30d
    cur.execute(
        """
        CREATE MATERIALIZED VIEW keyword_specificity_30d AS
        SELECT 
            tok,
            (1.0 / LN(doc_freq + 1)) as spec
        FROM shared_keywords_lib_30d
        ORDER BY spec DESC
    """
    )

    conn.commit()
    print("Recreated all materialized views")

    # Rebuild article_core_keywords with K=8 (was 6)
    cur.execute("DELETE FROM article_core_keywords")

    cur.execute(
        """
        WITH token_doc_freq AS (
            SELECT 
                kcm.canon_text,
                COUNT(DISTINCT ak.article_id) as doc_freq
            FROM article_keywords ak
            JOIN keywords k ON ak.keyword_id = k.id
            JOIN keyword_canon_map kcm ON kcm.token_norm = LOWER(TRIM(k.keyword))
            JOIN articles a ON ak.article_id = a.id
            WHERE (a.language = 'EN' OR a.language IS NULL)
              AND kcm.canon_text != ''
              AND a.published_at >= NOW() - INTERVAL '300 hours'
            GROUP BY kcm.canon_text
            HAVING COUNT(DISTINCT ak.article_id) BETWEEN 2 AND 250
        ),
        ranked_keywords AS (
            SELECT 
                ak.article_id,
                kcm.canon_text as token,
                MAX(ak.strategic_score) as score,
                tdf.doc_freq,
                ROW_NUMBER() OVER (PARTITION BY ak.article_id ORDER BY MAX(ak.strategic_score) DESC) as rn
            FROM article_keywords ak
            JOIN keywords k ON ak.keyword_id = k.id
            JOIN keyword_canon_map kcm ON kcm.token_norm = LOWER(TRIM(k.keyword))
            JOIN articles a ON ak.article_id = a.id
            JOIN token_doc_freq tdf ON kcm.canon_text = tdf.canon_text
            WHERE (a.language = 'EN' OR a.language IS NULL)
              AND kcm.canon_text != ''
              AND a.published_at >= NOW() - INTERVAL '300 hours'
            GROUP BY ak.article_id, kcm.canon_text, tdf.doc_freq
        )
        INSERT INTO article_core_keywords (article_id, token, score, doc_freq)
        SELECT article_id, token, score, doc_freq
        FROM ranked_keywords
        WHERE rn <= 8
    """
    )

    core_count = cur.rowcount
    conn.commit()

    print(f"Rebuilt article_core_keywords with K=8: {core_count:,} mappings")

    # Check stats
    cur.execute("SELECT COUNT(*) FROM shared_keywords_lib_30d")
    lib_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT article_id) FROM article_core_keywords")
    eligible_articles = cur.fetchone()[0]

    print(f"Vocabulary size: {lib_count:,} tokens")
    print(f"Articles with core keywords: {eligible_articles:,}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
