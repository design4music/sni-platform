#!/usr/bin/env python3
"""
CLUST-1 Optimized Orphan Attach Pass
Optimized version with batching, pre-computed embeddings, and performance improvements.
"""

import argparse
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

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
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def load_sentence_transformer():
    """Load sentence transformer model for embeddings."""
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence transformer model")
        return model
    except Exception as e:
        logger.warning(f"Could not load sentence transformer: {e}")
        return None


def get_hub_tokens(conn):
    """Get current hub tokens."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT tok FROM keyword_hubs_30d")
        hubs = {row[0] for row in cur.fetchall()}
        logger.info(f"Loaded {len(hubs)} hub tokens")
        return hubs
    finally:
        cur.close()


def get_clustered_articles(conn):
    """Get articles already in clusters."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT article_id FROM article_cluster_members")
        clustered = {row[0] for row in cur.fetchall()}
        logger.info(f"Found {len(clustered)} already clustered articles")
        return clustered
    finally:
        cur.close()


def get_cluster_info_optimized(conn, model=None):
    """Get cluster information with pre-computed embeddings."""
    cur = conn.cursor()
    try:
        # Get cluster members and their keywords
        cur.execute(
            """
            SELECT 
                acm.cluster_id,
                ac.size,
                array_agg(DISTINCT a.title) as titles,
                array_agg(DISTINCT ck.token) as anchor_tokens
            FROM article_cluster_members acm
            JOIN article_clusters ac ON ac.cluster_id = acm.cluster_id
            JOIN articles a ON a.id = acm.article_id
            JOIN article_core_keywords ck ON ck.article_id = acm.article_id
            WHERE a.language = 'EN'
            GROUP BY acm.cluster_id, ac.size
        """
        )

        clusters = {}
        cluster_embeddings = {}

        for cluster_id, size, titles, tokens in cur.fetchall():
            clean_titles = [t for t in titles if t and t.strip()]

            clusters[cluster_id] = {
                "size": size,
                "titles": clean_titles,
                "anchor_tokens": set(tokens),
            }

            # Pre-compute cluster embedding centroid
            if model and clean_titles:
                try:
                    title_embeddings = model.encode(
                        clean_titles[:5]
                    )  # Limit to 5 titles for speed
                    cluster_embeddings[cluster_id] = np.mean(title_embeddings, axis=0)
                except Exception as e:
                    logger.debug(
                        f"Error computing embedding for cluster {cluster_id}: {e}"
                    )
                    cluster_embeddings[cluster_id] = None
            else:
                cluster_embeddings[cluster_id] = None

        logger.info(
            f"Loaded {len(clusters)} clusters with {len([c for c in cluster_embeddings.values() if c is not None])} embeddings"
        )
        return clusters, cluster_embeddings

    finally:
        cur.close()


def get_orphan_articles_filtered(
    conn, hours_back=300, clustered_articles=None, min_keywords=3
):
    """Get orphaned articles with keyword filtering."""
    cur = conn.cursor()
    try:
        # Pre-filter orphans with strategic keywords only
        query = """
            SELECT 
                a.id,
                a.title,
                a.source_name,
                array_agg(ck.token) as core_keywords,
                a.published_at
            FROM articles a
            JOIN article_core_keywords ck ON ck.article_id = a.id
            JOIN strategic_candidates_300h sc ON a.id = sc.article_id
            WHERE a.language = 'EN'
            AND a.published_at >= %s
            GROUP BY a.id, a.title, a.source_name, a.published_at
            HAVING COUNT(ck.token) >= %s
            ORDER BY a.published_at DESC
        """

        window_start = datetime.now() - timedelta(hours=hours_back)
        cur.execute(query, (window_start, min_keywords))

        orphans = []
        for article_id, title, source, keywords, published_at in cur.fetchall():
            if clustered_articles and article_id in clustered_articles:
                continue  # Skip already clustered

            orphans.append(
                {
                    "id": article_id,
                    "title": title or "",
                    "source": source,
                    "keywords": set(keywords),
                }
            )

        logger.info(f"Found {len(orphans)} strategic orphan articles")
        return orphans

    finally:
        cur.close()


def calculate_keyword_overlap(article_keywords, cluster_tokens, hub_tokens):
    """Calculate non-hub keyword overlap."""
    article_nonhub = article_keywords - hub_tokens
    cluster_nonhub = cluster_tokens - hub_tokens
    shared_nonhub = len(article_nonhub & cluster_nonhub)
    return shared_nonhub


def attach_orphans_optimized(
    conn,
    orphans,
    clusters,
    cluster_embeddings,
    hub_tokens,
    model=None,
    cos_threshold=0.75,
    min_shared=2,
    batch_size=50,
    max_time=300,
):
    """Optimized orphan attachment with batching and timeouts."""
    attachments = []
    start_time = time.time()
    processed = 0

    # Batch process orphans
    for batch_start in range(0, len(orphans), batch_size):
        if time.time() - start_time > max_time:
            logger.warning(
                f"Timeout reached after {max_time}s, processed {processed}/{len(orphans)} orphans"
            )
            break

        batch = orphans[batch_start : batch_start + batch_size]
        batch_titles = [orphan["title"] for orphan in batch if orphan["title"].strip()]

        # Batch compute orphan embeddings
        orphan_embeddings = {}
        if model and batch_titles:
            try:
                embeddings = model.encode(batch_titles)
                for i, orphan in enumerate(batch):
                    if orphan["title"].strip():
                        orphan_embeddings[orphan["id"]] = embeddings[i]
            except Exception as e:
                logger.warning(f"Error computing batch embeddings: {e}")

        # Process each orphan in batch
        for orphan in batch:
            processed += 1
            best_cluster = None
            best_score = 0.0

            # Quick keyword filter first
            candidate_clusters = []
            for cluster_id, cluster_info in clusters.items():
                shared_keywords = calculate_keyword_overlap(
                    orphan["keywords"], cluster_info["anchor_tokens"], hub_tokens
                )
                if shared_keywords >= min_shared:
                    candidate_clusters.append(
                        (cluster_id, cluster_info, shared_keywords)
                    )

            # Process only candidate clusters
            for cluster_id, cluster_info, shared_keywords in candidate_clusters:
                score = 0.0

                # Calculate title similarity using pre-computed embeddings
                if (
                    model
                    and orphan["id"] in orphan_embeddings
                    and cluster_id in cluster_embeddings
                    and cluster_embeddings[cluster_id] is not None
                ):

                    try:
                        orphan_emb = orphan_embeddings[orphan["id"]]
                        cluster_emb = cluster_embeddings[cluster_id]

                        # Cosine similarity
                        dot_product = np.dot(orphan_emb, cluster_emb)
                        norm_a = np.linalg.norm(orphan_emb)
                        norm_c = np.linalg.norm(cluster_emb)

                        if norm_a > 0 and norm_c > 0:
                            title_sim = dot_product / (norm_a * norm_c)
                            if title_sim >= cos_threshold:
                                score = title_sim + (shared_keywords * 0.1)
                    except Exception as e:
                        logger.debug(f"Similarity calculation error: {e}")

                # Fallback to keyword-only scoring
                if score == 0.0 and shared_keywords >= 3:
                    score = shared_keywords * 0.1

                if score > best_score:
                    best_score = score
                    best_cluster = cluster_id

            if best_cluster:
                attachments.append(
                    {
                        "article_id": orphan["id"],
                        "cluster_id": best_cluster,
                        "score": float(
                            best_score
                        ),  # Convert numpy types to Python float
                        "shared_keywords": calculate_keyword_overlap(
                            orphan["keywords"],
                            clusters[best_cluster]["anchor_tokens"],
                            hub_tokens,
                        ),
                    }
                )

        if processed % 100 == 0:
            elapsed = time.time() - start_time
            logger.info(
                f"Processed {processed}/{len(orphans)} orphans in {elapsed:.1f}s, found {len(attachments)} attachments"
            )

    logger.info(
        f"Attachment process completed: {len(attachments)} orphans to attach from {processed} processed"
    )
    return attachments


def save_attachments(conn, attachments):
    """Save orphan attachments to database."""
    if not attachments:
        logger.info("No orphans to attach")
        return 0

    cur = conn.cursor()
    try:
        # Insert new cluster memberships
        insert_data = [
            (att["article_id"], att["cluster_id"], att["score"]) for att in attachments
        ]

        cur.executemany(
            """
            INSERT INTO article_cluster_members (article_id, cluster_id, weight)
            VALUES (%s, %s, %s)
            ON CONFLICT (article_id, cluster_id) DO NOTHING
        """,
            insert_data,
        )

        # Update cluster sizes
        cluster_updates = defaultdict(int)
        for att in attachments:
            cluster_updates[att["cluster_id"]] += 1

        for cluster_id, added_count in cluster_updates.items():
            cur.execute(
                """
                UPDATE article_clusters 
                SET size = size + %s, updated_at = now()
                WHERE cluster_id = %s
            """,
                (added_count, cluster_id),
            )

        conn.commit()
        logger.info(f"Successfully attached {len(attachments)} orphans to clusters")

        return len(attachments)

    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving attachments: {e}")
        return 0
    finally:
        cur.close()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Optimized orphan attachment")
    parser.add_argument("--window", type=int, default=300, help="Time window in hours")
    parser.add_argument(
        "--cos", type=float, default=0.75, help="Cosine similarity threshold"
    )
    parser.add_argument(
        "--min_shared", type=int, default=2, help="Minimum shared non-hub keywords"
    )
    parser.add_argument(
        "--batch_size", type=int, default=50, help="Batch size for processing"
    )
    parser.add_argument(
        "--max_time", type=int, default=300, help="Maximum processing time in seconds"
    )

    args = parser.parse_args()

    logger.info(
        f"Starting optimized orphan attach (window={args.window}h, cos={args.cos}, batch={args.batch_size})"
    )

    conn = get_db_connection()

    try:
        # Load components
        model = load_sentence_transformer()
        hub_tokens = get_hub_tokens(conn)
        clustered_articles = get_clustered_articles(conn)
        clusters, cluster_embeddings = get_cluster_info_optimized(conn, model)
        orphans = get_orphan_articles_filtered(
            conn, args.window, clustered_articles, min_keywords=3
        )

        if not orphans:
            logger.info("No orphan articles to process")
            return 0

        if not clusters:
            logger.info("No clusters available for attachment")
            return 0

        # Find and save attachments
        attachments = attach_orphans_optimized(
            conn,
            orphans,
            clusters,
            cluster_embeddings,
            hub_tokens,
            model,
            args.cos,
            args.min_shared,
            args.batch_size,
            args.max_time,
        )

        attached_count = save_attachments(conn, attachments)

        logger.info(
            f"Optimized orphan attach completed: {attached_count} articles attached"
        )
        return 0

    except Exception as e:
        logger.error(f"Error in orphan attach pass: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
