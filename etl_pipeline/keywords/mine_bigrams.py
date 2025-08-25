#!/usr/bin/env python3
"""
Bigram Mining for Strategic Narrative Intelligence
Mines stable title bigrams using PMI (Pointwise Mutual Information) scoring.
"""

import argparse
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from math import log2

import psycopg2
from psycopg2.extras import execute_batch

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


def parse_time_window(window_str):
    """Parse time window string like '30d', '7d', etc."""
    if window_str.endswith("d"):
        days = int(window_str[:-1])
        return timedelta(days=days)
    else:
        raise ValueError(f"Unsupported window format: {window_str}")


def tokenize_title(title):
    """Tokenize title into clean words."""
    if not title:
        return []

    # Convert to lowercase and split on non-alphanumeric characters
    words = re.findall(r"\b[a-zA-Z]{2,}\b", title.lower())

    # Filter out common stop words
    stop_words = {
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
        "from",
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
        "must",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "he",
        "she",
        "they",
        "we",
        "you",
        "i",
        "me",
        "him",
        "her",
        "them",
        "us",
        "my",
        "your",
        "his",
        "their",
        "our",
    }

    return [word for word in words if word not in stop_words and len(word) >= 2]


def calculate_pmi(bigram_count, word1_count, word2_count, total_bigrams, total_words):
    """Calculate Pointwise Mutual Information for a bigram."""
    if bigram_count == 0 or word1_count == 0 or word2_count == 0:
        return 0.0

    # PMI = log2(P(x,y) / (P(x) * P(y)))
    p_xy = bigram_count / total_bigrams
    p_x = word1_count / total_words
    p_y = word2_count / total_words

    if p_x * p_y == 0:
        return 0.0

    return log2(p_xy / (p_x * p_y))


def mine_title_bigrams(conn, window, min_count=3, min_pmi=3.0):
    """Mine stable bigrams from article titles."""
    cur = conn.cursor()

    # Get articles from time window
    window_start = datetime.now() - window

    logger.info(f"Mining bigrams from articles since {window_start}")

    cur.execute(
        """
        SELECT title 
        FROM articles 
        WHERE language = 'EN' 
        AND published_at >= %s 
        AND title IS NOT NULL
        AND LENGTH(title) > 10
    """,
        (window_start,),
    )

    titles = [row[0] for row in cur.fetchall()]
    logger.info(f"Processing {len(titles)} article titles")

    # Count word frequencies and bigrams
    word_counts = Counter()
    bigram_counts = Counter()

    for title in titles:
        tokens = tokenize_title(title)

        # Count individual words
        for token in tokens:
            word_counts[token] += 1

        # Count bigrams
        for i in range(len(tokens) - 1):
            bigram = (tokens[i], tokens[i + 1])
            bigram_counts[bigram] += 1

    total_words = sum(word_counts.values())
    total_bigrams = sum(bigram_counts.values())

    logger.info(
        f"Found {len(word_counts)} unique words, {len(bigram_counts)} unique bigrams"
    )

    # Filter and score bigrams
    stable_bigrams = []

    for (word1, word2), count in bigram_counts.items():
        if count >= min_count:
            pmi = calculate_pmi(
                count,
                word_counts[word1],
                word_counts[word2],
                total_bigrams,
                total_words,
            )

            if pmi >= min_pmi:
                bigram_text = f"{word1} {word2}"
                stable_bigrams.append(
                    {
                        "bigram": bigram_text,
                        "count": count,
                        "pmi": pmi,
                        "word1": word1,
                        "word2": word2,
                    }
                )

    # Sort by PMI score descending
    stable_bigrams.sort(key=lambda x: x["pmi"], reverse=True)

    logger.info(
        f"Found {len(stable_bigrams)} stable bigrams (min_count={min_count}, min_pmi={min_pmi})"
    )

    cur.close()
    return stable_bigrams


def update_canonicalization_with_bigrams(conn, bigrams):
    """Update keyword_canon_map with discovered bigrams."""
    cur = conn.cursor()

    logger.info(f"Updating canonicalization with {len(bigrams)} bigrams")

    # Prepare data for batch insert/update
    canon_updates = []

    for bigram_info in bigrams:
        bigram = bigram_info["bigram"]
        pmi = bigram_info["pmi"]

        # Use PMI as confidence score (normalize to 0-1 range)
        # PMI typically ranges from -∞ to +∞, but our threshold is 3+
        confidence = min(1.0, pmi / 10.0)  # Scale down for reasonable confidence

        canon_updates.append(
            (
                bigram.lower(),  # token_norm
                bigram.lower(),  # canon_text (bigram is its own canonical form)
                confidence,
                "bigram",  # concept_cluster
            )
        )

    # Insert new canonicalizations (ignore duplicates)
    if canon_updates:
        execute_batch(
            cur,
            """
            INSERT INTO keyword_canon_map (token_norm, canon_text, confidence, concept_cluster, created_at, updated_at)
            VALUES (%s, %s, %s, %s, now(), now())
            ON CONFLICT (token_norm) DO UPDATE SET
                canon_text = EXCLUDED.canon_text,
                confidence = GREATEST(keyword_canon_map.confidence, EXCLUDED.confidence),
                concept_cluster = COALESCE(keyword_canon_map.concept_cluster, EXCLUDED.concept_cluster),
                updated_at = now()
            """,
            canon_updates,
        )

        conn.commit()
        logger.info(f"Updated {len(canon_updates)} canonicalization entries")

    cur.close()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Mine stable title bigrams")
    parser.add_argument("--window", default="30d", help="Time window (e.g., 30d, 7d)")
    parser.add_argument(
        "--min_count", type=int, default=3, help="Minimum bigram frequency"
    )
    parser.add_argument("--min_pmi", type=float, default=3.5, help="Minimum PMI score")

    args = parser.parse_args()

    try:
        window = parse_time_window(args.window)
    except ValueError as e:
        logger.error(f"Invalid window format: {e}")
        return 1

    logger.info(
        f"Starting bigram mining with window={args.window}, min_count={args.min_count}, min_pmi={args.min_pmi}"
    )

    conn = get_db_connection()

    try:
        # Mine bigrams
        bigrams = mine_title_bigrams(conn, window, args.min_count, args.min_pmi)

        if not bigrams:
            logger.warning("No stable bigrams found with current parameters")
            return 0

        # Show top bigrams
        logger.info("Top 10 discovered bigrams:")
        for i, bigram_info in enumerate(bigrams[:10], 1):
            logger.info(
                f"{i:2d}. '{bigram_info['bigram']}' (count={bigram_info['count']}, PMI={bigram_info['pmi']:.2f})"
            )

        # Update canonicalization
        update_canonicalization_with_bigrams(conn, bigrams)

        logger.info("Bigram mining completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during bigram mining: {e}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())
