#!/usr/bin/env python3
"""
CLUST-1: Full Corpus Keyword Extraction
Process all remaining articles with timing and progress tracking
"""

import asyncio
import os
import sys
import time
from datetime import datetime

# Fix Windows Unicode encoding
if sys.platform.startswith("win"):
    import io

    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add project root to path
sys.path.append(".")

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.extraction.keyword_lifecycle_manager import \
    KeywordLifecycleManager


async def process_remaining_corpus():
    """Process all remaining articles with detailed timing"""

    print("CLUST-1: PROCESSING REMAINING CORPUS")
    print("=" * 50)

    # Initialize database
    config = get_config()
    initialize_database(config.database)

    # Get current progress
    with get_db_session() as session:
        result = session.execute(
            text("SELECT COUNT(DISTINCT article_id) FROM article_keywords")
        )
        processed_count = result.fetchone()[0]

        result = session.execute(
            text(
                "SELECT COUNT(*) FROM articles WHERE content IS NOT NULL AND LENGTH(content) > 100"
            )
        )
        total_count = result.fetchone()[0]

    print(
        f"Starting from: {processed_count}/{total_count} articles ({processed_count/total_count*100:.1f}%)"
    )

    # Get unprocessed articles in batches
    batch_size = 50
    total_processed = 0
    total_keywords_created = 0
    total_relationships = 0

    manager = KeywordLifecycleManager()
    overall_start = time.time()

    # Process in chunks to avoid memory issues
    offset = 0
    while True:
        # Get next batch of unprocessed articles
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT a.id, a.title, a.content, a.summary, a.published_at, a.source_name
                FROM articles a
                LEFT JOIN article_keywords ak ON a.id = ak.article_id
                WHERE a.content IS NOT NULL 
                  AND LENGTH(a.content) > 100
                  AND ak.article_id IS NULL  -- Not yet processed
                ORDER BY a.published_at DESC
                LIMIT :batch_size OFFSET :offset
            """
                ),
                {"batch_size": batch_size, "offset": offset},
            )

            articles = []
            for row in result.fetchall():
                articles.append(
                    {
                        "id": str(row.id),
                        "title": row.title or "",
                        "content": row.content or "",
                        "summary": row.summary or "",
                        "published_at": row.published_at or datetime.utcnow(),
                        "source_name": row.source_name or "Unknown",
                    }
                )

        if not articles:
            print("No more articles to process!")
            break

        # Process batch
        batch_start = time.time()
        batch_num = offset // batch_size + 1

        print(f"\nBatch {batch_num}: Processing {len(articles)} articles...")

        try:
            result = await manager.process_new_articles(articles)

            articles_done = result.get("articles_processed", 0)
            keywords_extracted = result.get("keywords_extracted", 0)
            new_keywords = result.get("new_keywords_created", 0)

            total_processed += articles_done
            total_keywords_created += new_keywords
            total_relationships += keywords_extracted

            batch_time = time.time() - batch_start
            overall_time = time.time() - overall_start

            # Progress stats
            current_total = processed_count + total_processed
            progress_pct = current_total / total_count * 100
            rate = total_processed / overall_time if overall_time > 0 else 0

            print(f"  SUCCESS: {articles_done} articles in {batch_time:.1f}s")
            print(f"  Keywords: {keywords_extracted} relationships, {new_keywords} new")
            print(f"  Progress: {current_total}/{total_count} ({progress_pct:.1f}%)")
            print(f"  Rate: {rate:.1f} articles/sec")

        except Exception as e:
            print(f"  ERROR: Batch {batch_num} failed: {e}")

        offset += batch_size

        # Stop after processing reasonable number for this session
        if total_processed >= 500:  # Process 500 more articles
            print(
                f"\nSession limit reached. Processed {total_processed} additional articles."
            )
            break

    total_time = time.time() - overall_start

    print(f"\n" + "=" * 50)
    print(f"SESSION COMPLETE")
    print(f"=" * 50)
    print(f"Articles processed this session: {total_processed}")
    print(f"Keywords discovered: {total_keywords_created}")
    print(f"Keyword relationships: {total_relationships}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average rate: {total_processed/total_time:.1f} articles/second")

    # Final progress
    with get_db_session() as session:
        result = session.execute(
            text("SELECT COUNT(DISTINCT article_id) FROM article_keywords")
        )
        final_processed = result.fetchone()[0]

        result = session.execute(text("SELECT COUNT(*) FROM keywords"))
        final_keywords = result.fetchone()[0]

    print(f"\nTOTAL CORPUS PROGRESS:")
    print(
        f"Articles with keywords: {final_processed}/{total_count} ({final_processed/total_count*100:.1f}%)"
    )
    print(f"Total unique keywords: {final_keywords}")


if __name__ == "__main__":
    asyncio.run(process_remaining_corpus())
