#!/usr/bin/env python3
"""
Regenerate all keywords using the improved extraction system.
Clean out garbage keywords and create high-quality ones.
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import psycopg2

# Add the ETL pipeline to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "etl_pipeline"))

from extraction.dynamic_keyword_extractor import extract_dynamic_keywords

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


def clear_existing_keywords(conn):
    """Clear existing keywords to start fresh"""
    logger.info("Clearing existing keywords and article-keyword mappings")

    cur = conn.cursor()
    try:
        # Clear article-keyword mappings first (foreign key constraint)
        cur.execute("DELETE FROM article_keywords")
        deleted_mappings = cur.rowcount

        # Clear keywords table
        cur.execute("DELETE FROM keywords")
        deleted_keywords = cur.rowcount

        # Reset sequence (try common naming patterns)
        try:
            cur.execute("ALTER SEQUENCE keywords_id_seq RESTART WITH 1")
        except Exception:
            try:
                cur.execute("ALTER SEQUENCE keywords_seq RESTART WITH 1")
            except Exception:
                logger.info("Could not find keywords sequence to reset, continuing...")

        logger.info(
            f"Cleared {deleted_mappings} article-keyword mappings and {deleted_keywords} keywords"
        )

    finally:
        cur.close()


def get_articles_for_processing(conn, hours_back=300):
    """Get articles for keyword processing"""
    cur = conn.cursor()
    try:
        # Get articles from last N hours
        query = """
            SELECT id, title, content, summary, published_at, language
            FROM articles 
            WHERE published_at >= %s
            ORDER BY published_at DESC
        """

        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cur.execute(query, (cutoff_time,))

        articles = cur.fetchall()
        logger.info(f"Found {len(articles)} articles from last {hours_back} hours")

        return articles

    finally:
        cur.close()


def store_keywords_batch(conn, keyword_results):
    """Store extracted keywords in database with full lifecycle fields"""
    if not keyword_results:
        return

    cur = conn.cursor()
    try:
        from datetime import datetime

        now = datetime.now()

        # Process each keyword result with full lifecycle data
        for result in keyword_results:
            article_id = result.article_id

            for rank, keyword in enumerate(result.keywords, 1):
                # Get or create keyword with full fields
                keyword_id = get_or_create_keyword_with_lifecycle(
                    cur,
                    keyword.text,
                    keyword.keyword_type,
                    keyword.entity_label,
                    float(keyword.strategic_score),
                    now,
                )

                # Create article-keyword relationship with full metadata
                cur.execute(
                    """
                    INSERT INTO article_keywords (
                        article_id, keyword_id, extraction_method, extraction_score,
                        strategic_score, keyword_rank, appears_in_title, appears_in_summary,
                        position_importance
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (article_id, keyword_id) DO NOTHING
                """,
                    (
                        article_id,
                        keyword_id,
                        keyword.extraction_method,
                        float(keyword.extraction_score),
                        float(keyword.strategic_score),
                        rank,
                        False,  # TODO: Implement title detection
                        False,  # TODO: Implement summary detection
                        0.0,  # TODO: Implement position scoring
                    ),
                )

        logger.info(
            f"Stored keywords with full lifecycle data for {len(keyword_results)} articles"
        )

    except Exception as e:
        logger.error(f"Failed to store keywords: {e}")
        raise
    finally:
        cur.close()


def get_or_create_keyword_with_lifecycle(
    cur, keyword_text, keyword_type, entity_label, strategic_score, now
):
    """Get existing keyword or create new one with full lifecycle fields"""
    import uuid

    # Try to find existing keyword
    cur.execute("SELECT id FROM keywords WHERE keyword = %s", (keyword_text,))
    existing = cur.fetchone()

    if existing:
        # Update existing keyword
        keyword_id = existing[0]
        cur.execute(
            """
            UPDATE keywords 
            SET base_frequency = base_frequency + 1,
                recent_frequency = recent_frequency + 1,
                last_seen = %s,
                updated_at = %s,
                strategic_score = GREATEST(strategic_score, %s)
            WHERE id = %s
        """,
            (now, now, float(strategic_score), keyword_id),
        )
        return keyword_id

    # Create new keyword with full lifecycle fields
    keyword_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO keywords (
            id, keyword, keyword_type, entity_label,
            strategic_score, base_frequency, recent_frequency,
            first_seen, last_seen, lifecycle_stage, trending_score, peak_frequency
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """,
        (
            keyword_id,
            keyword_text,
            keyword_type or "phrase",  # Default to phrase if no type
            entity_label,
            float(strategic_score),
            1,  # base_frequency (first occurrence)
            1,  # recent_frequency
            now,  # first_seen
            now,  # last_seen
            "active",  # lifecycle_stage
            0.0,  # trending_score (calculated later)
            1,  # peak_frequency (start with 1)
        ),
    )

    return keyword_id


def main():
    """Main regeneration function"""
    logger.info("Starting keyword regeneration with improved extractor")

    try:
        conn = get_db_connection()

        try:
            # Clear existing keywords
            clear_existing_keywords(conn)
            conn.commit()  # Commit the clearing

            # Get articles for processing
            articles = get_articles_for_processing(conn, hours_back=300)

            if not articles:
                logger.info("No articles found for processing")
                return

            # Process articles in batches
            batch_size = 50
            total_processed = 0
            batch_results = []

            # Statistics tracking
            total_stats = {
                "kept_keywords": 0,
                "dropped_html": 0,
                "dropped_temporal": 0,
                "dropped_boilerplate": 0,
                "dropped_numbers": 0,
                "kept_whitelist": 0,
                "kept_patterns": 0,
                "skipped_non_english": 0,
            }

            for i, (
                article_id,
                title,
                content,
                summary,
                published_at,
                language,
            ) in enumerate(articles):
                try:
                    # English-only filter for MVP
                    article_language = language or "en"
                    if article_language != "en":
                        total_stats["skipped_non_english"] += 1
                        logger.debug(
                            f"Skipped non-English article {article_id} (language: {article_language})"
                        )
                        continue

                    # Extract keywords using improved system
                    result = extract_dynamic_keywords(
                        str(article_id),
                        title or "",
                        content or "",
                        summary,
                        article_language,
                    )

                    batch_results.append(result)

                    # Accumulate statistics
                    for key, value in result.filter_stats.items():
                        total_stats[key] += value

                    total_processed += 1

                    # Process batch
                    if len(batch_results) >= batch_size:
                        store_keywords_batch(conn, batch_results)
                        conn.commit()  # Commit after each batch
                        batch_results = []

                    if total_processed % 100 == 0:
                        logger.info(
                            f"Processed {total_processed}/{len(articles)} articles"
                        )

                except Exception as e:
                    logger.error(f"Failed to process article {article_id}: {e}")
                    continue

            # Process remaining batch
            if batch_results:
                store_keywords_batch(conn, batch_results)
                conn.commit()  # Commit final batch

            # Final commit (redundant but safe)
            conn.commit()

            # Print final statistics
            logger.info("Keyword regeneration completed successfully")
            logger.info(f"Processed {total_processed} articles")
            logger.info("Filter Statistics:")
            for key, value in total_stats.items():
                logger.info(f"  {key}: {value}")

            # Show sample of new keywords
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT k.keyword, COUNT(*) as article_count, AVG(ak.score) as avg_score
                    FROM keywords k
                    JOIN article_keywords ak ON k.id = ak.keyword_id
                    GROUP BY k.keyword
                    ORDER BY avg_score DESC, article_count DESC
                    LIMIT 20
                """
                )

                logger.info("Top 20 highest quality keywords:")
                for keyword, count, score in cur.fetchall():
                    logger.info(
                        f"  {keyword} (articles: {count}, avg_score: {score:.3f})"
                    )

            finally:
                cur.close()

        except Exception as e:
            conn.rollback()
            logger.error(f"Keyword regeneration failed: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to regenerate keywords: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
