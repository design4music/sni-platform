"""
Phase 1: RSS Feed Ingestion for SNI v3

Fetches RSS feeds from Google News and inserts into titles_v3 table.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from pipeline.phase_1.rss_fetcher import RSSFetcher


def get_active_feeds(country_code=None):
    """Get all active feeds for ingestion, optionally filtered by country."""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            if country_code:
                cur.execute(
                    """
                    SELECT id, url, name, source_domain, language_code
                    FROM feeds
                    WHERE is_active = true AND country_code = %s
                    ORDER BY priority DESC, name
                    """,
                    (country_code.upper(),),
                )
            else:
                cur.execute(
                    """
                    SELECT id, url, name, source_domain, language_code
                    FROM feeds
                    WHERE is_active = true
                    ORDER BY priority DESC, name
                    """
                )
            feeds = cur.fetchall()

            return [
                {
                    "id": row[0],
                    "url": row[1],
                    "name": row[2],
                    "source_domain": row[3],
                    "language_code": row[4],
                }
                for row in feeds
            ]
    finally:
        conn.close()


def run_ingestion(max_feeds=None, country_code=None):
    """
    Run RSS ingestion for all active feeds.

    Args:
        max_feeds: Maximum number of feeds to process (optional)
        country_code: Filter feeds by country code (optional, e.g., 'RU', 'US')
    """
    start_time = datetime.now()

    # Overall statistics
    stats = {
        "feeds_processed": 0,
        "feeds_success": 0,
        "feeds_errors": 0,
        "total_fetched": 0,
        "total_inserted": 0,
        "total_skipped": 0,
        "total_errors": 0,
    }

    print("=" * 70)
    print("SNI v3 - Phase 1: RSS Feed Ingestion")
    print("=" * 70)
    print("Start time: {}".format(start_time.strftime("%Y-%m-%d %H:%M:%S")))
    if country_code:
        print("Country filter: {}".format(country_code.upper()))
    print()

    # Get active feeds
    feeds = get_active_feeds(country_code=country_code)
    print("Found {} active feeds".format(len(feeds)))

    if max_feeds:
        feeds = feeds[:max_feeds]
        print(
            "Processing first {} feeds (--max-feeds={})\n".format(len(feeds), max_feeds)
        )

    # Initialize fetcher
    fetcher = RSSFetcher()

    # Process each feed
    for feed in feeds:
        feed_start = datetime.now()
        print(f"\n[{stats['feeds_processed'] + 1}/{len(feeds)}] {feed['name']}")
        print(f"  URL: {feed['url']}")

        try:
            # Fetch and insert
            articles, feed_stats = fetcher.fetch_feed(feed["id"], feed["url"])

            # Update overall stats
            stats["feeds_processed"] += 1
            stats["feeds_success"] += 1
            stats["total_fetched"] += feed_stats["fetched"]
            stats["total_inserted"] += feed_stats["inserted"]
            stats["total_skipped"] += feed_stats["skipped"]
            stats["total_errors"] += feed_stats["errors"]

            # Per-feed summary
            duration = (datetime.now() - feed_start).total_seconds()
            print(
                f"  Result: {feed_stats['inserted']} inserted, {feed_stats['skipped']} skipped, {feed_stats['errors']} errors ({duration:.1f}s)"
            )

        except Exception as e:
            stats["feeds_processed"] += 1
            stats["feeds_errors"] += 1
            print(f"  ERROR: {e}")

    # Final summary
    total_duration = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*70}")
    print("INGESTION COMPLETE")
    print(f"{'='*70}")
    print(f"Feeds processed:     {stats['feeds_processed']}")
    print(f"Feeds successful:    {stats['feeds_success']}")
    print(f"Feeds with errors:   {stats['feeds_errors']}")
    print(f"\nTitles fetched:      {stats['total_fetched']}")
    print(f"Titles inserted:     {stats['total_inserted']}")
    print(f"Titles skipped:      {stats['total_skipped']}")
    print(f"Entry errors:        {stats['total_errors']}")
    print(f"\nTotal duration:      {total_duration:.1f}s")
    print(f"Avg per feed:        {total_duration / stats['feeds_processed']:.1f}s")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 1: RSS feed ingestion for SNI v3"
    )
    parser.add_argument(
        "--max-feeds", type=int, help="Maximum number of feeds to process"
    )
    parser.add_argument(
        "--country", type=str, help="Filter feeds by country code (e.g., RU, US, CN)"
    )

    args = parser.parse_args()

    run_ingestion(max_feeds=args.max_feeds, country_code=args.country)
