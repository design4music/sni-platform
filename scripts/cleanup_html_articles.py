#!/usr/bin/env python3
"""
HTML Cleanup Script
Strategic Narrative Intelligence ETL Pipeline

Cleans HTML from existing articles in the database.
Run this once to fix existing articles, then new ingestion will be clean.
"""

# Add project root to path
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def clean_html_text(text: str) -> str:
    """Clean HTML tags and normalize text"""
    if not text:
        return ""

    try:
        # Parse HTML and extract text
        soup = BeautifulSoup(text, "html.parser")
        cleaned_text = soup.get_text(separator=" ", strip=True)

        # Normalize whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)

        return cleaned_text.strip()
    except Exception:
        # Fallback: basic HTML tag removal
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"&[a-zA-Z0-9#]+;", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()


def cleanup_html_articles(window_hours: int = 168) -> dict:
    """Clean HTML from articles and recalculate word counts"""

    print(f"Starting HTML cleanup for articles from last {window_hours} hours...")

    config = get_config()
    initialize_database(config.database)

    stats = {"articles_found": 0, "articles_cleaned": 0, "errors": 0}

    with get_db_session() as session:
        # Find articles with HTML content
        result = session.execute(
            text(
                f"""
            SELECT id, title, content, summary
            FROM articles 
            WHERE created_at >= NOW() - INTERVAL '{window_hours} hours'
            AND (title LIKE '%<%' OR content LIKE '%<%' OR summary LIKE '%<%')
            ORDER BY created_at DESC
        """
            )
        )

        articles_with_html = result.fetchall()
        stats["articles_found"] = len(articles_with_html)

        if not articles_with_html:
            print("No articles with HTML found.")
            return stats

        print(f"Found {len(articles_with_html)} articles with HTML content")

        # Process each article
        for article_id, title, content, summary in articles_with_html:
            try:
                # Clean HTML from all text fields
                clean_title = clean_html_text(title) if title else title
                clean_content = clean_html_text(content) if content else content
                clean_summary = clean_html_text(summary) if summary else summary

                # Recalculate word count based on cleaned content
                if clean_content:
                    word_count = len(clean_content.split())
                else:
                    word_count = 0

                # Update the article
                session.execute(
                    text(
                        """
                    UPDATE articles 
                    SET title = :title,
                        content = :content,
                        summary = :summary,
                        word_count = :word_count
                    WHERE id = :article_id
                """
                    ),
                    {
                        "title": clean_title,
                        "content": clean_content,
                        "summary": clean_summary,
                        "word_count": word_count,
                        "article_id": article_id,
                    },
                )

                stats["articles_cleaned"] += 1

                if stats["articles_cleaned"] % 10 == 0:
                    print(
                        f"Cleaned {stats['articles_cleaned']}/{stats['articles_found']} articles..."
                    )

            except Exception as e:
                print(f"Error cleaning article {article_id}: {e}")
                stats["errors"] += 1

        # Commit all changes
        session.commit()

    print("\nHTML cleanup completed!")
    print(f"Articles found with HTML: {stats['articles_found']}")
    print(f"Articles cleaned: {stats['articles_cleaned']}")
    print(f"Errors: {stats['errors']}")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean HTML from existing articles")
    parser.add_argument(
        "--window",
        type=int,
        default=168,  # 7 days
        help="Time window in hours to process (default: 168 = 7 days)",
    )

    args = parser.parse_args()

    cleanup_html_articles(args.window)
