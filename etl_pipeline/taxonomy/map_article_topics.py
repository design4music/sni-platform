#!/usr/bin/env python3
"""
Article topic mapping script for CLUST-1 MVP.
Maps articles to taxonomy topics using keywords and fuzzy matching.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta

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


def get_recent_articles(conn, hours_back=72):
    """Get articles from the last N hours with their keywords."""
    cur = conn.cursor()
    try:
        # Get articles with their keywords (English-only for MVP)
        query = """
            SELECT 
                a.id,
                a.title,
                a.content,
                a.published_at,
                a.language,
                COALESCE(
                    array_agg(DISTINCT k.keyword) FILTER (WHERE k.keyword IS NOT NULL), 
                    ARRAY[]::text[]
                ) as keywords
            FROM articles a
            LEFT JOIN article_keywords ak ON a.id = ak.article_id
            LEFT JOIN keywords k ON ak.keyword_id = k.id
            WHERE a.published_at >= %s 
              AND (a.language = 'en' OR a.language IS NULL)
            GROUP BY a.id, a.title, a.content, a.published_at, a.language
            ORDER BY a.published_at DESC
        """

        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cur.execute(query, (cutoff_time,))

        articles = cur.fetchall()
        logger.info(f"Found {len(articles)} English articles from last {hours_back} hours")
        return articles

    finally:
        cur.close()


def get_taxonomy_data(conn):
    """Get taxonomy topics and aliases for matching."""
    cur = conn.cursor()
    try:
        # Get all topics
        cur.execute("SELECT topic_id, name, source FROM taxonomy_topics")
        topics = {row[0]: {"name": row[1], "source": row[2]} for row in cur.fetchall()}

        # Get all aliases with trigram matching setup
        cur.execute("SELECT topic_id, alias, lang FROM taxonomy_aliases")
        aliases = cur.fetchall()

        logger.info(f"Loaded {len(topics)} topics and {len(aliases)} aliases")
        return topics, aliases

    finally:
        cur.close()


def match_article_to_topics(
    conn, article_id, title, content, keywords, topics, aliases
):
    """Match article to topics using keywords and fuzzy matching."""
    matched_topics = []

    # Combine title and content for text matching
    article_text = f"{title} {content or ''}".lower()

    cur = conn.cursor()
    try:
        # 1. Exact alias match in taxonomy_aliases (score 1.0)
        if aliases:
            for topic_id, alias, lang in aliases:
                if alias.lower() in article_text:
                    matched_topics.append((article_id, topic_id, 1.0, "exact_alias"))

        # 2. Exact keyword == taxonomy_topics.name (score 0.8)
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for topic_id, topic_data in topics.items():
                if keyword_lower == topic_data["name"].lower():
                    matched_topics.append((article_id, topic_id, 0.8, "exact_keyword"))

        # 3. Fuzzy matching using pg_trgm (score 0.6)
        # Find aliases with similarity >= 0.4 to article keywords
        for keyword in keywords:
            fuzzy_query = """
                SELECT topic_id, alias, similarity(alias, %s) as sim
                FROM taxonomy_aliases
                WHERE similarity(alias, %s) >= 0.4
                ORDER BY sim DESC
                LIMIT 5
            """
            cur.execute(fuzzy_query, (keyword, keyword))
            fuzzy_matches = cur.fetchall()

            for topic_id, alias, similarity in fuzzy_matches:
                # Score based on similarity: 0.4 -> 0.6, 1.0 -> 0.6 (fuzzy bonus)
                score = 0.6 * similarity
                matched_topics.append((article_id, topic_id, score, "fuzzy_alias"))

    finally:
        cur.close()

    # Remove duplicates and keep highest score per topic
    topic_scores = {}
    for article_id, topic_id, score, source in matched_topics:
        if topic_id not in topic_scores or score > topic_scores[topic_id][1]:
            topic_scores[topic_id] = (article_id, score, source)

    # Return top 5 topics by score
    top_topics = sorted(topic_scores.items(), key=lambda x: x[1][1], reverse=True)[:5]
    return [
        (article_id, topic_id, score, source)
        for topic_id, (article_id, score, source) in top_topics
    ]


def upsert_article_topics(conn, topic_mappings):
    """Upsert article topics to the database."""
    if not topic_mappings:
        logger.info("No topic mappings to upsert")
        return

    cur = conn.cursor()
    try:
        upsert_sql = """
            INSERT INTO article_topics (article_id, topic_id, score, source)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (article_id, topic_id) DO UPDATE SET
                score = EXCLUDED.score,
                source = EXCLUDED.source
        """
        execute_batch(cur, upsert_sql, topic_mappings)
        logger.info(f"Upserted {len(topic_mappings)} article-topic mappings")

    except Exception as e:
        logger.error(f"Failed to upsert article topics: {e}")
        raise
    finally:
        cur.close()


def main():
    """Main article topic mapping function."""
    parser = argparse.ArgumentParser(description="Map articles to taxonomy topics")
    parser.add_argument(
        "--since",
        type=int,
        default=72,
        help="Hours back to process articles (default: 72)",
    )
    args = parser.parse_args()

    logger.info(f"Starting article topic mapping for last {args.since} hours")

    try:
        conn = get_db_connection()

        try:
            # Get recent articles with keywords
            articles = get_recent_articles(conn, args.since)
            if not articles:
                logger.info("No recent articles found, exiting")
                return

            # Get taxonomy data
            topics, aliases = get_taxonomy_data(conn)
            if not topics:
                logger.info("No taxonomy topics found, exiting")
                return

            # Process each article
            all_mappings = []
            processed_count = 0

            for article_id, title, content, published_at, language, keywords in articles:
                if keywords:  # Only process articles with keywords
                    topic_matches = match_article_to_topics(
                        conn, article_id, title, content, keywords, topics, aliases
                    )
                    all_mappings.extend(topic_matches)
                    processed_count += 1

                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count} articles")

            # Upsert all mappings
            upsert_article_topics(conn, all_mappings)

            # Commit transaction
            conn.commit()

            logger.info(
                f"Article topic mapping completed. Processed {processed_count} articles, "
                f"created {len(all_mappings)} topic mappings"
            )

        except Exception as e:
            conn.rollback()
            logger.error(f"Article topic mapping failed: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to map article topics: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
