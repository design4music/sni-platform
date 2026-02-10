"""
SNI Pipeline Backfill Script

One-time script to process all existing backlog:
- Phase 4.5a: Generate summaries for ALL events
- Phase 4.1: Aggregate ALL CTMs

Run this ONCE to catch up, then let the daemon handle incremental flow.

Usage:
    python -m pipeline.runner.backfill_pipeline
    python -m pipeline.runner.backfill_pipeline --phase 4.5a  # Only event summaries
    python -m pipeline.runner.backfill_pipeline --phase 4.1   # Only aggregation
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from pipeline.phase_4.consolidate_topics import process_ctm as phase41_aggregate
from pipeline.phase_4.generate_event_summaries_4_5a import (
    process_events as phase45a_process,
)


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_backlog_stats():
    """Get current backlog counts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Events needing summaries
            cur.execute(
                """
                SELECT COUNT(*)
                FROM events_v3 e
                JOIN ctm c ON c.id = e.ctm_id
                WHERE c.is_frozen = false
                  AND (e.title IS NULL OR e.summary LIKE 'Topic:%%' OR e.summary LIKE 'Other %%')
            """
            )
            events_need_summary = cur.fetchone()[0]

            # Events with summaries
            cur.execute(
                """
                SELECT COUNT(*)
                FROM events_v3 e
                JOIN ctm c ON c.id = e.ctm_id
                WHERE c.is_frozen = false
                  AND e.title IS NOT NULL
                  AND e.summary NOT LIKE 'Topic:%%'
                  AND e.summary NOT LIKE 'Other %%'
            """
            )
            events_have_summary = cur.fetchone()[0]

            # CTMs needing aggregation (never aggregated or have new content)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM ctm
                WHERE title_count >= 3 AND is_frozen = false
                  AND EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = ctm.id)
                  AND (
                      last_aggregated_at IS NULL
                      OR title_count > COALESCE(title_count_at_aggregation, 0)
                  )
            """
            )
            ctms_need_aggregation = cur.fetchone()[0]

            # Total CTMs with events
            cur.execute(
                """
                SELECT COUNT(*)
                FROM ctm
                WHERE title_count >= 3 AND is_frozen = false
                  AND EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = ctm.id)
            """
            )
            total_ctms = cur.fetchone()[0]

            return {
                "events_need_summary": events_need_summary,
                "events_have_summary": events_have_summary,
                "ctms_need_aggregation": ctms_need_aggregation,
                "total_ctms": total_ctms,
            }
    finally:
        conn.close()


async def backfill_event_summaries(batch_size: int = 500, concurrency: int = 10):
    """Process ALL events that need summaries."""
    print("\n" + "=" * 70)
    print("PHASE 4.5a BACKFILL: Event Summaries")
    print("=" * 70)

    total_processed = 0
    batch_num = 0

    while True:
        stats = get_backlog_stats()
        remaining = stats["events_need_summary"]

        if remaining == 0:
            print("\nAll events have summaries!")
            break

        batch_num += 1
        print(
            "\nBatch {}: Processing up to {} events ({} remaining)...".format(
                batch_num, batch_size, remaining
            )
        )

        start_time = time.time()
        await phase45a_process(max_events=batch_size, concurrency=concurrency)
        duration = time.time() - start_time

        # Check how many were actually processed
        new_stats = get_backlog_stats()
        processed = stats["events_need_summary"] - new_stats["events_need_summary"]
        total_processed += processed

        print(
            "Batch {} complete: {} events in {:.1f}s ({:.1f} events/sec)".format(
                batch_num,
                processed,
                duration,
                processed / duration if duration > 0 else 0,
            )
        )

        # Safety: if no progress, break to avoid infinite loop
        if processed == 0:
            print("No events processed - may be an issue. Stopping.")
            break

    print("\n" + "-" * 70)
    print("PHASE 4.5a BACKFILL COMPLETE")
    print("Total events processed: {}".format(total_processed))
    print("-" * 70)


def backfill_topic_aggregation(max_ctms_per_batch: int = 20):
    """Aggregate ALL CTMs that need it."""
    print("\n" + "=" * 70)
    print("PHASE 4.1 BACKFILL: Topic Aggregation")
    print("=" * 70)

    conn = get_connection()
    total_processed = 0
    batch_num = 0

    try:
        while True:
            # Get CTMs needing aggregation
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, centroid_id, track, title_count
                    FROM ctm
                    WHERE title_count >= 3 AND is_frozen = false
                      AND EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = ctm.id)
                      AND (
                          last_aggregated_at IS NULL
                          OR title_count > COALESCE(title_count_at_aggregation, 0)
                      )
                    ORDER BY
                        last_aggregated_at NULLS FIRST,
                        title_count DESC
                    LIMIT %s
                    """,
                    (max_ctms_per_batch,),
                )
                ctms = cur.fetchall()

            if not ctms:
                print("\nAll CTMs are aggregated!")
                break

            batch_num += 1
            print("\nBatch {}: Processing {} CTMs...".format(batch_num, len(ctms)))

            for ctm_id, centroid_id, track, title_count in ctms:
                try:
                    print(
                        "  Aggregating {} / {} ({} titles)...".format(
                            centroid_id, track, title_count
                        )
                    )
                    phase41_aggregate(ctm_id=ctm_id, dry_run=False)

                    # Mark as aggregated
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE ctm
                            SET last_aggregated_at = NOW(),
                                title_count_at_aggregation = title_count
                            WHERE id = %s
                            """,
                            (ctm_id,),
                        )
                    conn.commit()
                    total_processed += 1

                except Exception as e:
                    print("  X Failed: {}".format(e))
                    conn.rollback()

    finally:
        conn.close()

    print("\n" + "-" * 70)
    print("PHASE 4.1 BACKFILL COMPLETE")
    print("Total CTMs processed: {}".format(total_processed))
    print("-" * 70)


async def main(phases: list = None):
    """Run backfill for specified phases (or all)."""
    print("=" * 70)
    print("SNI PIPELINE BACKFILL")
    print("=" * 70)

    # Show initial stats
    stats = get_backlog_stats()
    print("\nInitial backlog:")
    print(
        "  Event summaries: {} need processing, {} already done".format(
            stats["events_need_summary"], stats["events_have_summary"]
        )
    )
    print(
        "  Topic aggregation: {} / {} CTMs need processing".format(
            stats["ctms_need_aggregation"], stats["total_ctms"]
        )
    )

    run_all = phases is None or len(phases) == 0

    # Phase 4.5a: Event Summaries
    if run_all or "4.5a" in phases:
        if stats["events_need_summary"] > 0:
            await backfill_event_summaries()
        else:
            print("\nPhase 4.5a: No backlog - skipping")

    # Phase 4.1: Topic Aggregation
    if run_all or "4.1" in phases:
        # Refresh stats
        stats = get_backlog_stats()
        if stats["ctms_need_aggregation"] > 0:
            backfill_topic_aggregation()
        else:
            print("\nPhase 4.1: No backlog - skipping")

    # Final stats
    print("\n" + "=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)
    stats = get_backlog_stats()
    print("\nFinal state:")
    print(
        "  Event summaries: {} pending, {} complete".format(
            stats["events_need_summary"], stats["events_have_summary"]
        )
    )
    print(
        "  Topic aggregation: {} / {} CTMs pending".format(
            stats["ctms_need_aggregation"], stats["total_ctms"]
        )
    )
    print("\nThe daemon can now handle incremental processing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SNI Pipeline Backfill")
    parser.add_argument(
        "--phase",
        type=str,
        action="append",
        choices=["4.5a", "4.1"],
        help="Specific phase to run (can specify multiple). Default: all",
    )
    args = parser.parse_args()

    asyncio.run(main(phases=args.phase))
