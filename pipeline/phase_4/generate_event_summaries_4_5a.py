"""
Phase 4.5a: Event Summary Generation

Generates structured event data for individual event clusters:
- title: Short headline (5-15 words) for UI and deduplication
- summary: 1-3 sentence narrative
- tags: Lowercase keywords for matching and filtering

Input: Mechanical event labels + source titles
Output: {title, summary, tags} stored in events_v3
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.prompts import EVENT_SUMMARY_SYSTEM_PROMPT


def get_events_needing_summaries(
    conn, max_events: int = None, ctm_id: str = None, centroid_id: str = None
) -> list:
    """Fetch events that need title/summary generation.

    Identifies events by checking if title is NULL (new) or summary matches mechanical label.
    """
    with conn.cursor() as cur:
        conditions = [
            # Events without title OR with mechanical labels
            "(e.title IS NULL OR e.summary LIKE '%%->%%' OR e.summary LIKE '%%titles)%%' OR e.summary LIKE '%%SPIKE]%%')"
        ]
        params = []

        if ctm_id:
            conditions.append("e.ctm_id = %s")
            params.append(ctm_id)

        if centroid_id:
            conditions.append("e.ctm_id IN (SELECT id FROM ctm WHERE centroid_id = %s)")
            params.append(centroid_id)

        where_clause = " AND ".join(conditions)
        limit_clause = "LIMIT %s" if max_events else ""
        if max_events:
            params.append(max_events)

        query = f"""
            SELECT e.id, e.ctm_id, e.summary as label, e.bucket_key, e.source_batch_count,
                   e.date, e.first_seen
            FROM events_v3 e
            WHERE {where_clause}
            ORDER BY e.source_batch_count DESC NULLS LAST
            {limit_clause}
        """

        cur.execute(query, tuple(params) if params else None)

        events = []
        for row in cur.fetchall():
            event_id, ctm_id_val, label, bucket_key, count, date, first_seen = row

            # Fetch titles for this event with dates
            cur.execute(
                """
                SELECT t.title_display, DATE(t.pubdate_utc)
                FROM event_v3_titles evt
                JOIN titles_v3 t ON evt.title_id = t.id
                WHERE evt.event_id = %s
                ORDER BY t.pubdate_utc DESC
                """,
                (event_id,),
            )
            rows = cur.fetchall()
            titles = [r[0] for r in rows]
            dates = [r[1] for r in rows if r[1]]

            events.append(
                {
                    "id": event_id,
                    "ctm_id": ctm_id_val,
                    "label": label,
                    "bucket_key": bucket_key,
                    "count": count or len(titles),
                    "titles": titles,
                    "date": date,
                    "first_seen": first_seen,
                    "title_dates": dates,
                }
            )

        return events


def extract_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON found in response")


async def generate_event_data(titles: list, label: str, max_titles: int = 40) -> dict:
    """Generate title, summary, and tags for an event cluster."""

    # Limit titles to avoid token overflow
    titles_sample = titles[:max_titles]
    titles_text = "\n".join("- %s" % t for t in titles_sample)

    if len(titles) > max_titles:
        titles_text += "\n... and %d more" % (len(titles) - max_titles)

    user_prompt = """Cluster: %s

Headlines:
%s

Generate JSON with title, summary, and tags:""" % (
        label,
        titles_text,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": EVENT_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "%s/chat/completions" % config.deepseek_api_url,
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(
                "LLM API error: %d - %s" % (response.status_code, response.text)
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        result = extract_json_from_response(content)

        # Validate and normalize
        title = result.get("title", "").strip()
        summary = result.get("summary", "").strip()
        tags = result.get("tags", [])

        # Normalize tags: lowercase, strip, filter empty
        tags = [str(t).lower().strip() for t in tags if t]

        # Filter out generic tags and validate format
        generic_tags = {"news", "update", "report", "article", "coverage", "headlines"}
        valid_prefixes = {"person", "org", "place", "topic", "event"}

        normalized_tags = []
        for tag in tags:
            if tag in generic_tags:
                continue
            # If tag has valid prefix, keep as-is
            if ":" in tag:
                prefix = tag.split(":")[0]
                if prefix in valid_prefixes:
                    normalized_tags.append(tag)
                    continue
            # Legacy format (no prefix) - try to infer type or add as topic
            if tag and len(tag) > 1:
                normalized_tags.append("topic:%s" % tag)

        return {
            "title": title,
            "summary": summary,
            "tags": normalized_tags,
        }


async def process_event(
    semaphore: asyncio.Semaphore,
    conn,
    event: dict,
) -> bool:
    """Process a single event with semaphore for concurrency control."""
    async with semaphore:
        try:
            if not event["titles"]:
                print("  Skipping %s: no titles" % event["id"][:8])
                return False

            result = await generate_event_data(
                event["titles"],
                event["label"],
            )

            title = result["title"]
            summary = result["summary"]
            tags = result["tags"]

            # Calculate date range from titles
            title_dates = event.get("title_dates", [])
            if title_dates:
                first_seen = min(title_dates)
                last_seen = max(title_dates)
            else:
                first_seen = event.get("first_seen") or event.get("date")
                last_seen = event.get("date")

            # Update event with all fields
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE events_v3
                    SET title = %s,
                        summary = %s,
                        tags = %s,
                        first_seen = %s,
                        date = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (title, summary, tags, first_seen, last_seen, event["id"]),
                )
            conn.commit()

            print("  [%3d] %s" % (event["count"], title[:60]))
            print("        %s" % summary[:70])
            print("        tags: %s" % tags[:5])

            return True

        except Exception as e:
            print("  X Error for %s: %s" % (event["id"][:8], e))
            conn.rollback()
            return False


async def process_events(
    max_events: int = None,
    ctm_id: str = None,
    centroid_id: str = None,
    concurrency: int = 5,
):
    """Process events to generate title, summary, and tags."""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        events = get_events_needing_summaries(conn, max_events, ctm_id, centroid_id)

        if not events:
            print("No events need processing.")
            return

        print(
            "Processing %d events (concurrency: %d)...\n" % (len(events), concurrency)
        )

        semaphore = asyncio.Semaphore(concurrency)

        tasks = [process_event(semaphore, conn, event) for event in events]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success = sum(1 for r in results if r is True)
        errors = len(results) - success

        print("")
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print("Total events:  %d" % len(events))
        print("Processed:     %d" % success)
        print("Errors:        %d" % errors)

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.5a: Generate title, summary, and tags for events"
    )
    parser.add_argument(
        "--max-events", type=int, help="Maximum number of events to process"
    )
    parser.add_argument(
        "--ctm-id", type=str, help="Process events for specific CTM only"
    )
    parser.add_argument(
        "--centroid",
        type=str,
        help="Process events for specific centroid (e.g., AMERICAS-USA)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=5, help="Number of concurrent LLM calls"
    )

    args = parser.parse_args()

    asyncio.run(
        process_events(
            max_events=args.max_events,
            ctm_id=args.ctm_id,
            centroid_id=args.centroid,
            concurrency=args.concurrency,
        )
    )
