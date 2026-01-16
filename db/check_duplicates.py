"""Quick check for duplicate titles"""
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

conn = psycopg2.connect(
    host=config.db_host,
    port=config.db_port,
    database=config.db_name,
    user=config.db_user,
    password=config.db_password,
)

with conn.cursor() as cur:
    # Total count
    cur.execute("SELECT COUNT(*) FROM titles_v3")
    total = cur.fetchone()[0]

    # Unique titles (ignoring publisher/date)
    cur.execute("SELECT COUNT(DISTINCT title_display) FROM titles_v3")
    unique_titles = cur.fetchone()[0]

    # Exact duplicates (same title + publisher + date)
    cur.execute("""
        SELECT
            title_display,
            publisher_name,
            pubdate_utc::date as pub_date,
            COUNT(*) as cnt
        FROM titles_v3
        GROUP BY title_display, publisher_name, pubdate_utc::date
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 10
    """)
    exact_dupes = cur.fetchall()

    # Growth in last 24h
    cur.execute("""
        SELECT COUNT(*)
        FROM titles_v3
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)
    last_24h = cur.fetchone()[0]

    # By date
    cur.execute("""
        SELECT
            pubdate_utc::date,
            COUNT(*) as cnt
        FROM titles_v3
        WHERE pubdate_utc >= NOW() - INTERVAL '7 days'
        GROUP BY pubdate_utc::date
        ORDER BY pubdate_utc::date DESC
    """)
    by_date = cur.fetchall()

print("=" * 60)
print("DEDUPLICATION ANALYSIS")
print("=" * 60)
print(f"Total titles:           {total:,}")
print(f"Unique titles:          {unique_titles:,}")
print(f"Reused titles:          {total - unique_titles:,} (different publisher/date)")
print(f"Inserted last 24h:      {last_24h:,}")
print()

if exact_dupes:
    print("EXACT DUPLICATES (same title + publisher + date):")
    print("-" * 60)
    for title, pub, date, cnt in exact_dupes:
        print(f"  {cnt}x | {pub} | {date} | {title[:60]}")
    print()
else:
    print("No exact duplicates found - deduplication working correctly")
    print()

print("TITLES BY DATE (last 7 days):")
print("-" * 60)
for date, cnt in by_date:
    print(f"  {date}: {cnt:,} titles")

conn.close()
