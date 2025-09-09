#!/usr/bin/env python3
"""
CLUST-2 Runner
Executes the Big-Bucket Grouping phase for actor-set clustering
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.clust2.bucket_db import BucketDB, get_strategic_titles_for_bucketing
from apps.clust2.bucket_manager import BucketManager
from core.config import get_config


def run_clust2(
    hours_back: int = None, dry_run: bool = False, summary: bool = False
) -> dict:
    """
    Execute CLUST-2 Big-Bucket Grouping phase.

    Args:
        hours_back: Hours to look back for strategic titles
        dry_run: If True, don't insert buckets into database

    Returns:
        Results dictionary with statistics
    """
    config = get_config()

    # Use config setting if hours_back not specified
    if hours_back is None:
        hours_back = config.processing_window_hours

    # Set bucket_max_span_hours to match processing window for consistency
    if config.bucket_max_span_hours < hours_back:
        config.bucket_max_span_hours = hours_back

    bucket_manager = BucketManager()
    bucket_db = BucketDB()

    start_time = datetime.now(timezone.utc)

    print(f"CLUST-2: Big-Bucket Grouping")
    print(f"Looking back {hours_back} hours")
    print(
        f"Config: max_span={config.bucket_max_span_hours}h, min_size={config.bucket_min_size}, max_actors={config.bucket_max_actors}"
    )

    # Query strategic titles
    titles = get_strategic_titles_for_bucketing(hours_back)
    print(f"Found {len(titles)} strategic titles")

    if not titles:
        print("No strategic titles found - skipping CLUST-2")
        return {
            "titles_processed": 0,
            "buckets_created": 0,
            "buckets_inserted": 0,
            "duration_seconds": 0,
        }

    # Titles are already filtered by the query time window
    recent_titles = titles
    print(f"Using {len(recent_titles)} strategic titles for bucketing")

    # Create buckets
    bucket_candidates = bucket_manager.create_buckets_from_titles(recent_titles)
    print(f"Created {len(bucket_candidates)} bucket candidates")

    # Show bucket details
    if summary and bucket_candidates:
        # Summary statistics
        sizes = [b.members_count for b in bucket_candidates]
        spans = [b.span_hours for b in bucket_candidates]

        sizes.sort()
        spans.sort()

        print(f"Summary Statistics:")
        print(
            f"  Bucket sizes - min: {min(sizes)}, median: {sizes[len(sizes)//2] if sizes else 0}, p95: {sizes[int(0.95*len(sizes))] if sizes else 0}"
        )
        print(
            f"  Time spans - min: {min(spans):.1f}h, median: {spans[len(spans)//2]:.1f}h, max: {max(spans):.1f}h"
        )

        # Rejection analysis
        if len(recent_titles) > 0:
            actor_groups = bucket_manager.group_titles_by_actor_sets(recent_titles)
            total_groups = len(actor_groups)
            accepted_groups = len(bucket_candidates)
            rejected_pct = (
                ((total_groups - accepted_groups) / total_groups * 100)
                if total_groups > 0
                else 0
            )
            print(
                f"  Rejection rate: {rejected_pct:.1f}% ({total_groups - accepted_groups}/{total_groups} groups)"
            )
    else:
        for bucket in bucket_candidates:
            print(
                f"  {bucket.bucket_id}: {bucket.members_count} titles, {bucket.span_hours:.1f}h span, actors: {bucket.actor_set}"
            )

    # Insert buckets (unless dry run)
    buckets_inserted = 0
    if not dry_run and bucket_candidates:
        print("Inserting buckets...")
        inserted_uuids = bucket_db.insert_buckets_batch(bucket_candidates)
        buckets_inserted = len(inserted_uuids)
        print(f"Inserted {buckets_inserted} buckets")
    elif dry_run:
        print("DRY RUN - buckets not inserted")

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    results = {
        "titles_processed": len(titles),
        "buckets_created": len(bucket_candidates),
        "buckets_inserted": buckets_inserted,
        "duration_seconds": duration,
    }

    print(f"CLUST-2 completed in {duration:.2f}s")
    return results


def main():
    """CLI entry point for CLUST-2"""
    parser = argparse.ArgumentParser(description="CLUST-2: Big-Bucket Grouping")
    parser.add_argument(
        "--hours",
        type=int,
        default=None,
        help="Hours to look back for strategic titles (default: from config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without inserting buckets",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics instead of individual bucket details",
    )

    args = parser.parse_args()

    try:
        results = run_clust2(
            hours_back=args.hours, dry_run=args.dry_run, summary=args.summary
        )

        print("\nResults:")
        print(f"  Titles processed: {results['titles_processed']}")
        print(f"  Buckets created: {results['buckets_created']}")
        print(f"  Buckets inserted: {results['buckets_inserted']}")
        print(f"  Duration: {results['duration_seconds']:.2f}s")

    except Exception as e:
        print(f"CLUST-2 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
