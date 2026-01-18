"""
Backfill events_v3 tables from existing ctm.events_digest JSONB data

This script migrates historical events from JSONB to normalized tables.
Safe to run multiple times (idempotent).
"""

import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))

import os

project_root = Path(__file__).parent.parent
os.chdir(project_root)

from core.config import config  # noqa: E402


def backfill_events_v3(limit=None):
    """
    Migrate events from ctm.events_digest to events_v3 tables.

    Args:
        limit: Optional limit on number of CTMs to process
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        print("=" * 60)
        print("BACKFILL: events_v3 from ctm.events_digest")
        print("=" * 60)
        print()

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find CTMs with events_digest but no events_v3 entries
            limit_clause = f"LIMIT {limit}" if limit else ""

            cur.execute(
                f"""
                SELECT c.id, c.events_digest, cent.label, c.track, c.month
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.events_digest IS NOT NULL
                  AND jsonb_array_length(c.events_digest) > 0
                  AND NOT EXISTS (
                    SELECT 1 FROM events_v3 WHERE ctm_id = c.id
                  )
                ORDER BY c.month DESC
                {limit_clause}
            """
            )

            ctms = cur.fetchall()

            print(f"CTMs to backfill: {len(ctms)}")
            print()

            if len(ctms) == 0:
                print("All CTMs already migrated!")
                return

            processed = 0
            total_events = 0
            total_titles = 0

            for ctm in ctms:
                ctm_id = ctm["id"]
                events_digest = ctm["events_digest"]
                label = ctm["label"]
                track = ctm["track"]
                month = ctm["month"]

                print(f"Processing: {label} / {track} / {month.strftime('%Y-%m')}")
                print(f"  {len(events_digest)} events in JSONB")

                # Insert events
                for event in events_digest:
                    # Insert event
                    cur.execute(
                        """
                        INSERT INTO events_v3 (
                            ctm_id, date, summary, date_confidence, source_batch_count
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """,
                        (
                            ctm_id,
                            event["date"],
                            event["summary"],
                            event.get("date_confidence", "high"),
                            1,  # Unknown batch count for historical data
                        ),
                    )

                    event_id = cur.fetchone()["id"]
                    total_events += 1

                    # Insert title associations
                    for title_id in event["source_title_ids"]:
                        cur.execute(
                            """
                            INSERT INTO event_v3_titles (event_id, title_id, added_from_batch)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (event_id, title_id) DO NOTHING
                        """,
                            (event_id, title_id, 0),  # Batch 0 = historical data
                        )
                        total_titles += 1

                conn.commit()
                processed += 1
                print(f"  OK: Migrated {len(events_digest)} events")

            print()
            print("=" * 60)
            print("BACKFILL COMPLETE")
            print("=" * 60)
            print(f"CTMs processed:     {processed}")
            print(f"Events migrated:    {total_events}")
            print(f"Title links created: {total_titles}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill events_v3 from JSONB")
    parser.add_argument(
        "--limit", type=int, help="Limit number of CTMs to process (for testing)"
    )

    args = parser.parse_args()

    backfill_events_v3(limit=args.limit)
