#!/usr/bin/env python3
"""
Load Strategic News Feeds from CSV
Imports feeds from data/strategic_news_feeds.csv into the feeds table
"""

import csv
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import create_engine, text

from core.config import get_config


def load_feeds_from_csv():
    """Load feeds from CSV file into database"""
    config = get_config()
    engine = create_engine(config.database_url)

    feeds_csv_path = project_root / "data" / "strategic_news_feeds.csv"

    if not feeds_csv_path.exists():
        logger.error(f"Feed CSV file not found: {feeds_csv_path}")
        return False

    logger.info(f"Loading feeds from {feeds_csv_path}")

    feeds_to_insert = []

    with open(feeds_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Clean up the URL - some have inconsistent formatting
            url = row["url"].strip()

            # Skip if URL is malformed
            if not url.startswith("http"):
                logger.warning(f"Skipping malformed URL: {url}")
                continue

            feed_data = {
                "id": str(uuid4()),
                "url": url,
                "name": row["name"].strip(),
                "source_domain": row["source_domain"].strip(),
                "language_code": row["language_code"].strip(),
                "country_code": (
                    row["country_code"].strip()[:3]
                    if row["country_code"].strip()
                    else None
                ),  # Truncate to 3 chars
                "fetch_interval_minutes": 60,  # Default 1 hour interval
                "is_active": True,
                "priority": 1,  # Default priority
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            feeds_to_insert.append(feed_data)

    logger.info(f"Prepared {len(feeds_to_insert)} feeds for insertion")

    # Insert feeds into database
    with engine.connect() as conn:
        # First, check if feeds table exists and get its structure
        try:
            result = conn.execute(
                text(
                    """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'feeds'
                ORDER BY ordinal_position
            """
                )
            )

            existing_columns = [row.column_name for row in result.fetchall()]
            logger.info(f"Feeds table columns: {existing_columns}")

        except Exception as e:
            logger.error(f"Could not check feeds table structure: {e}")
            return False

        # Check for existing feeds to avoid duplicates
        existing_urls = set()
        try:
            result = conn.execute(text("SELECT url FROM feeds"))
            existing_urls = {row.url for row in result.fetchall()}
            logger.info(f"Found {len(existing_urls)} existing feeds in database")
        except Exception as e:
            logger.warning(f"Could not check existing feeds: {e}")

        # Insert new feeds with individual transaction handling
        inserted_count = 0
        skipped_count = 0
        failed_count = 0

        for feed in feeds_to_insert:
            if feed["url"] in existing_urls:
                logger.debug(f"Skipping duplicate feed: {feed['name']}")
                skipped_count += 1
                continue

            # Use individual transaction for each feed to avoid rollback of all
            try:
                # Build insert query based on available columns
                insert_sql = """
                INSERT INTO feeds (id, url, name, source_domain, language_code, 
                                 country_code, fetch_interval_minutes, 
                                 is_active, priority, created_at, updated_at)
                VALUES (:id, :url, :name, :source_domain, :language_code,
                        :country_code, :fetch_interval_minutes,
                        :is_active, :priority, :created_at, :updated_at)
                """

                # Create a separate transaction for this feed
                with engine.begin() as trans:
                    trans.execute(text(insert_sql), feed)

                inserted_count += 1
                logger.debug(f"Inserted feed: {feed['name']}")

            except Exception as e:
                logger.error(f"Failed to insert feed {feed['name']}: {e}")
                failed_count += 1
                continue

        logger.info("Feed loading complete:")
        logger.info(f"  - Inserted: {inserted_count}")
        logger.info(f"  - Skipped (duplicates): {skipped_count}")
        logger.info(f"  - Failed: {failed_count}")
        logger.info(
            f"  - Total feeds in database: {inserted_count + len(existing_urls)}"
        )

        return inserted_count > 0


def main():
    """Main entry point"""
    logger.info("Starting strategic feeds loading...")

    try:
        success = load_feeds_from_csv()

        if success:
            logger.success("Strategic feeds loaded successfully!")
            return True
        else:
            logger.error("Feed loading failed")
            return False

    except Exception as e:
        logger.error(f"Feed loading failed with error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
