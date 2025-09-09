#!/usr/bin/env python3
"""
CLUST-2 Sliding Window Processor
Processes corpus in 72h chunks moving backwards in time

FUTURE ENHANCEMENT: Not yet implemented
This script would process historical content in tight 72h windows
to avoid "Trump everything" mega-buckets while still reaching old content.

Usage (when implemented):
    python sliding_processor.py --days-back 30 --dry-run
    python sliding_processor.py --days-back 7 --force
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.clust2.bucket_db import BucketDB, get_strategic_titles_for_bucketing
from apps.clust2.bucket_manager import BucketManager
from core.config import get_config
from core.database import get_db_session


@dataclass
class ProcessingWindow:
    """Represents a 72h processing window"""

    start_time: datetime
    end_time: datetime

    @property
    def window_id(self) -> str:
        """Unique identifier for this window"""
        return f"W-{self.start_time.strftime('%Y-%m-%d-%H')}"

    @property
    def hours_span(self) -> float:
        return (self.end_time - self.start_time).total_seconds() / 3600.0


class SlidingWindowProcessor:
    """Processes titles in sliding 72h windows moving backwards"""

    def __init__(self):
        self.config = get_config()
        self.bucket_manager = BucketManager()
        self.bucket_db = BucketDB()
        self.window_size_hours = self.config.processing_window_hours  # Default 72h

    def get_processing_windows(
        self, start_time: datetime, total_hours_back: int
    ) -> List[ProcessingWindow]:
        """
        Generate list of 72h windows moving backwards from start_time.

        Args:
            start_time: Starting point (usually NOW)
            total_hours_back: Total historical period to cover

        Returns:
            List of ProcessingWindow objects, ordered newest to oldest
        """
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        windows = []
        current_end = start_time

        while (start_time - current_end).total_seconds() / 3600.0 < total_hours_back:
            window_start = current_end - timedelta(hours=self.window_size_hours)

            # Don't go beyond the total lookback period
            earliest_allowed = start_time - timedelta(hours=total_hours_back)
            if window_start < earliest_allowed:
                window_start = earliest_allowed

            window = ProcessingWindow(start_time=window_start, end_time=current_end)
            windows.append(window)

            # Move to next window
            current_end = window_start

            # Stop if we've covered the full period
            if window_start <= earliest_allowed:
                break

        return windows

    def get_titles_in_window(self, window: ProcessingWindow) -> List[Dict[str, Any]]:
        """
        Get strategic titles within a specific time window.

        Args:
            window: ProcessingWindow to query

        Returns:
            List of title dictionaries
        """
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT 
                    id, title_norm, title_display, pubdate_utc,
                    gate_actor_hit, gate_keep, processing_status
                FROM titles 
                WHERE gate_keep = true 
                  AND pubdate_utc >= :start_time
                  AND pubdate_utc < :end_time
                  AND pubdate_utc IS NOT NULL
                ORDER BY pubdate_utc DESC
            """
                ),
                {"start_time": window.start_time, "end_time": window.end_time},
            )

            titles = []
            for row in result:
                title_dict = dict(row._mapping)
                title_dict["id"] = str(title_dict["id"])
                titles.append(title_dict)

            return titles

    def window_already_processed(self, window: ProcessingWindow) -> bool:
        """
        Check if a window has already been processed by looking for buckets
        that overlap with this time period.

        Args:
            window: ProcessingWindow to check

        Returns:
            True if window appears to have been processed
        """
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT COUNT(*) as bucket_count
                FROM buckets 
                WHERE (date_window_start <= :end_time AND date_window_end >= :start_time)
            """
                ),
                {"start_time": window.start_time, "end_time": window.end_time},
            )

            count = result.scalar()
            return count > 0

    def process_window(
        self, window: ProcessingWindow, dry_run: bool = False, force: bool = False
    ) -> Dict[str, Any]:
        """
        Process a single 72h window.

        Args:
            window: ProcessingWindow to process
            dry_run: If True, don't insert buckets
            force: If True, process even if already processed

        Returns:
            Results dictionary
        """
        print(
            f"Processing {window.window_id}: {window.start_time.strftime('%Y-%m-%d %H:%M')} to {window.end_time.strftime('%Y-%m-%d %H:%M')}"
        )

        # Check if already processed
        if not force and self.window_already_processed(window):
            print(f"  Window {window.window_id} already processed - skipping")
            return {
                "window_id": window.window_id,
                "titles_found": 0,
                "buckets_created": 0,
                "buckets_inserted": 0,
                "skipped": True,
            }

        # Get titles in this window
        titles = self.get_titles_in_window(window)
        print(f"  Found {len(titles)} strategic titles")

        if not titles:
            return {
                "window_id": window.window_id,
                "titles_found": 0,
                "buckets_created": 0,
                "buckets_inserted": 0,
                "skipped": False,
            }

        # Create buckets for this window
        bucket_candidates = self.bucket_manager.create_buckets_from_titles(titles)
        print(f"  Created {len(bucket_candidates)} bucket candidates")

        # Insert buckets (unless dry run)
        buckets_inserted = 0
        if not dry_run and bucket_candidates:
            inserted_uuids = self.bucket_db.insert_buckets_batch(bucket_candidates)
            buckets_inserted = len(inserted_uuids)
            print(f"  Inserted {buckets_inserted} buckets")
        elif dry_run:
            print(f"  DRY RUN - would insert {len(bucket_candidates)} buckets")

        return {
            "window_id": window.window_id,
            "titles_found": len(titles),
            "buckets_created": len(bucket_candidates),
            "buckets_inserted": buckets_inserted,
            "skipped": False,
        }


def main():
    """CLI entry point for sliding window processing"""
    print("CLUST-2 Sliding Window Processor")
    print("This is a FUTURE ENHANCEMENT - not yet ready for production use")
    print("Current implementation: Use regular run_clust2.py with 72h windows")
    return


if __name__ == "__main__":
    main()
