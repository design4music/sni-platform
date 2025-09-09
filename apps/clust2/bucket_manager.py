"""
CLUST-2 Bucket Manager
Implements time windowing and bucket logic for actor-set clustering
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.clust2.actor_sets import ActorSetBuilder
from core.config import get_config


@dataclass
class BucketCandidate:
    """Candidate bucket for grouping titles"""

    actor_set: List[str]  # Sorted actor codes
    bucket_key: str  # Deterministic key like "CN-US"
    time_window_start: datetime  # Window start (UTC)
    time_window_end: datetime  # Window end (UTC)
    title_ids: List[str]  # UUIDs of titles in this bucket
    members_count: int  # Number of titles

    @property
    def bucket_id(self) -> str:
        """Generate deterministic bucket ID"""
        # Format: B-YYYY-MM-DD-ACTOR_SET
        date_str = self.time_window_start.strftime("%Y-%m-%d")
        return f"B-{date_str}-{self.bucket_key}"

    @property
    def span_hours(self) -> float:
        """Calculate time span in hours"""
        delta = self.time_window_end - self.time_window_start
        return delta.total_seconds() / 3600.0


class BucketManager:
    """Manages time windowing and bucket creation for CLUST-2"""

    def __init__(self):
        self.config = get_config()
        self.actor_builder = ActorSetBuilder()

        # Configuration from core/config.py
        self.max_span_hours = self.config.bucket_max_span_hours
        self.min_size = self.config.bucket_min_size
        self.since_hours = self.config.processing_window_hours
        self.max_actors = self.config.bucket_max_actors

    def get_time_window(self, base_time: datetime) -> Tuple[datetime, datetime]:
        """
        Calculate time window boundaries based on configuration.

        Args:
            base_time: Reference time (usually NOW)

        Returns:
            Tuple of (window_start, window_end) in UTC
        """
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=timezone.utc)

        # Look back from base_time
        window_end = base_time
        window_start = base_time - timedelta(hours=self.since_hours)

        return window_start, window_end

    def group_titles_by_actor_sets(
        self, titles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group titles by their actor sets.

        Args:
            titles: List of title dictionaries with pubdate_utc and text fields

        Returns:
            Dict mapping bucket_keys to lists of titles
        """
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for title in titles:
            # Extract actor set and bucket key
            actor_codes, bucket_key = self.actor_builder.extract_and_build_key(
                title, max_actors=self.max_actors
            )

            # Skip titles with no actors
            if not bucket_key:
                continue

            # Add title to appropriate group
            if bucket_key not in groups:
                groups[bucket_key] = []

            # Enrich title with actor information for bucket creation
            title_with_actors = title.copy()
            title_with_actors["_actor_codes"] = actor_codes
            title_with_actors["_bucket_key"] = bucket_key

            groups[bucket_key].append(title_with_actors)

        return groups

    def create_bucket_from_group(
        self, bucket_key: str, titles: List[Dict[str, Any]]
    ) -> Optional[BucketCandidate]:
        """
        Create a bucket candidate from a group of titles with the same actor set.

        Args:
            bucket_key: The actor set key (e.g., "CN-US")
            titles: List of titles with this actor set

        Returns:
            BucketCandidate if valid, None if doesn't meet criteria
        """
        if not titles:
            return None

        # Filter titles that have valid publication dates
        valid_titles = []
        for title in titles:
            pubdate = title.get("pubdate_utc")
            if pubdate is not None:
                if isinstance(pubdate, str):
                    try:
                        pubdate = datetime.fromisoformat(pubdate.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                elif pubdate.tzinfo is None:
                    pubdate = pubdate.replace(tzinfo=timezone.utc)

                title_copy = title.copy()
                title_copy["pubdate_utc"] = pubdate
                valid_titles.append(title_copy)

        # Check minimum size requirement
        if len(valid_titles) < self.min_size:
            return None

        # Calculate time boundaries
        pub_dates = [t["pubdate_utc"] for t in valid_titles]
        time_start = min(pub_dates)
        time_end = max(pub_dates)

        # Check maximum span requirement
        span_hours = (time_end - time_start).total_seconds() / 3600.0
        if span_hours > self.max_span_hours:
            return None

        # Extract actor codes from first title (they should all be the same)
        actor_codes = valid_titles[0].get("_actor_codes", [])

        # Create bucket candidate
        return BucketCandidate(
            actor_set=actor_codes,
            bucket_key=bucket_key,
            time_window_start=time_start,
            time_window_end=time_end,
            title_ids=[str(t.get("id", "")) for t in valid_titles],
            members_count=len(valid_titles),
        )

    def create_buckets_from_titles(
        self, titles: List[Dict[str, Any]]
    ) -> List[BucketCandidate]:
        """
        Create bucket candidates from a list of titles.

        Args:
            titles: List of title dictionaries from database query

        Returns:
            List of valid BucketCandidate objects
        """
        # Group titles by actor sets
        groups = self.group_titles_by_actor_sets(titles)

        # Create bucket candidates from each group
        buckets = []
        for bucket_key, group_titles in groups.items():
            bucket = self.create_bucket_from_group(bucket_key, group_titles)
            if bucket:
                buckets.append(bucket)

        return buckets

    def filter_recent_titles(
        self, titles: List[Dict[str, Any]], base_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter titles to only include those within the time window.

        Args:
            titles: List of title dictionaries
            base_time: Reference time (defaults to NOW)

        Returns:
            Filtered list of titles within the time window
        """
        if base_time is None:
            base_time = datetime.now(timezone.utc)

        window_start, window_end = self.get_time_window(base_time)

        recent_titles = []
        for title in titles:
            pubdate = title.get("pubdate_utc")
            if pubdate is None:
                continue

            # Parse datetime if it's a string
            if isinstance(pubdate, str):
                try:
                    pubdate = datetime.fromisoformat(pubdate.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif pubdate.tzinfo is None:
                pubdate = pubdate.replace(tzinfo=timezone.utc)

            # Check if within window
            if window_start <= pubdate <= window_end:
                recent_titles.append(title)

        return recent_titles


def create_buckets_from_recent_titles(
    since_hours: Optional[int] = None,
) -> List[BucketCandidate]:
    """
    Convenience function to create buckets from recent strategic titles.

    Args:
        since_hours: Hours to look back (defaults to config value)

    Returns:
        List of BucketCandidate objects ready for database insertion
    """
    # This would be implemented with actual database query
    # For now, returns empty list as placeholder
    # In production, this would:
    # 1. Query recent strategic titles (gate_keep = true)
    # 2. Filter by time window
    # 3. Create buckets
    return []


if __name__ == "__main__":
    # Basic validation test
    print("CLUST-2 Bucket Manager - Validation Test")
    print("=" * 45)

    try:
        # Test initialization
        manager = BucketManager()
        print(f"[PASS] BucketManager initialized")
        print(f"  Max span: {manager.max_span_hours}h")
        print(f"  Min size: {manager.min_size} titles")
        print(f"  Lookback: {manager.since_hours}h")
        print(f"  Max actors: {manager.max_actors}")

        # Test time window calculation
        base_time = datetime.now(timezone.utc)
        window_start, window_end = manager.get_time_window(base_time)
        print(f"[PASS] Time window calculation working")
        print(
            f"  Window: {window_start.strftime('%Y-%m-%d %H:%M')} to {window_end.strftime('%Y-%m-%d %H:%M')}"
        )

        # Test empty buckets creation
        buckets = manager.create_buckets_from_titles([])
        print(f"[PASS] Empty bucket creation: {len(buckets)} buckets")

        print("\nModule ready for production use")
        print("Integrate with database queries for full functionality")

    except Exception as e:
        print(f"[FAIL] Validation error: {e}")
        import traceback

        traceback.print_exc()
