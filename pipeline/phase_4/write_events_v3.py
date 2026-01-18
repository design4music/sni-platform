"""
Phase 4 Events V3 Writer

Dual-write module for parallel implementation of events_v3 tables.
Writes canonical events to normalized tables alongside JSONB storage.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def write_events_to_v3_tables(
    conn: Any, ctm_id: str, events: list[dict], batch_count: int = 1
) -> int:
    """
    Write canonical events to events_v3 and event_v3_titles tables.

    This implements the dual-write pattern - writing the same data to both
    JSONB (ctm.events_digest) and normalized tables (events_v3).

    Args:
        conn: psycopg2 connection (already open, will use existing transaction)
        ctm_id: CTM UUID
        events: List of event dicts from LLM consolidation
        batch_count: Number of batches that contributed to these events

    Returns:
        Number of events written

    Event dict structure:
    {
        "date": "2025-01-15",
        "summary": "Event description",
        "source_title_ids": ["uuid1", "uuid2"],
        "date_confidence": "high" or "low"
    }

    Implementation notes:
    - Uses UPSERT logic: if event already exists, updates it
    - Event identity: (ctm_id, date, summary) - same date/summary = same event
    - Title assignment: mechanical union (A U B U C) from all batches
    - No semantic analysis, no keyword matching, just mechanical reassignment
    """
    if not events:
        return 0

    events_written = 0

    with conn.cursor() as cur:
        # Delete existing events for this CTM (full rewrite)
        cur.execute(
            "DELETE FROM events_v3 WHERE ctm_id = %s",
            (ctm_id,),
        )

        for event in events:
            # Check if event already exists (same CTM, date, summary)
            cur.execute(
                """
                SELECT id FROM events_v3
                WHERE ctm_id = %s
                  AND date = %s
                  AND summary = %s
                """,
                (ctm_id, event["date"], event["summary"]),
            )

            existing = cur.fetchone()

            if existing:
                # Event exists - update metadata
                event_id = existing[0]

                cur.execute(
                    """
                    UPDATE events_v3
                    SET date_confidence = %s,
                        source_batch_count = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (event["date_confidence"], batch_count, event_id),
                )
            else:
                # New event - insert
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
                        event["date_confidence"],
                        batch_count,
                    ),
                )

                event_id = cur.fetchone()[0]
                events_written += 1

            # Write title associations (mechanical union)
            # Clear existing titles and rewrite (simpler than merge logic)
            cur.execute(
                """
                DELETE FROM event_v3_titles
                WHERE event_id = %s
                """,
                (event_id,),
            )

            # Insert all title associations
            for title_id in event["source_title_ids"]:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id, added_from_batch)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (event_id, title_id) DO NOTHING
                    """,
                    (event_id, title_id, batch_count),
                )

    return events_written


def cleanup_orphaned_events_v3(conn: Any, ctm_id: str) -> int:
    """
    Remove events_v3 entries that no longer exist in ctm.events_digest.

    This is a safety function for keeping the two systems in sync.
    Should only be needed if events are manually deleted from JSONB.

    Args:
        conn: psycopg2 connection
        ctm_id: CTM UUID

    Returns:
        Number of orphaned events removed
    """
    with conn.cursor() as cur:
        # Get all event summaries from events_digest
        cur.execute(
            """
            SELECT jsonb_array_elements(events_digest)->>'summary' as summary
            FROM ctm
            WHERE id = %s
              AND events_digest IS NOT NULL
            """,
            (ctm_id,),
        )

        digest_summaries = {row[0] for row in cur.fetchall()}

        if not digest_summaries:
            # No events in digest - remove all events_v3 for this CTM
            cur.execute(
                """
                DELETE FROM events_v3
                WHERE ctm_id = %s
                """,
                (ctm_id,),
            )
            return cur.rowcount

        # Remove events that are not in digest
        cur.execute(
            """
            DELETE FROM events_v3
            WHERE ctm_id = %s
              AND summary NOT IN %s
            """,
            (ctm_id, tuple(digest_summaries)),
        )

        return cur.rowcount
