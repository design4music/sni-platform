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


async def extract_events_from_titles(
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

            # Convert source indices to actual title IDs
            enriched_events = []
            for event in events:
                title_ids = [
                    str(titles[idx][0]) for idx in event["source_title_indices"]
                ]
                enriched_events.append(
                    {
                        "date": event["date"],
                        "summary": event["summary"],
                        "source_title_ids": title_ids,
                    }
                )

            return enriched_events

        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response: {events_json}")
            return []


async def process_ctm_batch(max_ctms=None):
    """Process CTMs that need events digest generation"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get CTMs with titles but empty events_digest
            limit_clause = f"LIMIT {max_ctms}" if max_ctms else ""
            cur.execute(
                f"""
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       cent.label
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.title_count > 0
                  AND (c.events_digest = '[]'::jsonb OR c.events_digest IS NULL)
                  AND c.is_frozen = false
                ORDER BY c.title_count DESC, c.month DESC
                {limit_clause}
            """
            )
            ctms = cur.fetchall()

        print(f"Processing {len(ctms)} CTMs for events digest generation...\n")

        processed_count = 0
        error_count = 0
        total_events = 0

        for ctm_id, centroid_id, track, month, title_count, centroid_label in ctms:
            try:
                # Fetch titles for this CTM via title_assignments junction table
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
                    continue

                print(
                    f"Processing CTM: {centroid_label} / {track} / {month.strftime('%Y-%m')}"
                )
                print(f"  {len(titles)} titles")

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

                    print(f"  OK: Extracted {len(events)} distinct events")
                    total_events += len(events)
                    processed_count += 1
                else:
                    print("  X: No events extracted")
                    error_count += 1

            except Exception as e:
                print(f"  X Error processing CTM {ctm_id}: {e}")
                error_count += 1
                conn.rollback()
                continue

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total CTMs:          {len(ctms)}")
        print(f"Successfully processed: {processed_count}")
        print(f"Total events extracted: {total_events}")
        print(f"Errors:              {error_count}")

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
