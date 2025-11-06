"""Test events digest generation on a single CTM"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config


async def extract_events_from_titles(
    centroid_label: str, track: str, month: str, titles: list
) -> list:
    """Extract events using LLM"""
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
        "temperature": 0.3,
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


async def test_single_ctm(ctm_id: str):
    """Test events digest generation on a single CTM"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Get CTM details
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       cent.label
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.id = %s
            """,
                (ctm_id,),
            )
            result = cur.fetchone()

            if not result:
                print(f"CTM {ctm_id} not found")
                return

            ctm_id, centroid_id, track, month, title_count, centroid_label = result

        print("CTM Details:")
        print(f"  ID: {ctm_id}")
        print(f"  Centroid: {centroid_label} ({centroid_id})")
        print(f"  Track: {track}")
        print(f"  Month: {month.strftime('%Y-%m')}")
        print(f"  Title Count: {title_count}")

        # Fetch titles for this CTM
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title_display, pubdate_utc
                FROM titles_v3
                WHERE %s = ANY(ctm_ids)
                ORDER BY pubdate_utc ASC
            """,
                (ctm_id,),
            )
            titles = cur.fetchall()

        print(f"\nTitles ({len(titles)}):")
        for i, (tid, text, pubdate) in enumerate(titles):
            try:
                print(f"  [{i}] {pubdate.strftime('%Y-%m-%d')}: {text}")
            except UnicodeEncodeError:
                # Skip printing titles with encoding issues
                print(
                    f"  [{i}] {pubdate.strftime('%Y-%m-%d')}: [title with special characters]"
                )

        print("\nExtracting events...")

        # Extract events using LLM
        events = await extract_events_from_titles(
            centroid_label, track, month.strftime("%Y-%m"), titles
        )

        if events:
            print(f"\nExtracted {len(events)} distinct events:")
            for i, event in enumerate(events, 1):
                print(f"\nEvent {i}:")
                print(f"  Date: {event['date']}")
                print(f"  Summary: {event['summary']}")
                print(f"  Source titles: {len(event['source_title_ids'])}")

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

            print("\nUpdated CTM with events digest")
        else:
            print("\nNo events extracted")

    finally:
        conn.close()


if __name__ == "__main__":
    ctm_id = "114979ac-c9b6-4979-829f-1f5290989a12"
    asyncio.run(test_single_ctm(ctm_id))
