"""
Phase 4.1: Events Digest Generation

Extracts distinct events from titles within each CTM and populates events_digest.

Events digest schema:
[{
  "date": "2025-10-15",
  "summary": "Brief event description",
  "source_title_ids": ["uuid1", "uuid2"]
}]

Strategy:
1. Group titles by CTM
2. Sort by pubdate_utc
3. Use LLM to identify distinct events
4. Generate concise summaries
5. Store in events_digest JSONB
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ensure .env is loaded from project root
import os

project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

from core.config import config  # noqa: E402


def validate_and_fix_event_date(event_date_str: str, ctm_month: str) -> tuple[str, str]:
    """
    Validate event date falls within reasonable range of CTM month.

    Args:
        event_date_str: Date string from LLM (YYYY-MM-DD)
        ctm_month: CTM month string (YYYY-MM)

    Returns:
        (fixed_date_str, confidence) where confidence is "high" or "low"
    """
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        ctm_date = datetime.strptime(ctm_month + "-01", "%Y-%m-%d")

        # Calculate valid range: [month_start - 5 days, month_end + 5 days]
        month_start = ctm_date
        # Get last day of month
        if ctm_date.month == 12:
            month_end = ctm_date.replace(day=31)
        else:
            next_month = ctm_date.replace(month=ctm_date.month + 1, day=1)
            month_end = next_month - timedelta(days=1)

        valid_start = month_start - timedelta(days=5)
        valid_end = month_end + timedelta(days=5)

        # Check if date is within valid range
        if valid_start <= event_date <= valid_end:
            return event_date_str, "high"
        else:
            # Date out of range - clamp to month_start and mark as low confidence
            return month_start.strftime("%Y-%m-%d"), "low"

    except (ValueError, Exception):
        # Invalid date format - default to month start
        ctm_date = datetime.strptime(ctm_month + "-01", "%Y-%m-%d")
        return ctm_date.strftime("%Y-%m-%d"), "low"


async def extract_events_from_titles_single_batch(
    centroid_label: str, track: str, month: str, titles: list
) -> list:
    """
    Use LLM to extract distinct events from chronologically ordered titles.

    Args:
        centroid_label: Human-readable centroid name
        track: Track category
        month: Month string (YYYY-MM)
        titles: List of (title_id, title_text, pubdate) tuples

    Returns:
        List of event dicts with date, summary, source_title_ids
    """
    # Format titles with indices for LLM reference
    titles_text = "\n".join(
        [
            f"[{i}] {pubdate.strftime('%Y-%m-%d')}: {text}"
            for i, (_, text, pubdate) in enumerate(titles)
        ]
    )

    system_prompt = """You are analyzing news titles for a specific centroid-track-month combination.
Extract distinct events from these chronologically ordered titles.

Your task:
1. Identify unique developments/events (merge near-duplicate reports)
2. Create 1-2 sentence summaries for each event
3. Link to source title indices
4. Use the most specific date available from source titles

Return ONLY a JSON array, no other text:
[{
  "date": "YYYY-MM-DD",
  "summary": "1-2 sentence event description",
  "source_title_indices": [0, 1, 2]
}]

Guidelines:
- Focus on distinct developments, not repetitive coverage
- Merge similar reports into single events
- Keep summaries concise and factual
- Use journalistic present tense"""

    user_prompt = f"""Centroid: {centroid_label}
Track: {track}
Month: {month}

Titles:
{titles_text}

Extract distinct events as JSON array:"""

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
        "temperature": 0.3,  # Slightly creative for summarization
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=config.llm_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")

        data = response.json()
        events_json = data["choices"][0]["message"]["content"].strip()

        # Parse JSON response
        try:
            # Remove markdown code fences if present
            if events_json.startswith("```"):
                events_json = events_json.split("```")[1]
                if events_json.startswith("json"):
                    events_json = events_json[4:]
                events_json = events_json.strip()

            events = json.loads(events_json)

            # Convert source indices to actual title IDs and validate dates
            enriched_events = []
            for event in events:
                title_ids = [
                    str(titles[idx][0]) for idx in event["source_title_indices"]
                ]

                # Validate and fix date
                fixed_date, confidence = validate_and_fix_event_date(
                    event["date"], month
                )

                enriched_events.append(
                    {
                        "date": fixed_date,
                        "summary": event["summary"],
                        "source_title_ids": title_ids,
                        "date_confidence": confidence,
                    }
                )

            return enriched_events

        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response: {events_json}")
            return []


async def consolidate_events(
    centroid_label: str, track: str, month: str, all_events: list
) -> list:
    """
    Consolidation pass: deduplicate and normalize events from multiple batches.

    Takes events extracted from multiple batches and uses LLM to:
    - Merge duplicate/similar events
    - Normalize dates
    - Combine source_title_ids
    """
    # Format events for consolidation
    events_text = "\n".join(
        [
            f"[{i}] {event['date']}: {event['summary']} (sources: {len(event['source_title_ids'])})"
            for i, event in enumerate(all_events)
        ]
    )

    system_prompt = """You are consolidating events from multiple batches into a final deduplicated timeline.

Your task:
1. Identify duplicate or highly similar events and merge them
2. Keep the most specific date when merging
3. Combine source indices for merged events
4. Preserve all unique events
5. Return consolidated events in chronological order

Return ONLY a JSON array:
[{
  "date": "YYYY-MM-DD",
  "summary": "Consolidated 1-2 sentence description",
  "source_event_indices": [0, 1, 2]
}]

Guidelines:
- Merge events about the same development even if phrased differently
- Keep event summaries concise and factual
- Use the earliest specific date when merging
- Combine all source indices from merged events"""

    user_prompt = f"""Centroid: {centroid_label}
Track: {track}
Month: {month}

Events to consolidate:
{events_text}

Consolidate into deduplicated timeline:"""

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
        "temperature": 0.2,  # Lower for consistency
        "max_tokens": 3000,  # More tokens for consolidated output
    }

    async with httpx.AsyncClient(timeout=config.llm_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")

        data = response.json()
        consolidated_json = data["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences
        if consolidated_json.startswith("```"):
            consolidated_json = consolidated_json.split("```")[1]
            if consolidated_json.startswith("json"):
                consolidated_json = consolidated_json[4:]
            consolidated_json = consolidated_json.strip()

        try:
            consolidated = json.loads(consolidated_json)

            # Map source_event_indices back to title UUIDs and validate dates
            final_events = []
            for event in consolidated:
                combined_title_ids = []
                for idx in event["source_event_indices"]:
                    if idx < len(all_events):
                        combined_title_ids.extend(all_events[idx]["source_title_ids"])

                # Validate and fix date in consolidation
                fixed_date, confidence = validate_and_fix_event_date(
                    event["date"], month
                )

                final_events.append(
                    {
                        "date": fixed_date,
                        "summary": event["summary"],
                        "source_title_ids": combined_title_ids,
                        "date_confidence": confidence,
                    }
                )

            return final_events

        except json.JSONDecodeError as e:
            print(f"Failed to parse consolidation response: {e}")
            print(f"Response: {consolidated_json}")
            return all_events  # Return unmerged events as fallback


async def extract_events_from_titles(
    centroid_label: str, track: str, month: str, titles: list
) -> list:
    """
    Extract events from titles with automatic batching for high-volume CTMs.

    For CTMs with >batch_size titles, uses two-pass approach:
    1. Extract events from each batch separately
    2. Consolidation pass to deduplicate across batches
    """
    batch_size = config.v3_p4_batch_size

    # Single batch: process directly
    if len(titles) <= batch_size:
        return await extract_events_from_titles_single_batch(
            centroid_label, track, month, titles
        )

    # Multi-batch: extract + consolidate
    print(
        f"  High-volume CTM: splitting {len(titles)} titles into batches of {batch_size}"
    )

    all_events = []
    num_batches = (len(titles) + batch_size - 1) // batch_size

    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(titles))
        batch_titles = titles[start_idx:end_idx]

        print(
            f"  Batch {batch_num + 1}/{num_batches}: processing {len(batch_titles)} titles"
        )

        batch_events = await extract_events_from_titles_single_batch(
            centroid_label, track, month, batch_titles
        )

        if batch_events:
            all_events.extend(batch_events)
            print(f"    -> {len(batch_events)} events extracted")
        else:
            print("    -> No events extracted")

    print(f"  Total from batches: {len(all_events)} events")

    # Consolidation pass
    if len(all_events) > 0:
        print("  Consolidating events across batches...")
        consolidated_events = await consolidate_events(
            centroid_label, track, month, all_events
        )
        print(f"  Final: {len(consolidated_events)} consolidated events")
        return consolidated_events
    else:
        return []


async def process_single_ctm(
    semaphore: asyncio.Semaphore,
    ctm_id: str,
    centroid_id: str,
    track: str,
    month,
    title_count: int,
    centroid_label: str,
) -> tuple[bool, int]:
    """
    Process a single CTM with semaphore for concurrency control.

    Returns:
        (success, event_count)
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
            # Fetch titles for this CTM
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT t.id, t.title_display, t.pubdate_utc
                    FROM title_assignments ta
                    JOIN titles_v3 t ON ta.title_id = t.id
                    WHERE ta.ctm_id = %s
                    ORDER BY t.pubdate_utc ASC
                """,
                    (ctm_id,),
                )
                titles = cur.fetchall()

            if not titles:
                print(f"Warning: CTM {ctm_id} has no linked titles, skipping")
                return False, 0

            print(
                f"Processing: {centroid_label} / {track} / {month.strftime('%Y-%m')} ({len(titles)} titles)"
            )

            # Extract events using LLM
            events = await extract_events_from_titles(
                centroid_label, track, month.strftime("%Y-%m"), titles
            )

            if events:
                # Update CTM with events digest
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE ctm
                        SET events_digest = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """,
                        (Json(events), ctm_id),
                    )
                conn.commit()

                print(f"  OK: {len(events)} events extracted")
                return True, len(events)
            else:
                print("  X: No events extracted")
                return False, 0

        except Exception as e:
            print(f"  X Error: {e}")
            conn.rollback()
            return False, 0

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
            # Get CTMs for daily processing - prioritize empty events_digest first
            limit_clause = f"LIMIT {max_ctms}" if max_ctms else ""
            cur.execute(
                f"""
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       cent.label
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.title_count >= %s
                  AND (c.events_digest IS NULL OR jsonb_array_length(c.events_digest) = 0)
                  AND c.is_frozen = false
                ORDER BY c.title_count DESC, c.month DESC
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

        # Create tasks for all CTMs
        tasks = [
            process_single_ctm(
                semaphore,
                ctm_id,
                centroid_id,
                track,
                month,
                title_count,
                centroid_label,
            )
            for ctm_id, centroid_id, track, month, title_count, centroid_label in ctms
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results
        processed_count = 0
        error_count = 0
        total_events = 0

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            elif result[0]:  # success
                processed_count += 1
                total_events += result[1]
            else:
                error_count += 1

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total CTMs:             {len(ctms)}")
        print(f"Successfully processed: {processed_count}")
        print(f"Total events extracted: {total_events}")
        print(f"Errors:                 {error_count}")
        print(f"Concurrency level:      {config.v3_p4_max_concurrent}")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 4.1: Generate events digest for CTMs"
    )
    parser.add_argument(
        "--max-ctms", type=int, help="Maximum number of CTMs to process"
    )

    args = parser.parse_args()

    asyncio.run(process_ctm_batch(max_ctms=args.max_ctms))
