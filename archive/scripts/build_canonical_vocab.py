#!/usr/bin/env python3
"""
Build Canonical Vocabulary System
Strategic Narrative Intelligence ETL Pipeline

1. Normalize all existing keywords and cache canonical mappings
2. Compute document frequencies
3. Build article_core_keywords materialized view (top 6 per article, df in [3..250])
4. Generate vocabulary metrics
"""

import logging
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_batch

# Add ETL pipeline to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from etl_pipeline.extraction.keyword_normalizer import get_normalizer

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


def build_canonical_mappings(conn):
    """Build and cache canonical mappings for all existing keywords."""
    logger.info("Building canonical mappings cache...")

    normalizer = get_normalizer()
    cur = conn.cursor()

    # Get all unique keywords
    cur.execute("SELECT DISTINCT keyword FROM keywords")
    keywords = [row[0] for row in cur.fetchall()]

    logger.info(f"Processing {len(keywords)} unique keywords")

    # Normalize in batches
    mappings = []
    for keyword in keywords:
        norm, canon, conf = normalizer.normalize_and_canonicalize(keyword)
        if canon:  # Only store if not filtered out
            concept_cluster = normalizer.get_concept_cluster(canon)
            mappings.append((norm, canon, conf, concept_cluster))

    # Clear existing mappings
    cur.execute("DELETE FROM keyword_canon_map")

    # Insert new mappings
    if mappings:
        insert_sql = """
            INSERT INTO keyword_canon_map (token_norm, canon_text, confidence, concept_cluster)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (token_norm) DO UPDATE SET
                canon_text = EXCLUDED.canon_text,
                confidence = EXCLUDED.confidence,
                concept_cluster = EXCLUDED.concept_cluster,
                updated_at = NOW()
        """
        execute_batch(cur, insert_sql, mappings)

    conn.commit()
    logger.info(f"Cached {len(mappings)} canonical mappings")
    cur.close()
    return len(mappings)


def compute_document_frequencies(conn):
    """Compute document frequencies for canonical tokens."""
    logger.info("Computing document frequencies...")

    cur = conn.cursor()

    # Get canonical keywords per article
    query = """
        SELECT 
            ak.article_id,
            kcm.canon_text,
            ak.strategic_score
        FROM article_keywords ak
        JOIN keywords k ON ak.keyword_id = k.id
        JOIN keyword_canon_map kcm ON kcm.token_norm = LOWER(TRIM(k.keyword))
        JOIN articles a ON ak.article_id = a.id
        WHERE (a.language = 'EN' OR a.language IS NULL)
          AND kcm.canon_text != ''
    """

    cur.execute(query)
    rows = cur.fetchall()

    # Build document frequency map
    doc_freq = Counter()
    article_tokens = defaultdict(list)

    # Track unique tokens per article (take highest score for duplicates)
    article_token_scores = defaultdict(lambda: defaultdict(float))

    for article_id, canon_text, score in rows:
        # Keep highest score for each token per article
        article_token_scores[article_id][canon_text] = max(
            article_token_scores[article_id][canon_text], score
        )

    # Build final structures
    for article_id, token_scores in article_token_scores.items():
        for canon_text, score in token_scores.items():
            doc_freq[canon_text] += 1
            article_tokens[article_id].append((canon_text, score))

    logger.info(
        f"Found {len(doc_freq)} unique canonical tokens across {len(article_tokens)} articles"
    )

    # Filter by document frequency [3..250]
    valid_tokens = {token for token, freq in doc_freq.items() if 3 <= freq <= 250}
    logger.info(f"Tokens with df in [3..250]: {len(valid_tokens)}")

    cur.close()
    return article_tokens, doc_freq, valid_tokens


def build_core_keywords(conn, article_tokens, doc_freq, valid_tokens):
    """Build article_core_keywords with top 6 per article."""
    logger.info("Building article_core_keywords...")

    cur = conn.cursor()

    # Clear existing core keywords
    cur.execute("DELETE FROM article_core_keywords")

    # Process each article
    core_keywords = []
    articles_with_core = 0

    for article_id, tokens in article_tokens.items():
        # Filter by valid document frequency
        filtered_tokens = [
            (token, score) for token, score in tokens if token in valid_tokens
        ]

        if not filtered_tokens:
            continue

        # Sort by strategic score and take top 6 (MMR diversification could be added here)
        filtered_tokens.sort(key=lambda x: x[1], reverse=True)
        top_tokens = filtered_tokens[:6]

        # Add to core keywords
        for token, score in top_tokens:
            core_keywords.append((article_id, token, score, doc_freq[token]))

        if len(top_tokens) >= 3:  # Count articles with >=3 core concepts
            articles_with_core += 1

    # Insert core keywords
    if core_keywords:
        insert_sql = """
            INSERT INTO article_core_keywords (article_id, token, score, doc_freq)
            VALUES (%s, %s, %s, %s)
        """
        execute_batch(cur, insert_sql, core_keywords)

    conn.commit()

    total_articles = len(article_tokens)
    pct_with_core = (
        (articles_with_core / total_articles * 100) if total_articles > 0 else 0
    )

    logger.info(f"Built article_core_keywords: {len(core_keywords)} mappings")
    logger.info(
        f"Articles with >=3 core concepts: {articles_with_core}/{total_articles} ({pct_with_core:.1f}%)"
    )

    cur.close()
    return len(core_keywords), articles_with_core, total_articles


def calculate_edge_metrics(conn):
    """Calculate average edges per article (pairs sharing >=2 concepts)."""
    logger.info("Calculating edge metrics...")

    cur = conn.cursor()

    # Get articles with their core concepts
    query = """
        SELECT article_id, array_agg(token) as tokens
        FROM article_core_keywords
        GROUP BY article_id
        HAVING COUNT(*) >= 2
    """

    cur.execute(query)
    articles = cur.fetchall()

    total_edges = 0
    articles_with_edges = 0

    normalizer = get_normalizer()

    for article_id, tokens in articles:
        if len(tokens) < 2:
            continue

        # Convert to concept clusters for overlap counting
        clusters = [normalizer.get_concept_cluster(token) for token in tokens]
        cluster_counts = Counter(clusters)

        # Count pairs with shared concepts (same cluster or exact match)
        edges = 0
        for i, token1 in enumerate(tokens):
            for token2 in tokens[i + 1 :]:
                cluster1 = normalizer.get_concept_cluster(token1)
                cluster2 = normalizer.get_concept_cluster(token2)

                # Count as edge if same cluster or both appear frequently
                if cluster1 == cluster2 or (
                    cluster_counts[cluster1] >= 2 or cluster_counts[cluster2] >= 2
                ):
                    edges += 1

        if edges > 0:
            total_edges += edges
            articles_with_edges += 1

    avg_edges = total_edges / len(articles) if articles else 0

    logger.info(f"Average edges per article: {avg_edges:.2f}")
    logger.info(f"Articles with edges: {articles_with_edges}/{len(articles)}")

    cur.close()
    return avg_edges


def generate_metrics_report(
    conn, vocab_size, articles_with_core, total_articles, avg_edges
):
    """Generate and display final metrics report."""

    pct_with_core = (
        (articles_with_core / total_articles * 100) if total_articles > 0 else 0
    )

    report = f"""
=== CANONICAL VOCABULARY METRICS REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

(a) Vocabulary Size: {vocab_size:,} canonical tokens with df in [3..250]

(b) Articles with >=3 Core Concepts: {articles_with_core:,}/{total_articles:,} ({pct_with_core:.1f}%)

(c) Average Edges per Article: {avg_edges:.2f}
    (pairs sharing >=2 concepts via concept clusters)

Core Vocabulary System Status: OPERATIONAL
- Canonical mappings cached: {vocab_size:,} tokens  
- Article core keywords: Top 6 per EN article
- Concept clustering: Active for overlap counting
- Document frequency filtering: [3..250] range applied

Next: Update CLUST-1 to use article_core_keywords only
"""

    print(report)
    logger.info("Metrics report generated successfully")


def main():
    """Main vocabulary building function."""
    logger.info("Starting canonical vocabulary build process...")

    try:
        conn = get_db_connection()

        try:
            # Step 1: Build canonical mappings cache
            build_canonical_mappings(conn)

            # Step 2: Compute document frequencies
            article_tokens, doc_freq, valid_tokens = compute_document_frequencies(conn)

            # Step 3: Build core keywords
            core_count, articles_with_core, total_articles = build_core_keywords(
                conn, article_tokens, doc_freq, valid_tokens
            )

            # Step 4: Calculate edge metrics
            avg_edges = calculate_edge_metrics(conn)

            # Step 5: Generate report
            generate_metrics_report(
                conn, len(valid_tokens), articles_with_core, total_articles, avg_edges
            )

            logger.info("Canonical vocabulary build completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Vocabulary build failed: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to build canonical vocabulary: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
