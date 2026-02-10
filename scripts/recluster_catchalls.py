"""
Re-cluster catchall titles for all unfrozen CTMs.

Frees titles from catchall events (unlinks them), then runs incremental
clustering which picks them up, matches against existing topics, forms
new topics from clusters, and puts true singletons back in catchalls.

Usage:
    python scripts/recluster_catchalls.py             # dry run
    python scripts/recluster_catchalls.py --apply      # apply
    python scripts/recluster_catchalls.py --ctm-id X   # single CTM
"""

import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2  # noqa: E402

from core.config import config  # noqa: E402
from pipeline.phase_4.incremental_clustering import process_ctm_for_daemon  # noqa: E402


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def free_catchall_titles(conn, ctm_id):
    """Unlink all titles from catchall events for a CTM. Returns count freed."""
    cur = conn.cursor()

    # Get catchall event IDs and their title counts
    cur.execute(
        """SELECT e.id, e.event_type, e.bucket_key, e.source_batch_count
           FROM events_v3 e
           WHERE e.ctm_id = %s AND e.is_catchall = true
             AND e.source_batch_count > 0""",
        (ctm_id,),
    )
    catchalls = cur.fetchall()

    if not catchalls:
        return 0, 0

    total_freed = 0
    for event_id, event_type, bucket_key, count in catchalls:
        # Delete title-event links
        cur.execute(
            "DELETE FROM event_v3_titles WHERE event_id = %s",
            (event_id,),
        )
        freed = cur.rowcount
        total_freed += freed

        # Delete the empty catchall event
        cur.execute("DELETE FROM events_v3 WHERE id = %s", (event_id,))

    return total_freed, len(catchalls)


def main():
    parser = argparse.ArgumentParser(description="Re-cluster catchall titles")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--ctm-id", type=str, help="Process single CTM")
    args = parser.parse_args()

    dry_run = not args.apply
    conn = get_connection()

    try:
        cur = conn.cursor()

        if args.ctm_id:
            cur.execute(
                "SELECT id, centroid_id, track, month, title_count FROM ctm WHERE id = %s",
                (args.ctm_id,),
            )
        else:
            cur.execute(
                """SELECT id, centroid_id, track, month, title_count FROM ctm
                   WHERE is_frozen = false AND title_count >= 3
                   ORDER BY title_count DESC"""
            )

        ctms = cur.fetchall()
        print(
            "{} - Processing {} CTMs".format(
                "DRY RUN" if dry_run else "APPLYING", len(ctms)
            )
        )

        total_freed = 0
        total_new_events = 0
        ctms_affected = 0
        start = time.time()

        for i, (ctm_id, centroid_id, track, month, title_count) in enumerate(ctms):
            # Phase 1: Free catchall titles
            freed, catchall_count = free_catchall_titles(conn, ctm_id)

            if freed == 0:
                continue

            ctms_affected += 1
            total_freed += freed

            if dry_run:
                conn.rollback()
                print(
                    "  [{}/{}] {} / {} ({}): {} titles from {} catchalls would be freed".format(
                        i + 1,
                        len(ctms),
                        centroid_id,
                        track,
                        month,
                        freed,
                        catchall_count,
                    )
                )
                continue

            # Phase 2: Re-cluster (picks up freed titles as unlinked)
            new_events = process_ctm_for_daemon(conn, ctm_id, centroid_id, track)
            conn.commit()

            total_new_events += new_events
            elapsed = time.time() - start

            print(
                "  [{}/{}] {} / {} ({}): freed {} -> {} new events ({:.0f}s elapsed)".format(
                    i + 1,
                    len(ctms),
                    centroid_id,
                    track,
                    month,
                    freed,
                    new_events,
                    elapsed,
                )
            )

        print("\n--- TOTALS ---")
        print("CTMs affected: {}".format(ctms_affected))
        print("Catchall titles freed: {}".format(total_freed))
        if not dry_run:
            print("New events created: {}".format(total_new_events))
            print("Time: {:.0f}s".format(time.time() - start))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
