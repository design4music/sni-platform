#!/usr/bin/env python3
"""Export bucket members grouped by bucket_id to CSV for cluster analysis"""

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from core.database import get_db_session


def export_bucket_clusters():
    """Export bucket members grouped by bucket_id in human-readable format"""

    output_file = Path("bucket_clusters_export.txt")

    print(f"Exporting bucket clusters to {output_file}...")

    with get_db_session() as session:
        # Query all bucket members with bucket and title details
        result = session.execute(
            text(
                """
            SELECT 
                b.bucket_id,
                b.members_count,
                t.title_display
            FROM bucket_members bm
            JOIN buckets b ON bm.bucket_id = b.id
            JOIN titles t ON bm.title_id::uuid = t.id
            ORDER BY b.bucket_id, t.pubdate_utc DESC
        """
            )
        )

        rows = list(result.fetchall())

    print(f"Found {len(rows)} bucket member records")

    # Group by bucket_id
    buckets = {}
    for row in rows:
        bucket_id = row.bucket_id
        if bucket_id not in buckets:
            buckets[bucket_id] = []
        buckets[bucket_id].append(row.title_display or "")

    # Write to text file
    with open(output_file, "w", encoding="utf-8") as f:
        for bucket_id, titles in buckets.items():
            f.write(f"{bucket_id}\n")
            for title in titles:
                f.write(f"{title}\n")
            f.write("\n")  # Empty line between buckets

    print(f"Export complete: {output_file}")

    print(f"\nSummary:")
    print(f"  Total buckets: {len(buckets)}")
    print(f"  Total titles: {len(rows)}")
    print(f"  Avg titles per bucket: {len(rows)/len(buckets):.1f}")

    # Show top 10 largest buckets
    largest_buckets = sorted(buckets.items(), key=lambda x: len(x[1]), reverse=True)[
        :10
    ]
    print(f"\nLargest buckets:")
    for bucket_id, titles in largest_buckets:
        print(f"  {bucket_id}: {len(titles)} titles")


if __name__ == "__main__":
    export_bucket_clusters()
