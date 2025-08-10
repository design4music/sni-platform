#!/usr/bin/env python3
"""
Cluster labeling script for CLUST-1 MVP.
Generates human-readable labels for clusters based on topics and content.
"""

import logging
import os
import re
import sys
from collections import Counter

import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common stopwords for title analysis
STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "me",
    "him",
    "her",
    "us",
    "them",
    "my",
    "your",
    "his",
    "our",
    "their",
    "up",
    "down",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "more",
    "most",
    "other",
    "some",
    "any",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "now",
}


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def get_topic_names(conn, topic_ids):
    """Get human-readable names for topic IDs."""
    if not topic_ids:
        return []

    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT topic_id, name FROM taxonomy_topics WHERE topic_id = ANY(%s)",
            (topic_ids,),
        )
        topic_map = dict(cur.fetchall())
        return [topic_map.get(tid, tid) for tid in topic_ids]
    finally:
        cur.close()


def extract_bigrams(text):
    """Extract meaningful bigrams from text."""
    if not text:
        return []

    # Clean and tokenize
    text = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in text.split() if w not in STOPWORDS and len(w) > 2]

    # Generate bigrams
    bigrams = []
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        bigrams.append(bigram)

    return bigrams


def get_clusters_to_label(conn):
    """Get clusters that need labels."""
    cur = conn.cursor()
    try:
        query = """
            SELECT 
                ac.cluster_id, 
                ac.top_topics, 
                ac.size,
                array_agg(DISTINCT a.title) as titles
            FROM article_clusters ac
            LEFT JOIN article_cluster_members acm ON ac.cluster_id = acm.cluster_id
            LEFT JOIN articles a ON acm.article_id = a.id
            WHERE ac.label IS NULL
            GROUP BY ac.cluster_id, ac.top_topics, ac.size
            ORDER BY ac.size DESC
        """
        cur.execute(query)
        return cur.fetchall()
    finally:
        cur.close()


def generate_label_from_topics(conn, top_topics):
    """Generate label from topic names."""
    if not top_topics:
        return None

    topic_names = get_topic_names(conn, top_topics[:2])  # Use first 2 topics
    if topic_names:
        # Clean topic names and join
        clean_names = []
        for name in topic_names:
            # Remove common prefixes/suffixes, clean format
            clean_name = re.sub(r"^(IPTC_|GDELT_)", "", name)
            clean_name = clean_name.replace("_", " ").title()
            clean_names.append(clean_name)

        return " / ".join(clean_names)

    return None


def generate_label_from_titles(titles):
    """Generate label from most frequent bigrams in titles."""
    if not titles:
        return None

    all_bigrams = []
    for title in titles:
        if title:
            bigrams = extract_bigrams(title)
            all_bigrams.extend(bigrams)

    if not all_bigrams:
        return None

    # Find most frequent bigrams
    bigram_counts = Counter(all_bigrams)
    most_common = bigram_counts.most_common(3)

    if most_common and most_common[0][1] >= 2:  # At least 2 occurrences
        return most_common[0][0].title()

    return None


def update_cluster_labels(conn, cluster_labels):
    """Update cluster labels in database."""
    if not cluster_labels:
        logger.info("No cluster labels to update")
        return

    cur = conn.cursor()
    try:
        for cluster_id, label in cluster_labels:
            cur.execute(
                "UPDATE article_clusters SET label = %s WHERE cluster_id = %s",
                (label, cluster_id),
            )

        logger.info(f"Updated labels for {len(cluster_labels)} clusters")
    finally:
        cur.close()


def main():
    """Main cluster labeling function."""
    logger.info("Starting cluster labeling")

    try:
        conn = get_db_connection()

        try:
            # Get clusters that need labels
            clusters = get_clusters_to_label(conn)

            if not clusters:
                logger.info("No clusters found that need labeling")
                return

            logger.info(f"Found {len(clusters)} clusters to label")

            cluster_labels = []

            for cluster_id, top_topics, size, titles in clusters:
                label = None

                # Strategy 1: Use topic names
                if top_topics:
                    label = generate_label_from_topics(conn, top_topics)

                # Strategy 2: Fallback to title bigrams
                if not label and titles:
                    label = generate_label_from_titles([t for t in titles if t])

                # Strategy 3: Final fallback
                if not label:
                    if top_topics and len(top_topics) > 0:
                        label = f"Topic {top_topics[0][:8]}..."
                    else:
                        label = f"Cluster {str(cluster_id)[:8]}..."

                cluster_labels.append((cluster_id, label))
                logger.debug(f"Cluster {cluster_id} (size: {size}): '{label}'")

            # Update labels in database
            update_cluster_labels(conn, cluster_labels)

            # Commit changes
            conn.commit()

            logger.info(
                f"Cluster labeling completed. Labeled {len(cluster_labels)} clusters"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Cluster labeling failed: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to label clusters: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
