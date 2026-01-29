"""
Phase 4.5: Summary Text Generation

Generates 150-250 word narrative summaries for CTMs based on clustered events.

Input: Mechanical event labels from Phase 4 clustering
  e.g. "US_EXECUTIVE -> ECONOMIC_PRESSURE (137 titles)"

Output: Narrative prose summary for the frontend

Strategy:
1. Read events from events_v3 table (mechanical labels with source counts)
2. Get centroid metadata for context
3. Use LLM to interpret labels and generate cohesive narrative
4. Store in summary_text field
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.prompts import CTM_SUMMARY_SYSTEM_PROMPT, CTM_SUMMARY_USER_PROMPT


def get_events_for_ctm(conn, ctm_id: str) -> list:
    """Fetch enriched events from events_v3 with their narrative summaries.

    Only returns events that have been enriched by Phase 4.5a (title IS NOT NULL).
    Catchall events are included for counting but skipped during formatting.
    Returns events ordered by importance (non-catchall first, then by count).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.date::text, e.summary, e.source_batch_count,
                   e.event_type, e.bucket_key, e.is_catchall
            FROM events_v3 e
            WHERE e.ctm_id = %s
              AND e.title IS NOT NULL
            ORDER BY e.is_catchall ASC, e.source_batch_count DESC
            """,
            (ctm_id,),
        )
        events = []
        for row in cur.fetchall():
            date, summary, count, event_type, bucket_key, is_catchall = row
            events.append(
                {
                    "date": date,
                    "summary": summary,
                    "count": count or 0,
                    "event_type": event_type,
                    "bucket_key": bucket_key,
                    "is_catchall": is_catchall,
                }
            )

        return events


def format_events_for_digest(events: list) -> str:
    """Format event summaries for CTM digest generation."""
    lines = []

    for event in events:
        # Skip catchall events in summary
        if event.get("is_catchall"):
            continue

        count = event.get("count", 0)
        summary = event.get("summary", "")

        # Format: [count] summary
        lines.append(f"[{count} sources] {summary}")

    return "\n\n".join(lines)


async def generate_summary(
    centroid_label: str,
    centroid_class: str,
    primary_theater: str,
    track: str,
    month: str,
    events: list,
    centroid_focus: str,
    track_focus: str = None,
) -> str:
    """
    Generate 150-250 word narrative summary from event summaries.

    Args:
        centroid_label: Human-readable centroid name
        centroid_class: 'geo' or 'systemic'
        primary_theater: Theater for geo centroids (e.g., 'MIDEAST')
        track: Track category
        month: Month string (YYYY-MM)
        events: List of event dicts with 'summary' field (narrative summaries)
        centroid_focus: Centroid-type focus line from track_configs
        track_focus: Track-specific focus line (optional, GEO only)

    Returns:
        Summary text (150-250 words)
    """
    # Format event summaries for digest
    events_text = format_events_for_digest(events)

    # Safety: refuse to call LLM with no content (prevents hallucination)
    if not events_text.strip():
        raise ValueError(
            "No non-catchall event summaries to digest - skipping LLM call"
        )

    # Build context
    context_parts = [f"Centroid: {centroid_label} ({centroid_class})"]
    if primary_theater:
        context_parts.append(f"Theater: {primary_theater}")
    context_parts.append(f"Track: {track}")
    context_parts.append(f"Month: {month}")

    context = "\n".join(context_parts)

    # Build system prompt with dynamic focus lines
    system_prompt = CTM_SUMMARY_SYSTEM_PROMPT.format(centroid_focus=centroid_focus)

    # Add track focus if provided (GEO only)
    if track_focus:
        system_prompt += "\n\n**Domain / Track focus:**\n" + track_focus

    user_prompt = CTM_SUMMARY_USER_PROMPT.format(
        context=context, events_text=events_text
    )

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.v3_p4_temperature,
        "max_tokens": config.v3_p4_max_tokens,
    }

    async with httpx.AsyncClient(timeout=config.v3_p4_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")

        data = response.json()
        summary = data["choices"][0]["message"]["content"].strip()

        return summary


async def process_single_ctm(
    semaphore: asyncio.Semaphore,
    ctm_id: str,
    centroid_id: str,
    track: str,
    month,
    title_count: int,
    centroid_label: str,
    centroid_class: str,
    primary_theater: str,
    centroid_focus: str,
    track_focus: str = None,
) -> bool:
    """
    Process a single CTM with semaphore for concurrency control.

    Returns:
        success (bool)
    """
    async with semaphore:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )

        try:
            # Fetch events with their narrative summaries
            events = get_events_for_ctm(conn, ctm_id)

            if not events:
                print(f"Skipping: {centroid_label} / {track} (no events)")
                return False

            # Count non-catchall events
            real_events = [e for e in events if not e.get("is_catchall")]
            total_sources = sum(e.get("count", 0) for e in real_events)

            # Skip if no real (non-catchall) events - nothing to summarize
            if not real_events:
                print(
                    f"Skipping: {centroid_label} / {track} / {month.strftime('%Y-%m')} "
                    "(all events are catchalls - no content to summarize)"
                )
                return False

            print(
                f"Processing: {centroid_label} / {track} / {month.strftime('%Y-%m')} "
                f"({len(real_events)} events, {total_sources} sources)"
            )

            # Generate summary using LLM
            summary = await generate_summary(
                centroid_label,
                centroid_class,
                primary_theater,
                track,
                month.strftime("%Y-%m"),
                events,
                centroid_focus,
                track_focus,
            )

            word_count = len(summary.split())
            print(f"  OK: {word_count} words")

            # Update CTM with summary and track event count for incremental logic
            event_count = len(events)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ctm
                    SET summary_text = %s,
                        updated_at = NOW(),
                        last_summary_at = NOW(),
                        event_count_at_summary = %s
                    WHERE id = %s
                """,
                    (summary, event_count, ctm_id),
                )
            conn.commit()

            return True

        except Exception as e:
            print(f"  X Error: {e}")
            conn.rollback()
            return False

        finally:
            conn.close()


async def process_ctm_batch(max_ctms=None):
    """Process CTMs concurrently with bounded semaphore"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get CTMs for EVENT-DRIVEN processing with focus lines from track_configs
            # Regenerate if: no summary, OR new events appeared (with 24h cooldown)
            limit_clause = f"LIMIT {max_ctms}" if max_ctms else ""
            cur.execute(
                f"""
                SELECT c.id, c.centroid_id, c.track, c.month,
                       c.title_count,
                       cent.label, cent.class, cent.primary_theater,
                       tc.llm_summary_centroid_focus,
                       tc.llm_summary_track_focus,
                       (SELECT COUNT(*) FROM events_v3 e WHERE e.ctm_id = c.id) as event_count
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                JOIN track_configs tc ON cent.track_config_id = tc.id
                WHERE c.is_frozen = false
                  AND c.title_count >= %s
                  -- Must have non-catchall events with real summaries (Phase 4.5a enriched)
                  AND EXISTS (
                      SELECT 1 FROM events_v3 e
                      WHERE e.ctm_id = c.id
                        AND e.is_catchall = false
                        AND e.title IS NOT NULL
                  )
                  AND (
                      -- Never had a summary
                      c.summary_text IS NULL
                      OR (
                          -- Has new events since last summary AND cooldown passed
                          (SELECT COUNT(*) FROM events_v3 e WHERE e.ctm_id = c.id)
                              > COALESCE(c.event_count_at_summary, 0)
                          AND (c.last_summary_at IS NULL
                               OR c.last_summary_at < NOW() - INTERVAL '24 hours')
                      )
                  )
                ORDER BY
                  (c.summary_text IS NULL) DESC,
                  c.title_count DESC,
                  c.month DESC
                {limit_clause}
            """,
                (config.v3_p4_min_titles,),
            )
            ctms = cur.fetchall()

        print(
            f"Processing {len(ctms)} CTMs concurrently (max {config.v3_p4_max_concurrent} at a time)...\n"
        )

        # Create semaphore for bounded concurrency
        semaphore = asyncio.Semaphore(config.v3_p4_max_concurrent)

        # Create tasks for all CTMs with focus lines
        tasks = []
        for (
            ctm_id,
            centroid_id,
            track,
            month,
            title_count,
            centroid_label,
            centroid_class,
            primary_theater,
            centroid_focus,
            track_focus_jsonb,
            event_count,
        ) in ctms:
            # Extract track-specific focus from JSONB if available
            track_focus = None
            if track_focus_jsonb and centroid_class == "geo":
                # Parse JSONB and extract track-specific focus
                try:
                    track_focus_map = (
                        json.loads(track_focus_jsonb)
                        if isinstance(track_focus_jsonb, str)
                        else track_focus_jsonb
                    )
                    track_focus = track_focus_map.get(track)
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass  # Use None if parsing fails

            tasks.append(
                process_single_ctm(
                    semaphore,
                    ctm_id,
                    centroid_id,
                    track,
                    month,
                    title_count,
                    centroid_label,
                    centroid_class,
                    primary_theater,
                    centroid_focus,
                    track_focus,
                )
            )

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results
        processed_count = 0
        error_count = 0

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            elif result:  # success
                processed_count += 1
            else:
                error_count += 1

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total CTMs:             {len(ctms)}")
        print(f"Successfully processed: {processed_count}")
        print(f"Errors:                 {error_count}")
        print(f"Concurrency level:      {config.v3_p4_max_concurrent}")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 4.5: Generate summary text for CTMs from clustered events"
    )
    parser.add_argument(
        "--max-ctms", type=int, help="Maximum number of CTMs to process"
    )

    args = parser.parse_args()

    asyncio.run(process_ctm_batch(max_ctms=args.max_ctms))
