#!/usr/bin/env python3
"""
Nightly Keyword Canonicalization Job
Strategic Narrative Intelligence ETL Pipeline

Scans last 300h tokens from keywords table, applies enhanced canonicalization rules,
and populates/updates keyword_canon_map table.

Run schedule: Nightly or before clustering jobs
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_batch

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from etl_pipeline.keywords.canonicalizer import get_canonicalizer

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


def get_recent_keywords(conn, hours_back=300):
    """Get keywords from articles in the last N hours."""
    logger.info(f"Fetching keywords from last {hours_back} hours...")

    cur = conn.cursor()
    try:
        # Get unique keywords from recent articles
        query = """
            SELECT DISTINCT k.keyword
            FROM keywords k
            JOIN article_keywords ak ON k.id = ak.keyword_id
            JOIN articles a ON ak.article_id = a.id
            WHERE a.published_at >= %s
              AND (a.language = 'EN' OR a.language IS NULL)
            ORDER BY k.keyword
        """

        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        cur.execute(query, (cutoff_time,))

        keywords = [row[0] for row in cur.fetchall()]
        logger.info(f"Found {len(keywords)} unique keywords from recent articles")

        return keywords

    finally:
        cur.close()


def canonicalize_keywords_batch(keywords):
    """Apply enhanced canonicalization to batch of keywords."""
    logger.info(f"Canonicalizing {len(keywords)} keywords...")

    canonicalizer = get_canonicalizer()

    # Process keywords and build mappings
    mappings = []
    stats = {
        "total_processed": 0,
        "kept_canonical": 0,
        "filtered_out": 0,
        "title_stripped": 0,
        "acronym_expanded": 0,
        "demonym_converted": 0,
    }

    for keyword in keywords:
        stats["total_processed"] += 1

        # Get canonical form
        canonical = canonicalizer.normalize_token(keyword)

        if not canonical:
            stats["filtered_out"] += 1
            continue

        stats["kept_canonical"] += 1

        # Detect transformation types for stats
        if any(
            title in keyword.lower()
            for title in ["president", "prime minister", "mr", "ms"]
        ):
            stats["title_stripped"] += 1
        if any(acronym in keyword.lower() for acronym in ["u.s.", "usa", "uk", "eu"]):
            stats["acronym_expanded"] += 1
        if canonical != canonicalizer._normalize_text_basic(keyword):
            if keyword.lower() in canonicalizer.demonym_countries:
                stats["demonym_converted"] += 1

        # Get concept cluster
        concept_cluster = canonicalizer.get_concept_cluster(canonical)

        # Normalize original for lookup key
        token_norm = canonicalizer._normalize_text_basic(keyword)

        mappings.append((token_norm, canonical, 1.0, concept_cluster))

    logger.info(f"Canonicalization stats: {stats}")
    return mappings, stats


def update_canonical_mappings(conn, mappings):
    """Update keyword_canon_map table with new mappings."""
    if not mappings:
        logger.info("No mappings to update")
        return

    logger.info(f"Updating canonical mappings: {len(mappings)} entries")

    cur = conn.cursor()
    try:
        # Clear existing mappings (for fresh rebuild)
        cur.execute("DELETE FROM keyword_canon_map")
        deleted_count = cur.rowcount

        # Insert new mappings
        upsert_sql = """
            INSERT INTO keyword_canon_map (token_norm, canon_text, confidence, concept_cluster)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (token_norm) DO UPDATE SET
                canon_text = EXCLUDED.canon_text,
                confidence = EXCLUDED.confidence,
                concept_cluster = EXCLUDED.concept_cluster,
                updated_at = NOW()
        """

        execute_batch(cur, upsert_sql, mappings)

        logger.info(
            f"Updated canonical mappings: deleted {deleted_count}, inserted {len(mappings)}"
        )

    finally:
        cur.close()


def refresh_materialized_views(conn):
    """Refresh materialized views that depend on canonical mappings."""
    logger.info("Refreshing materialized views...")

    cur = conn.cursor()
    try:
        # Refresh shared_keywords_300h (if it exists)
        try:
            cur.execute("REFRESH MATERIALIZED VIEW shared_keywords_300h")
            logger.info("Refreshed shared_keywords_300h materialized view")
        except psycopg2.Error as e:
            logger.warning(f"Could not refresh shared_keywords_300h: {e}")

        # Update article_core_keywords with canonical tokens
        try:
            logger.info("Rebuilding article_core_keywords with canonical tokens...")

            # Clear existing
            cur.execute("DELETE FROM article_core_keywords")

            # Rebuild with canonical tokens - GPT-5 optimization: df >= 2, top 8 per article
            rebuild_sql = """
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

            cur.execute(rebuild_sql)
            core_keywords_count = cur.rowcount

            logger.info(
                f"Rebuilt article_core_keywords with {core_keywords_count} canonical mappings"
            )

        except psycopg2.Error as e:
            logger.error(f"Failed to rebuild article_core_keywords: {e}")
            raise

    finally:
        cur.close()


def generate_update_report(stats, mappings_count):
    """Generate summary report of canonicalization update."""

    report = f"""
=== NIGHTLY KEYWORD CANONICALIZATION REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Processing Summary:
- Total keywords processed: {stats['total_processed']:,}
- Canonical mappings created: {stats['kept_canonical']:,}
- Keywords filtered out: {stats['filtered_out']:,}

Transformation Types:
- Titles/honorifics stripped: {stats['title_stripped']:,}
- Acronyms expanded: {stats['acronym_expanded']:,}
- Demonyms converted: {stats['demonym_converted']:,}

Database Updates:
- keyword_canon_map entries: {mappings_count:,}
- article_core_keywords: Rebuilt with canonical tokens

Status: COMPLETED
Next: Run CLUST-1 clustering with enhanced vocabulary
"""

    print(report)
    logger.info("Canonicalization update completed successfully")


def main():
    """Main canonicalization update job."""
    logger.info("Starting nightly keyword canonicalization update...")

    try:
        conn = get_db_connection()

        try:
            # Step 1: Get recent keywords from database
            keywords = get_recent_keywords(conn, hours_back=300)

            if not keywords:
                logger.info("No recent keywords found, exiting")
                return

            # Step 2: Apply enhanced canonicalization
            mappings, stats = canonicalize_keywords_batch(keywords)

            # Step 3: Update database mappings
            update_canonical_mappings(conn, mappings)

            # Step 4: Refresh dependent views
            refresh_materialized_views(conn)

            # Commit all changes
            conn.commit()

            # Step 5: Generate report
            generate_update_report(stats, len(mappings))

        except Exception as e:
            conn.rollback()
            logger.error(f"Canonicalization update failed: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to run canonicalization update: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
