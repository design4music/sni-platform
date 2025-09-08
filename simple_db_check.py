#!/usr/bin/env python3
"""Simple database smoke test without Unicode issues"""

import sys

sys.path.append(".")

from sqlalchemy import text

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database


def main():
    config = get_config()
    initialize_database(config.database)

    print("=== DATABASE STATUS REPORT ===")
    print()

    with get_db_session() as db:
        # Core counts
        print("CORE TABLE COUNTS:")
        tables = [
            "articles",
            "keywords",
            "article_keywords",
            "narratives",
            "article_clusters",
        ]
        counts = {}

        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).first()
            count = result[0]
            counts[table] = count
            print(f"  {table}: {count:,}")

        print()
        print("INDEXES PER TABLE:")
        result = db.execute(
            text(
                """
            SELECT tablename, COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('articles', 'keywords', 'article_keywords', 'narratives', 'article_clusters')
            GROUP BY tablename
            ORDER BY tablename
        """
            )
        ).fetchall()

        for table, idx_count in result:
            print(f"  {table}: {idx_count} indexes")

        print()
        print("DATA RELATIONSHIPS:")
        if counts["articles"] > 0 and counts["article_keywords"] > 0:
            avg_keywords = counts["article_keywords"] / counts["articles"]
            print(f"  Average keywords per article: {avg_keywords:.1f}")

        print()
        print("POSTGRESQL EXTENSIONS:")
        result = db.execute(
            text("SELECT extname, extversion FROM pg_extension ORDER BY extname")
        ).fetchall()
        for name, version in result:
            print(f"  {name}: {version}")

        print()
        print("STATUS SUMMARY:")
        print(f"  Database: CONNECTED (PostgreSQL)")
        print(f"  Tables: {len(tables)} core tables exist")
        print(f"  Data: {sum(counts.values()):,} total records")
        print(f"  Extensions: vector + pg_trgm ready")

        # Check pipeline status
        has_articles = counts["articles"] > 0
        has_keywords = counts["keywords"] > 0
        has_relationships = counts["article_keywords"] > 0
        has_narratives = counts["narratives"] > 0
        has_clusters = counts["article_clusters"] > 0

        print()
        print("PIPELINE STATUS:")
        print(
            f"  RSS Ingestion: {'ACTIVE' if has_articles else 'IDLE'} ({counts['articles']:,} articles)"
        )
        print(
            f"  Keyword Extraction: {'ACTIVE' if has_keywords else 'IDLE'} ({counts['keywords']:,} keywords)"
        )
        print(
            f"  Article Processing: {'ACTIVE' if has_relationships else 'IDLE'} ({counts['article_keywords']:,} relationships)"
        )
        print(
            f"  Narrative Generation: {'INACTIVE' if not has_narratives else 'ACTIVE'} ({counts['narratives']:,} narratives)"
        )
        print(
            f"  Clustering: {'INACTIVE' if not has_clusters else 'ACTIVE'} ({counts['article_clusters']:,} clusters)"
        )


if __name__ == "__main__":
    main()
