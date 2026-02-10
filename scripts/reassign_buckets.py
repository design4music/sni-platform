"""
Mechanical bucket reassignment for all unfrozen CTMs.

Moves titles to correct bilateral buckets based on centroid_ids:
1. Domestic titles with foreign GEO centroids -> bilateral catchalls
2. OI catchall titles with single foreign GEO -> bilateral catchalls
3. OI catchall titles with multiple foreign GEO -> dominant bilateral catchall

Creates bilateral catchall events where needed. No LLM calls.

Usage:
    python scripts/reassign_buckets.py             # dry run
    python scripts/reassign_buckets.py --apply      # apply changes
    python scripts/reassign_buckets.py --ctm-id X   # single CTM
"""

import argparse
import sys
import uuid
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2  # noqa: E402

from core.config import config  # noqa: E402


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def is_geo_centroid(centroid_id):
    return not centroid_id.startswith("SYS-")


def get_foreign_geo_centroids(centroid_ids, home_centroid_id):
    """Return list of foreign GEO centroids for a title."""
    return [c for c in centroid_ids if c != home_centroid_id and is_geo_centroid(c)]


def find_or_create_catchall(conn, ctm_id, bucket_key, event_type="bilateral"):
    """Find existing catchall for bucket or create one."""
    cur = conn.cursor()
    cur.execute(
        """SELECT id FROM events_v3
           WHERE ctm_id = %s AND bucket_key = %s AND is_catchall = true""",
        (ctm_id, bucket_key),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Create new catchall
    event_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO events_v3
           (id, ctm_id, event_type, bucket_key, is_catchall,
            source_batch_count, date, first_seen)
           VALUES (%s, %s, %s, %s, true, 0, NOW(), NOW())""",
        (event_id, ctm_id, event_type, bucket_key),
    )
    return event_id


def reassign_ctm(conn, ctm_id, centroid_id, dry_run=True):
    """Reassign misplaced titles for one CTM."""
    cur = conn.cursor()
    stats = {
        "domestic_moved": 0,
        "oi_moved": 0,
        "catchalls_created": 0,
        "events_deleted": 0,
    }

    # ---- Phase A: Domestic titles with foreign GEO centroids ----
    cur.execute(
        """SELECT evt.title_id, evt.event_id, t.centroid_ids
           FROM event_v3_titles evt
           JOIN events_v3 e ON e.id = evt.event_id
           JOIN titles_v3 t ON t.id = evt.title_id
           WHERE e.ctm_id = %s AND e.event_type = 'domestic'""",
        (ctm_id,),
    )
    domestic_rows = cur.fetchall()

    moves_domestic = []  # (title_id, old_event_id, target_bucket_key)
    for title_id, event_id, centroid_ids in domestic_rows:
        foreign_geo = get_foreign_geo_centroids(centroid_ids or [], centroid_id)
        if not foreign_geo:
            continue
        # Pick the dominant foreign centroid (most titles in this CTM)
        if len(foreign_geo) == 1:
            target = foreign_geo[0]
        else:
            # Count existing bilateral bucket sizes to pick dominant
            cur.execute(
                """SELECT e.bucket_key, COUNT(*)
                   FROM event_v3_titles evt
                   JOIN events_v3 e ON e.id = evt.event_id
                   WHERE e.ctm_id = %s AND e.event_type = 'bilateral'
                     AND e.bucket_key = ANY(%s)
                   GROUP BY e.bucket_key""",
                (ctm_id, foreign_geo),
            )
            bucket_sizes = dict(cur.fetchall())
            target = max(foreign_geo, key=lambda c: bucket_sizes.get(c, 0))
        moves_domestic.append((title_id, event_id, target))

    # ---- Phase B: OI catchall titles ----
    cur.execute(
        """SELECT evt.title_id, evt.event_id, t.centroid_ids
           FROM event_v3_titles evt
           JOIN events_v3 e ON e.id = evt.event_id
           JOIN titles_v3 t ON t.id = evt.title_id
           WHERE e.ctm_id = %s
             AND e.event_type = 'other_international'
             AND e.is_catchall = true""",
        (ctm_id,),
    )
    oi_rows = cur.fetchall()

    moves_oi = []  # (title_id, old_event_id, target_bucket_key)
    for title_id, event_id, centroid_ids in oi_rows:
        foreign_geo = get_foreign_geo_centroids(centroid_ids or [], centroid_id)
        if not foreign_geo:
            continue
        if len(foreign_geo) == 1:
            target = foreign_geo[0]
        else:
            # Pick largest existing bilateral bucket
            cur.execute(
                """SELECT e.bucket_key, COUNT(*)
                   FROM event_v3_titles evt
                   JOIN events_v3 e ON e.id = evt.event_id
                   WHERE e.ctm_id = %s AND e.event_type = 'bilateral'
                     AND e.bucket_key = ANY(%s)
                   GROUP BY e.bucket_key""",
                (ctm_id, foreign_geo),
            )
            bucket_sizes = dict(cur.fetchall())
            target = max(foreign_geo, key=lambda c: bucket_sizes.get(c, 0))
        moves_oi.append((title_id, event_id, target))

    if not moves_domestic and not moves_oi:
        return stats

    # ---- Apply moves ----
    if dry_run:
        stats["domestic_moved"] = len(moves_domestic)
        stats["oi_moved"] = len(moves_oi)
        # Count unique new buckets
        existing_buckets = set()
        cur.execute(
            """SELECT DISTINCT bucket_key FROM events_v3
               WHERE ctm_id = %s AND is_catchall = true AND event_type = 'bilateral'""",
            (ctm_id,),
        )
        existing_buckets = {r[0] for r in cur.fetchall()}
        new_buckets = set()
        for _, _, bk in moves_domestic + moves_oi:
            if bk not in existing_buckets:
                new_buckets.add(bk)
        stats["catchalls_created"] = len(new_buckets)
        return stats

    # Track affected events for source count update
    affected_events = set()
    target_catchalls = {}  # bucket_key -> catchall event_id

    all_moves = [("domestic", m) for m in moves_domestic] + [
        ("oi", m) for m in moves_oi
    ]

    for source, (title_id, old_event_id, bucket_key) in all_moves:
        # Get or create target catchall
        if bucket_key not in target_catchalls:
            catchall_id = find_or_create_catchall(conn, ctm_id, bucket_key)
            target_catchalls[bucket_key] = catchall_id

        target_id = target_catchalls[bucket_key]

        # Move the title-event link
        cur.execute(
            """UPDATE event_v3_titles
               SET event_id = %s
               WHERE title_id = %s AND event_id = %s""",
            (target_id, title_id, old_event_id),
        )

        affected_events.add(old_event_id)
        affected_events.add(target_id)

        if source == "domestic":
            stats["domestic_moved"] += 1
        else:
            stats["oi_moved"] += 1

    # Update source counts for all affected events
    for event_id in affected_events:
        cur.execute(
            """UPDATE events_v3
               SET source_batch_count = (
                   SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
               ), updated_at = NOW()
               WHERE id = %s""",
            (event_id, event_id),
        )

    # Delete events that became empty
    cur.execute(
        """DELETE FROM events_v3
           WHERE ctm_id = %s AND source_batch_count = 0
           RETURNING id""",
        (ctm_id,),
    )
    deleted = cur.fetchall()
    stats["events_deleted"] = len(deleted)

    # Count newly created catchalls
    stats["catchalls_created"] = len(target_catchalls)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Mechanical bucket reassignment")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry run)"
    )
    parser.add_argument("--ctm-id", type=str, help="Process single CTM")
    args = parser.parse_args()

    dry_run = not args.apply
    conn = get_connection()

    try:
        cur = conn.cursor()

        if args.ctm_id:
            cur.execute(
                "SELECT id, centroid_id, track, month FROM ctm WHERE id = %s",
                (args.ctm_id,),
            )
        else:
            cur.execute(
                """SELECT id, centroid_id, track, month FROM ctm
                   WHERE is_frozen = false AND title_count >= 3
                   ORDER BY title_count DESC"""
            )

        ctms = cur.fetchall()
        print(
            "{} - Processing {} CTMs".format(
                "DRY RUN" if dry_run else "APPLYING", len(ctms)
            )
        )

        totals = defaultdict(int)
        ctms_affected = 0

        for ctm_id, centroid_id, track, month in ctms:
            stats = reassign_ctm(conn, ctm_id, centroid_id, dry_run=dry_run)
            moved = stats["domestic_moved"] + stats["oi_moved"]

            if moved > 0:
                ctms_affected += 1
                print(
                    "  {} / {} ({}): {} domestic + {} OI moved, {} catchalls, {} deleted".format(
                        centroid_id,
                        track,
                        month,
                        stats["domestic_moved"],
                        stats["oi_moved"],
                        stats["catchalls_created"],
                        stats["events_deleted"],
                    )
                )
                for k, v in stats.items():
                    totals[k] += v

            if not dry_run and moved > 0:
                conn.commit()

        print("\n--- TOTALS ---")
        print("CTMs affected: {}".format(ctms_affected))
        print("Domestic titles moved: {}".format(totals["domestic_moved"]))
        print("OI catchall titles moved: {}".format(totals["oi_moved"]))
        print("Catchalls created: {}".format(totals["catchalls_created"]))
        print("Empty events deleted: {}".format(totals["events_deleted"]))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
