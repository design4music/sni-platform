#!/usr/bin/env python3
"""
CLUST-1 Orphan Attach Pass
Attaches orphaned articles to existing clusters using title embedding cosine similarity.
Safe recall boost without creating new clusters.
"""

import argparse
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

# Add project root to path for centralized config
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import centralized database connection
from etl_pipeline.core.config import get_db_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Database connection now uses centralized system


def load_sentence_transformer():
    """Load sentence transformer model for embeddings."""
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence transformer model")
        return model
    except Exception as e:
        logger.warning(f"Could not load sentence transformer: {e}")
        logger.info("Will use keyword overlap only for similarity")
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


def get_cluster_info(conn):
    """Get cluster information with centroids."""
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
        for cluster_id, size, titles, tokens in cur.fetchall():
            clusters[cluster_id] = {
                "size": size,
                "titles": [t for t in titles if t],
                "anchor_tokens": set(tokens),
            }

        logger.info(f"Loaded {len(clusters)} clusters for attachment")
        return clusters

    finally:
        cur.close()


def get_orphan_articles(conn, hours_back=300, clustered_articles=None):
    """Get orphaned articles (not in clusters) with their keywords."""
    cur = conn.cursor()
    try:
        # Get orphan articles
        query = """
            SELECT DISTINCT
                a.id,
                a.title,
                a.source_name,
                array_agg(ck.token) as core_keywords
            FROM articles a
            JOIN article_core_keywords ck ON ck.article_id = a.id
            WHERE a.language = 'EN'
            AND a.published_at >= %s
            GROUP BY a.id, a.title, a.source_name
            HAVING COUNT(ck.token) >= 3
        """

        window_start = datetime.now() - timedelta(hours=hours_back)
        cur.execute(query, (window_start,))

        orphans = []
        for article_id, title, source, keywords in cur.fetchall():
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

        logger.info(f"Found {len(orphans)} orphan articles")
        return orphans

    finally:
        cur.close()


def calculate_keyword_overlap(article_keywords, cluster_tokens, hub_tokens):
    """Calculate non-hub keyword overlap."""
    article_nonhub = article_keywords - hub_tokens
    cluster_nonhub = cluster_tokens - hub_tokens
    shared_nonhub = len(article_nonhub & cluster_nonhub)
    return shared_nonhub


def calculate_title_similarity(model, article_title, cluster_titles):
    """Calculate title embedding similarity."""
    if not model or not article_title.strip() or not cluster_titles:
        return 0.0

    try:
        # Get embeddings
        article_emb = model.encode([article_title])
        cluster_embs = model.encode(cluster_titles)

        # Calculate cosine similarity with cluster centroid
        cluster_centroid = np.mean(cluster_embs, axis=0)

        # Cosine similarity
        dot_product = np.dot(article_emb[0], cluster_centroid)
        norm_a = np.linalg.norm(article_emb[0])
        norm_c = np.linalg.norm(cluster_centroid)

        if norm_a == 0 or norm_c == 0:
            return 0.0

        similarity = dot_product / (norm_a * norm_c)
        return float(similarity)

    except Exception as e:
        logger.debug(f"Error calculating title similarity: {e}")
        return 0.0


def attach_orphans(
    conn, orphans, clusters, hub_tokens, model=None, cos_threshold=0.89, min_shared=1
):
    """Attach orphans to clusters based on keyword overlap and cosine similarity."""
    attachments = []

    for orphan in orphans:
        best_cluster = None
        best_score = 0.0

        for cluster_id, cluster_info in clusters.items():
            # Calculate keyword overlap (non-hub only)
            shared_nonhub = calculate_keyword_overlap(
                orphan["keywords"], cluster_info["anchor_tokens"], hub_tokens
            )

            if shared_nonhub < min_shared:
                continue

            # Calculate title similarity if model available
            title_sim = 0.0
            if model:
                title_sim = calculate_title_similarity(
                    model, orphan["title"], cluster_info["titles"]
                )

            # Scoring: prioritize title similarity if available, else keyword overlap
            if model and title_sim >= cos_threshold:
                score = title_sim + (shared_nonhub * 0.1)  # Boost for keyword overlap
            elif shared_nonhub >= 2:  # Fallback to strong keyword overlap
                score = shared_nonhub * 0.1
            else:
                continue

            if score > best_score:
                best_score = score
                best_cluster = cluster_id

        if best_cluster:
            attachments.append(
                {
                    "article_id": orphan["id"],
                    "cluster_id": best_cluster,
                    "score": best_score,
                    "shared_keywords": calculate_keyword_overlap(
                        orphan["keywords"],
                        clusters[best_cluster]["anchor_tokens"],
                        hub_tokens,
                    ),
                }
            )

    logger.info(f"Found {len(attachments)} orphans to attach")
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

        # Log attachment stats
        for cluster_id, added_count in cluster_updates.items():
            logger.info(f"  Cluster {cluster_id[:8]}: +{added_count} articles")

        return len(attachments)

    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving attachments: {e}")
        return 0
    finally:
        cur.close()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Attach orphaned articles to clusters")
    parser.add_argument("--window", type=int, default=300, help="Time window in hours")
    parser.add_argument(
        "--cos", type=float, default=0.89, help="Cosine similarity threshold"
    )
    parser.add_argument(
        "--min_shared", type=int, default=1, help="Minimum shared non-hub keywords"
    )

    args = parser.parse_args()

    logger.info(
        f"Starting orphan attach pass (window={args.window}h, cos_threshold={args.cos})"
    )

    conn = get_db_connection()

    try:
        # Load components
        model = load_sentence_transformer()
        hub_tokens = get_hub_tokens(conn)
        clustered_articles = get_clustered_articles(conn)
        clusters = get_cluster_info(conn)
        orphans = get_orphan_articles(conn, args.window, clustered_articles)

        if not orphans:
            logger.info("No orphan articles to process")
            return 0

        if not clusters:
            logger.info("No clusters available for attachment")
            return 0

        # Find and save attachments
        attachments = attach_orphans(
            conn, orphans, clusters, hub_tokens, model, args.cos, args.min_shared
        )

        attached_count = save_attachments(conn, attachments)

        logger.info(f"Orphan attach pass completed: {attached_count} articles attached")
        return 0

    except Exception as e:
        logger.error(f"Error in orphan attach pass: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
