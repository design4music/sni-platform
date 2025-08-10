#!/usr/bin/env python3
"""
CLUST-1 taxonomy-aware clustering with 4 stages: seed, densify, refine, persist.
Deterministic, LLM-free implementation for scalable clustering.
"""

import argparse
import hashlib
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations

import psycopg2
from psycopg2.extras import execute_batch

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


def generate_topic_key(topic_combo):
    """Generate deterministic hash key for topic combination."""
    sorted_combo = "::".join(sorted(topic_combo))
    return hashlib.sha1(sorted_combo.encode()).hexdigest()


def get_articles_with_topics(conn, hours_back=72, lang=None):
    """Get articles with their top topics from the specified time window."""
    cur = conn.cursor()
    try:
        lang_filter = "AND a.language = %s" if lang else ""
        query_params = [datetime.now() - timedelta(hours=hours_back)]
        if lang:
            query_params.append(lang)

        query = f"""
            SELECT 
                a.id,
                a.title,
                a.published_at,
                a.source_name,
                a.language,
                array_agg(at.topic_id ORDER BY at.score DESC) as topics,
                array_agg(at.score ORDER BY at.score DESC) as scores
            FROM articles a
            JOIN article_topics at ON a.id = at.article_id
            WHERE a.published_at >= %s
            {lang_filter}
            GROUP BY a.id, a.title, a.published_at, a.source_name, a.language
            HAVING COUNT(at.topic_id) >= 1
            ORDER BY a.published_at DESC
        """

        cur.execute(query, query_params)
        articles = cur.fetchall()

        logger.info(
            "Found {} articles with topics from last {} hours{}".format(
                len(articles), hours_back, f" (lang: {lang})" if lang else ""
            )
        )
        return articles

    finally:
        cur.close()


def stage_seed(conn, hours_back=72, lang=None):
    """Stage 1: Create seed clusters based on topic combinations."""
    logger.info("Starting seed stage (window: {}h, lang: {})".format(hours_back, lang))

    articles = get_articles_with_topics(conn, hours_back, lang)
    if not articles:
        logger.warning("No articles with topics found")
        return {}

    # Build topic combinations for each article (top 3 topics)
    topic_combos = defaultdict(list)

    for (
        article_id,
        title,
        published_at,
        source_name,
        language,
        topics,
        scores,
    ) in articles:
        # Take top 3 topics with score > 0
        valid_topics = [topics[i] for i in range(min(3, len(topics))) if scores[i] > 0]

        if len(valid_topics) >= 1:
            # Generate 2-3 topic combinations
            for combo_size in range(2, min(4, len(valid_topics) + 1)):
                if combo_size <= len(valid_topics):
                    for combo in combinations(valid_topics, combo_size):
                        topic_key = generate_topic_key(combo)
                        topic_combos[topic_key].append(
                            {
                                "article_id": article_id,
                                "title": title,
                                "published_at": published_at,
                                "source_name": source_name,
                                "language": language,
                                "topics": list(combo),
                                "combo_size": combo_size,
                            }
                        )

    # Filter seeds: size >= 3 and >= 2 unique sources
    seeds = {}
    for topic_key, members in topic_combos.items():
        if len(members) >= 3:
            unique_sources = set(m["source_name"] for m in members)
            if len(unique_sources) >= 2:
                seeds[topic_key] = {
                    "members": members,
                    "size": len(members),
                    "sources": unique_sources,
                    "topics": members[0]["topics"],  # All members have same topics
                    "lang": lang,
                }

    logger.info("Created {} seed clusters".format(len(seeds)))

    # Store seeds temporarily (in-memory for this MVP)
    return seeds


def get_cosine_similarity(conn, article_id1, article_id2):
    """Get cosine similarity between two articles using title embeddings."""
    cur = conn.cursor()
    try:
        query = """
            SELECT 
                ae1.title_embedding <=> ae2.title_embedding as distance
            FROM article_embeddings ae1, article_embeddings ae2
            WHERE ae1.article_id = %s AND ae2.article_id = %s
            AND ae1.title_embedding IS NOT NULL 
            AND ae2.title_embedding IS NOT NULL
        """
        cur.execute(query, (article_id1, article_id2))
        result = cur.fetchone()

        if result:
            # Convert cosine distance to similarity
            return 1.0 - result[0]
        return 0.0

    except Exception as e:
        logger.debug("Error getting cosine similarity: {}".format(e))
        return 0.0
    finally:
        cur.close()


def find_similar_articles(
    conn, seed_member_ids, hours_back=72, lang=None, cos_threshold=0.82
):
    """Find articles similar to seed members using embeddings."""
    if not seed_member_ids:
        return []

    cur = conn.cursor()
    try:
        lang_filter = "AND a.language = %s" if lang else ""
        query_params = [datetime.now() - timedelta(hours=hours_back)]
        if lang:
            query_params.append(lang)

        # Find articles with embeddings in the time window
        query = f"""
            SELECT DISTINCT a.id, a.title, a.published_at, a.source_name, a.language
            FROM articles a
            JOIN article_embeddings ae ON a.id = ae.article_id
            WHERE a.published_at >= %s
            {lang_filter}
            AND ae.title_embedding IS NOT NULL
            AND a.id NOT IN %s
            ORDER BY a.published_at DESC
            LIMIT 1000
        """

        cur.execute(query, query_params + [tuple(seed_member_ids)])
        candidate_articles = cur.fetchall()

        similar_articles = []

        # Check cosine similarity against seed members (limit to k=20 per seed member)
        for (
            candidate_id,
            title,
            published_at,
            source_name,
            language,
        ) in candidate_articles:
            max_similarity = 0.0

            # Check against up to 5 seed members for efficiency
            for seed_member_id in seed_member_ids[:5]:
                similarity = get_cosine_similarity(conn, candidate_id, seed_member_id)
                max_similarity = max(max_similarity, similarity)

                if max_similarity >= cos_threshold:
                    break

            if max_similarity >= cos_threshold:
                similar_articles.append(
                    {
                        "article_id": candidate_id,
                        "title": title,
                        "published_at": published_at,
                        "source_name": source_name,
                        "language": language,
                        "similarity": max_similarity,
                    }
                )

        return similar_articles[:20]  # Limit to top 20 similar articles per seed

    finally:
        cur.close()


def stage_densify(conn, seeds, hours_back=72, lang=None, cos_threshold=0.82):
    """Stage 2: Densify clusters by adding similar articles."""
    logger.info("Starting densify stage (cos_threshold: {})".format(cos_threshold))

    if not seeds:
        logger.warning("No seeds to densify")
        return seeds

    densified_seeds = {}

    for topic_key, seed_data in seeds.items():
        logger.debug(
            "Densifying seed {} (size: {})".format(topic_key, seed_data["size"])
        )

        # Get articles with shared topics
        seed_member_ids = [m["article_id"] for m in seed_data["members"]]
        seed_topics = set(seed_data["topics"])

        # Find articles that share >= 2 topics OR share >= 1 topic + high cosine similarity
        cur = conn.cursor()
        try:
            lang_filter = "AND a.language = %s" if lang else ""
            query_params = [
                datetime.now() - timedelta(hours=hours_back),
                tuple(seed_member_ids),
            ]
            if lang:
                query_params.append(lang)

            # Find articles with topic overlap
            query = f"""
                SELECT 
                    a.id, a.title, a.published_at, a.source_name, a.language,
                    array_agg(at.topic_id) as topics,
                    array_agg(at.score) as scores
                FROM articles a
                JOIN article_topics at ON a.id = at.article_id
                WHERE a.published_at >= %s
                AND a.id NOT IN %s
                {lang_filter}
                GROUP BY a.id, a.title, a.published_at, a.source_name, a.language
                HAVING array_agg(at.topic_id) && %s
            """

            cur.execute(query, query_params + [list(seed_topics)])
            candidates = cur.fetchall()

            added_members = []

            for (
                candidate_id,
                title,
                published_at,
                source_name,
                language,
                topics,
                scores,
            ) in candidates:
                candidate_topics = set(topics)
                topic_overlap = len(seed_topics.intersection(candidate_topics))

                should_add = False

                # Rule 1: >= 2 shared topics
                if topic_overlap >= 2:
                    should_add = True
                    reason = "topic_overlap_2+"

                # Rule 2: >= 1 shared topic + high cosine similarity
                elif topic_overlap >= 1:
                    # Check cosine similarity with seed members
                    max_similarity = 0.0
                    for seed_member_id in seed_member_ids[
                        :3
                    ]:  # Check against top 3 seed members
                        similarity = get_cosine_similarity(
                            conn, candidate_id, seed_member_id
                        )
                        max_similarity = max(max_similarity, similarity)

                        if max_similarity >= cos_threshold:
                            break

                    if max_similarity >= cos_threshold:
                        should_add = True
                        reason = f"topic_overlap_1+cos_{max_similarity:.3f}"

                if should_add:
                    added_members.append(
                        {
                            "article_id": candidate_id,
                            "title": title,
                            "published_at": published_at,
                            "source_name": source_name,
                            "language": language,
                            "topics": topics,
                            "reason": reason,
                        }
                    )

            # Update seed with new members
            all_members = seed_data["members"] + added_members
            densified_seeds[topic_key] = {
                **seed_data,
                "members": all_members,
                "size": len(all_members),
                "added_count": len(added_members),
            }

            if added_members:
                logger.debug(
                    "Added {} members to seed {}".format(len(added_members), topic_key)
                )

        finally:
            cur.close()

    total_added = sum(s.get("added_count", 0) for s in densified_seeds.values())
    logger.info(
        "Densify complete. Added {} articles across {} seeds".format(
            total_added, len(densified_seeds)
        )
    )

    return densified_seeds


def stage_refine(seeds, min_size=80):
    """Stage 3: Refine oversized clusters (optional, simplified for MVP)."""
    logger.info("Starting refine stage (min_size: {})".format(min_size))

    # For MVP, just log oversized clusters - actual DBSCAN refinement would be complex
    oversized_count = 0
    for topic_key, seed_data in seeds.items():
        if seed_data["size"] > min_size:
            oversized_count += 1
            logger.debug(
                "Cluster {} is oversized: {} members".format(
                    topic_key, seed_data["size"]
                )
            )

    if oversized_count > 0:
        logger.info(
            "Found {} oversized clusters (refinement skipped in MVP)".format(
                oversized_count
            )
        )

    return seeds


def compute_cluster_cohesion(members):
    """Compute cluster cohesion score based on multiple factors."""
    if not members:
        return 0.0

    # Factor 1: Source diversity (0-1)
    unique_sources = set(m["source_name"] for m in members)
    source_diversity = min(len(unique_sources) / 5.0, 1.0)  # Normalize to max 5 sources

    # Factor 2: Topic overlap (simplified - assume high since they're in same cluster)
    topic_overlap = 0.8  # Static for MVP since members share topics

    # Factor 3: Time span penalty
    timestamps = [m["published_at"] for m in members]
    if len(timestamps) > 1:
        time_span = (max(timestamps) - min(timestamps)).total_seconds() / 3600  # Hours
        time_penalty = -0.1 if time_span > 72 else 0.0
    else:
        time_penalty = 0.0

    # Weighted combination
    cohesion = (
        0.45 * 0.8  # avg_cos (simplified)
        + 0.35 * topic_overlap
        + 0.20 * source_diversity
        + time_penalty
    )

    return max(0.0, min(1.0, cohesion))


def stage_persist(conn, seeds):
    """Stage 4: Persist clusters to database."""
    logger.info("Starting persist stage")

    if not seeds:
        logger.warning("No seeds to persist")
        return

    cur = conn.cursor()

    try:
        # Clear existing clusters (for clean run)
        cur.execute("DELETE FROM article_cluster_members")
        cur.execute("DELETE FROM article_clusters")

        cluster_rows = []
        member_rows = []

        for topic_key, seed_data in seeds.items():
            members = seed_data["members"]
            if not members:
                continue

            # Compute time window
            timestamps = [m["published_at"] for m in members]
            time_start = min(timestamps)
            time_end = max(timestamps)
            time_window = f"[{time_start},{time_end}]"

            # Compute cohesion
            cohesion = compute_cluster_cohesion(members)

            # Create cluster record
            cluster_rows.append(
                (
                    topic_key,
                    seed_data["topics"],
                    None,  # label (to be filled by labeler)
                    seed_data.get("lang"),
                    time_window,
                    len(members),
                    cohesion,
                )
            )

            # Create member records
            for member in members:
                member_rows.append(
                    (
                        topic_key,  # Will be replaced with actual cluster_id after insert
                        member["article_id"],
                        1.0,  # weight (simplified)
                    )
                )

        # Insert clusters
        insert_cluster_sql = """
            INSERT INTO article_clusters (topic_key, top_topics, label, lang, time_window, size, cohesion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_batch(cur, insert_cluster_sql, cluster_rows)

        # Get cluster IDs for members
        cur.execute(
            """
            SELECT cluster_id, topic_key 
            FROM article_clusters 
            WHERE topic_key = ANY(%s)
        """,
            ([topic_key for topic_key, _ in seeds.items()],),
        )

        topic_key_to_cluster_id = {row[1]: row[0] for row in cur.fetchall()}

        # Update member rows with actual cluster IDs
        updated_member_rows = []
        for topic_key, article_id, weight in member_rows:
            cluster_id = topic_key_to_cluster_id.get(topic_key)
            if cluster_id:
                updated_member_rows.append((cluster_id, article_id, weight))

        # Insert members
        insert_member_sql = """
            INSERT INTO article_cluster_members (cluster_id, article_id, weight)
            VALUES (%s, %s, %s)
        """
        execute_batch(cur, insert_member_sql, updated_member_rows)

        logger.info(
            "Persisted {} clusters with {} total members".format(
                len(cluster_rows), len(updated_member_rows)
            )
        )

    except Exception as e:
        logger.error("Failed to persist clusters: {}".format(e))
        raise
    finally:
        cur.close()


def main():
    """Main clustering function with stage selection."""
    parser = argparse.ArgumentParser(description="CLUST-1 taxonomy-aware clustering")
    parser.add_argument(
        "--stage",
        choices=["seed", "densify", "refine", "persist"],
        required=True,
        help="Clustering stage to run",
    )
    parser.add_argument(
        "--window", type=int, default=72, help="Time window in hours (default: 72)"
    )
    parser.add_argument("--lang", type=str, help="Language filter (e.g., en, de)")
    parser.add_argument(
        "--cos",
        type=float,
        default=0.82,
        help="Cosine similarity threshold (default: 0.82)",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=80,
        help="Minimum size for refine stage (default: 80)",
    )

    args = parser.parse_args()

    logger.info("Starting CLUST-1 stage: {}".format(args.stage))

    try:
        conn = get_db_connection()

        try:
            if args.stage == "seed":
                seeds = stage_seed(conn, args.window, args.lang)
                logger.info("Seed stage completed with {} seeds".format(len(seeds)))
                # Store seeds in a simple way for MVP (could use Redis/file for production)

            elif args.stage == "densify":
                # For MVP, re-run seed stage then densify
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                logger.info("Densify stage completed")

            elif args.stage == "refine":
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                    seeds = stage_refine(seeds, args.min_size)
                logger.info("Refine stage completed")

            elif args.stage == "persist":
                seeds = stage_seed(conn, args.window, args.lang)
                if seeds:
                    seeds = stage_densify(conn, seeds, args.window, args.lang, args.cos)
                    seeds = stage_refine(seeds, args.min_size)
                    stage_persist(conn, seeds)
                conn.commit()
                logger.info("Persist stage completed")

        except Exception as e:
            conn.rollback()
            logger.error("CLUST-1 stage {} failed: {}".format(args.stage, e))
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error("Failed to run CLUST-1: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
