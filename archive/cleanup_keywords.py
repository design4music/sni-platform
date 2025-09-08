#!/usr/bin/env python3
"""
CLUST-1: Keyword Cleanup
Remove noise keywords and keep only meaningful ones for clustering
"""

import os
import sys
import time

# Fix Windows Unicode encoding
if sys.platform.startswith("win"):
    import io

    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add project root to path
sys.path.append(".")

import psycopg2
from etl_pipeline.core.config import get_config


def cleanup_keywords():
    """Clean up keyword database by removing noise"""

    print("CLUST-1: KEYWORD CLEANUP")
    print("=" * 50)

    config = get_config()
    conn = psycopg2.connect(
        host=config.database.host,
        database=config.database.database,
        user=config.database.username,
        password=config.database.password,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Get initial stats
    cur.execute("SELECT COUNT(*) FROM keywords")
    initial_keywords = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM article_keywords")
    initial_relationships = cur.fetchone()[0]

    print(f"BEFORE cleanup:")
    print(f"  Keywords: {initial_keywords:,}")
    print(f"  Relationships: {initial_relationships:,}")

    # CLEANUP RULES
    print(f"\nApplying cleanup rules...")

    # Rule 1: Remove keywords that appear only once (94.7% of noise)
    print("1. Removing unique keywords (frequency = 1)...")
    cur.execute(
        """
        DELETE FROM keywords 
        WHERE base_frequency = 1
    """
    )
    removed_unique = cur.rowcount
    print(f"   Removed {removed_unique:,} unique keywords")

    # Rule 2: Remove very long phrases (likely over-extraction errors)
    print("2. Removing overly long phrases (>40 characters)...")
    cur.execute(
        """
        DELETE FROM keywords 
        WHERE LENGTH(keyword) > 40 AND keyword_type IN ('phrase', 'keyphrase')
    """
    )
    removed_long = cur.rowcount
    print(f"   Removed {removed_long:,} overly long phrases")

    # Rule 3: Remove very short non-entity keywords (2 chars or less, except entities like US, UK)
    print("3. Removing very short non-entity noise...")
    cur.execute(
        """
        DELETE FROM keywords 
        WHERE LENGTH(keyword) <= 2 
          AND keyword_type != 'entity'
          AND keyword NOT IN ('AI', 'US', 'UK', 'EU', 'UN', 'NY', 'LA', 'DC')
    """
    )
    removed_short = cur.rowcount
    print(f"   Removed {removed_short:,} very short noise keywords")

    # Rule 4: Remove common stop-word phrases that slipped through
    print("4. Removing stop-word phrases...")
    stop_patterns = [
        "first time",
        "last time",
        "same time",
        "long time",
        "next time",
        "new york",
        "los angeles",
        "san francisco",  # Keep as entities only
        "per cent",
        "percent",
        "according",
        "according to",
        "said that",
        "reports that",
        "years old",
        "year old",
        "weeks ago",
        "days ago",
        "thousand",
        "million",
        "billion",  # Keep as MONEY entities only
    ]

    for pattern in stop_patterns:
        cur.execute(
            "DELETE FROM keywords WHERE LOWER(keyword) = %s AND keyword_type != 'entity'",
            (pattern,),
        )

    removed_stopwords = sum(cur.rowcount for _ in stop_patterns)  # Approximate
    print(f"   Removed ~{removed_stopwords} stop-word phrases")

    # Rule 5: Keep only keywords with reasonable frequency for clustering (freq >= 2)
    print("5. Final frequency filter (keeping freq >= 2)...")
    cur.execute("SELECT COUNT(*) FROM keywords WHERE base_frequency >= 2")
    strategic_keywords = cur.fetchone()[0]

    # Get final stats
    cur.execute("SELECT COUNT(*) FROM keywords")
    final_keywords = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM article_keywords")
    final_relationships = cur.fetchone()[0]

    print(f"\nAFTER cleanup:")
    print(f"  Keywords: {final_keywords:,} (was {initial_keywords:,})")
    print(f"  Relationships: {final_relationships:,} (was {initial_relationships:,})")
    print(
        f"  Reduction: {(1 - final_keywords/initial_keywords)*100:.1f}% fewer keywords"
    )
    print(f"  Strategic keywords (freq >= 2): {strategic_keywords:,}")

    # Show top keywords after cleanup
    print(f"\nTop Strategic Keywords After Cleanup:")
    cur.execute(
        """
        SELECT keyword, keyword_type, entity_label, base_frequency 
        FROM keywords 
        ORDER BY base_frequency DESC 
        LIMIT 20
    """
    )

    for i, (keyword, ktype, label, freq) in enumerate(cur.fetchall(), 1):
        entity_info = f" ({label})" if label else ""
        print(f'  {i:2}. "{keyword}"{entity_info} - {ktype}, freq: {freq}')

    # Keyword type distribution after cleanup
    print(f"\nKeyword Types After Cleanup:")
    cur.execute(
        "SELECT keyword_type, COUNT(*) FROM keywords GROUP BY keyword_type ORDER BY COUNT(*) DESC"
    )
    for ktype, count in cur.fetchall():
        print(f"  {ktype}: {count:,} keywords")

    # Frequency distribution after cleanup
    print(f"\nFrequency Distribution After Cleanup:")
    cur.execute(
        "SELECT base_frequency, COUNT(*) FROM keywords GROUP BY base_frequency ORDER BY base_frequency"
    )
    freq_data = cur.fetchall()

    rare_count = sum(count for freq, count in freq_data if 2 <= freq <= 5)
    common_count = sum(count for freq, count in freq_data if 6 <= freq <= 20)
    strategic_count = sum(count for freq, count in freq_data if freq > 20)

    print(f"  Rare (2-5 times): {rare_count:,} keywords")
    print(f"  Common (6-20 times): {common_count:,} keywords")
    print(f"  Strategic (20+ times): {strategic_count:,} keywords")

    print(f"\n[OK] KEYWORD CLEANUP COMPLETE!")
    print(f"Ready for high-quality keyword-based clustering!")

    cur.close()
    conn.close()


if __name__ == "__main__":
    cleanup_keywords()
