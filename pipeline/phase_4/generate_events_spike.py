"""
Event Generation - Bucket Pass-through.

Generates events_digest from existing bucket structure.
No hardcoded semantic rules - bucket assignment comes from upstream alias matching.

Output format:
[{
    "date": "2026-01-15",
    "summary": "Coverage description",
    "source_title_ids": ["uuid1", "uuid2"],
    "event_type": "domestic" | "bilateral" | "other_international",
    "bucket_key": "ASIA-CHINA" | null
}]
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import Json

from core.config import config


def load_ctm_titles(conn, ctm_id: str) -> dict[str, list[dict]]:
    """
    Load titles for a CTM, grouped by bucket from existing events_digest.

    Returns dict of bucket_key -> list of title dicts.
    Bucket keys: 'DOMESTIC', bilateral keys like 'ASIA-CHINA', 'OTHER-INTERNATIONAL'
    """
    cur = conn.cursor()

    # Get current events_digest to extract bucket structure
    cur.execute(
        """
        SELECT events_digest
        FROM ctm
        WHERE id = %s
    """,
        (ctm_id,),
    )
    row = cur.fetchone()

    if not row or not row[0]:
        # No existing events - load all titles as DOMESTIC
        cur.execute(
            """
            SELECT t.id::text, t.pubdate_utc::date
            FROM title_assignments ta
            JOIN titles_v3 t ON ta.title_id = t.id
            WHERE ta.ctm_id = %s
        """,
            (ctm_id,),
        )

        titles = [{"id": r[0], "pubdate": r[1]} for r in cur.fetchall()]
        return {"DOMESTIC": titles} if titles else {}

    events = row[0]

    # Group title IDs by bucket from existing structure
    bucket_ids = defaultdict(set)
    for e in events:
        etype = e.get("event_type")
        bucket_key = e.get("bucket_key")
        title_ids = e.get("source_title_ids", [])

        if etype in (None, "domestic"):
            bucket_ids["DOMESTIC"].update(title_ids)
        elif etype == "bilateral" and bucket_key:
            bucket_ids[bucket_key].update(title_ids)
        elif etype == "other_international":
            bucket_ids["OTHER-INTERNATIONAL"].update(title_ids)

    # Load title data
    all_ids = list(set(tid for ids in bucket_ids.values() for tid in ids))
    if not all_ids:
        return {}

    cur.execute(
        """
        SELECT id::text, pubdate_utc::date
        FROM titles_v3
        WHERE id::text = ANY(%s)
    """,
        (all_ids,),
    )

    title_data = {r[0]: {"id": r[0], "pubdate": r[1]} for r in cur.fetchall()}

    # Build bucket -> titles mapping
    buckets = {}
    for bucket_key, ids in bucket_ids.items():
        titles = [title_data[tid] for tid in ids if tid in title_data]
        if titles:
            buckets[bucket_key] = titles

    return buckets


def create_coverage_event(
    titles: list[dict], event_type: str, bucket_key: str = None, label: str = "Coverage"
) -> dict:
    """Create a coverage event for a bucket."""
    if not titles:
        return None

    latest_date = max(t["pubdate"] for t in titles)

    return {
        "date": latest_date.isoformat(),
        "summary": label,
        "source_title_ids": [t["id"] for t in titles],
        "event_type": event_type,
        "bucket_key": bucket_key,
    }


def process_bucket(titles: list[dict], bucket_key: str) -> list[dict]:
    """
    Process a single bucket - create coverage event.

    Returns list of event dicts in events_digest format.
    """
    # Determine event_type and label based on bucket_key
    if bucket_key == "DOMESTIC":
        event_type = "domestic"
        bk = None
        label = "Domestic Coverage"
    elif bucket_key == "OTHER-INTERNATIONAL":
        event_type = "other_international"
        bk = None
        label = "Other International Coverage"
    else:
        event_type = "bilateral"
        bk = bucket_key
        # Extract country name from bucket_key: "ASIA-CHINA" -> "China"
        country = bucket_key.split("-")[-1].title()
        label = "{} Coverage".format(country)

    event = create_coverage_event(titles, event_type, bk, label)
    return [event] if event else []


def generate_events_for_ctm(
    conn,
    ctm_id: str,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Generate events for a single CTM.

    Returns (event_count, title_coverage_count).
    """
    buckets = load_ctm_titles(conn, ctm_id)

    if not buckets:
        return 0, 0

    all_events = []

    for bucket_key, titles in buckets.items():
        bucket_events = process_bucket(titles, bucket_key)
        all_events.extend(bucket_events)

    # Sort events by date
    all_events.sort(key=lambda e: e["date"])

    # Count titles in events
    title_coverage = len(
        set(tid for e in all_events for tid in e.get("source_title_ids", []))
    )

    if not dry_run and all_events:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE ctm
            SET events_digest = %s, updated_at = NOW()
            WHERE id = %s
        """,
            (Json(all_events), ctm_id),
        )
        conn.commit()

    return len(all_events), title_coverage


def process_all_ctms(
    centroid_filter: str = None,
    track_filter: str = None,
    limit: int = None,
    dry_run: bool = False,
):
    """
    Process CTMs - generate coverage events per bucket.

    Args:
        centroid_filter: Only process this centroid (e.g., 'AMERICAS-USA')
        track_filter: Only process this track (e.g., 'geo_economy')
        limit: Max CTMs to process
        dry_run: If True, don't write to database
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    cur = conn.cursor()

    # Build query with filters
    min_titles = getattr(config, "events_min_ctm_titles", 10)
    where_clauses = ["c.title_count >= %s"]
    params = [min_titles]

    if centroid_filter:
        where_clauses.append("c.centroid_id = %s")
        params.append(centroid_filter)

    if track_filter:
        where_clauses.append("c.track = %s")
        params.append(track_filter)

    where_sql = " AND ".join(where_clauses)
    limit_sql = "LIMIT %s" if limit else ""
    if limit:
        params.append(limit)

    cur.execute(
        """
        SELECT c.id, c.centroid_id, c.track, c.month, c.title_count
        FROM ctm c
        WHERE {}
        ORDER BY c.title_count DESC
        {}
    """.format(
            where_sql, limit_sql
        ),
        params,
    )

    ctms = cur.fetchall()

    print("Processing {} CTMs...".format(len(ctms)))
    if dry_run:
        print("(DRY RUN - no database writes)")
    print()

    total_events = 0
    total_titles_covered = 0
    processed = 0
    errors = 0

    for ctm_id, centroid_id, track, month, title_count in ctms:
        try:
            event_count, title_coverage = generate_events_for_ctm(
                conn,
                ctm_id,
                dry_run=dry_run,
            )

            print(
                "{} / {} / {} - {} titles -> {} events".format(
                    centroid_id,
                    track,
                    month.strftime("%Y-%m"),
                    title_count,
                    event_count,
                )
            )

            total_events += event_count
            total_titles_covered += title_coverage
            processed += 1

        except Exception as e:
            print("ERROR {} / {}: {}".format(centroid_id, track, str(e)[:50]))
            errors += 1

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("CTMs processed: {}".format(processed))
    print("Errors: {}".format(errors))
    print("Total events created: {}".format(total_events))
    print("Total titles covered: {}".format(total_titles_covered))

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate coverage events per bucket (no clustering)"
    )
    parser.add_argument(
        "--centroid", type=str, help="Filter by centroid ID (e.g., AMERICAS-USA)"
    )
    parser.add_argument(
        "--track", type=str, help="Filter by track (e.g., 'geo_economy')"
    )
    parser.add_argument("--limit", type=int, help="Max CTMs to process")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database, just show what would happen",
    )

    args = parser.parse_args()

    process_all_ctms(
        centroid_filter=args.centroid,
        track_filter=args.track,
        limit=args.limit,
        dry_run=args.dry_run,
    )
