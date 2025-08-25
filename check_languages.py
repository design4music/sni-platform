#!/usr/bin/env python3
import os

import psycopg2

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    database=os.getenv("DB_NAME", "narrative_intelligence"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
)

cur = conn.cursor()

# Check language distribution
cur.execute(
    """
    SELECT 
        language, 
        COUNT(*) as article_count,
        COUNT(DISTINCT ak.keyword_id) as keyword_count
    FROM articles a
    LEFT JOIN article_keywords ak ON a.id = ak.article_id
    GROUP BY language 
    ORDER BY article_count DESC
"""
)

print("Language distribution in articles:")
print("Language | Articles | Unique Keywords")
print("-" * 40)
total_articles = 0
total_keywords = 0

for row in cur.fetchall():
    lang, article_count, keyword_count = row
    lang_display = lang if lang else "NULL"
    print(f"{lang_display:8} | {article_count:8} | {keyword_count:8}")
    total_articles += article_count
    if keyword_count:
        total_keywords += keyword_count

print("-" * 40)
print(f"{'Total':8} | {total_articles:8} | {total_keywords:8}")

print()
print("Note: Articles with keywords were processed with English-only filter")

conn.close()
