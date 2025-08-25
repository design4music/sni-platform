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

# Top keywords by strategic score
cur.execute(
    """
    SELECT keyword, keyword_type, entity_label, strategic_score, lifecycle_stage 
    FROM keywords 
    ORDER BY strategic_score DESC 
    LIMIT 10
"""
)

print("Top 10 keywords by strategic score:")
for row in cur.fetchall():
    keyword, ktype, entity_label, score, stage = row
    print(f"  {keyword} ({ktype}, {entity_label}, score: {score:.3f}, stage: {stage})")

print()

# Sample by keyword type
cur.execute(
    """
    SELECT keyword_type, COUNT(*) 
    FROM keywords 
    GROUP BY keyword_type 
    ORDER BY COUNT(*) DESC
"""
)

print("Keywords by type:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
