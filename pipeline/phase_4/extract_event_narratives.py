"""
Event Narrative Extraction

Single-pass LLM analysis to identify 2-5 narrative frames from high-source events.
Stores results in narratives table (parallel to epic_narratives).

Selection: events with source_batch_count >= 30 and is_catchall = false.
"""

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.llm_utils import extract_json
from core.prompts import EVENT_NARRATIVE_SYSTEM, EVENT_NARRATIVE_USER

MIN_SOURCES = 30


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_events_for_extraction(conn, limit=50, ctm_id=None):
    """Fetch high-source events that don't yet have narratives."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        where = """
            e.source_batch_count >= %s
            AND e.is_catchall = false
            AND e.title IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM narratives en WHERE en.entity_type = 'event' AND en.entity_id = e.id
            )
        """
        params = [MIN_SOURCES]

        if ctm_id:
            where += " AND e.ctm_id = %s"
            params.append(ctm_id)

        params.append(limit)
        cur.execute(
            """
            SELECT e.id, e.title, e.summary, e.source_batch_count,
                   e.ctm_id, c.centroid_id, c.track
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            WHERE """
            + where
            + """
            ORDER BY e.source_batch_count DESC
            LIMIT %s
        """,
            params,
        )
        return cur.fetchall()


def fetch_event_titles(conn, event_id):
    """Fetch headlines for an event with publisher info."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT t.title_display, t.publisher
            FROM event_v3_titles evt
            JOIN titles_v3 t ON t.id = evt.title_id
            WHERE evt.event_id = %s
            ORDER BY t.published_at DESC
            LIMIT 200
        """,
            (event_id,),
        )
        return cur.fetchall()


def build_titles_block(titles):
    """Format titles for LLM prompt."""
    lines = []
    for i, t in enumerate(titles, 1):
        pub = t.get("publisher", "Unknown")
        lines.append("%d. [%s] %s" % (i, pub, t["title_display"]))
    return "\n".join(lines)


def compute_top_sources(titles, frame_indices):
    """Compute top sources for a narrative frame based on title indices."""
    sources = Counter()
    for idx in frame_indices:
        if 0 < idx <= len(titles):
            pub = titles[idx - 1].get("publisher", "Unknown")
            sources[pub] += 1
    return [s for s, _ in sources.most_common(10)]


async def extract_narratives_for_event(event, titles):
    """Call LLM to extract narrative frames from event titles."""
    titles_block = build_titles_block(titles)

    user_prompt = EVENT_NARRATIVE_USER.format(
        event_title=event["title"] or "",
        event_summary=event["summary"] or "",
        title_count=len(titles),
        titles_block=titles_block,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": EVENT_NARRATIVE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "%s/chat/completions" % config.deepseek_api_url,
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(
                "LLM API error: %d - %s" % (response.status_code, response.text[:200])
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        return extract_json(content)


def save_narratives(conn, event_id, frames, titles):
    """Save extracted narrative frames to narratives table."""
    saved = 0
    with conn.cursor() as cur:
        for frame in frames:
            label = frame.get("label", "").strip()
            if not label:
                continue

            indices = frame.get("title_indices", [])
            title_count = len(indices)
            top_sources = compute_top_sources(titles, indices)

            # Build sample_titles from indices
            sample_titles = []
            for idx in indices[:10]:
                if 0 < idx <= len(titles):
                    t = titles[idx - 1]
                    sample_titles.append(
                        {
                            "title": t["title_display"],
                            "publisher": t.get("publisher", ""),
                        }
                    )

            cur.execute(
                """
                INSERT INTO narratives
                    (entity_type, entity_id, label, description, moral_frame,
                     title_count, top_sources, sample_titles)
                VALUES ('event', %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_id, label) DO UPDATE SET
                    description = EXCLUDED.description,
                    moral_frame = EXCLUDED.moral_frame,
                    title_count = EXCLUDED.title_count,
                    top_sources = EXCLUDED.top_sources,
                    sample_titles = EXCLUDED.sample_titles
            """,
                (
                    event_id,
                    label,
                    frame.get("description"),
                    frame.get("moral_frame"),
                    title_count,
                    top_sources,
                    json.dumps(sample_titles),
                ),
            )
            saved += 1

    conn.commit()
    return saved


async def process_event(conn, event, semaphore):
    """Process a single event: fetch titles, extract narratives, save."""
    async with semaphore:
        event_id = event["id"]
        titles = fetch_event_titles(conn, event_id)

        if len(titles) < 10:
            print("  Skipping %s - only %d titles" % (event["title"], len(titles)))
            return 0

        try:
            frames = await extract_narratives_for_event(event, titles)
        except Exception as e:
            print("  ERROR extracting narratives for %s: %s" % (event["title"], e))
            return 0

        if not frames or not isinstance(frames, list):
            print("  No frames extracted for %s" % event["title"])
            return 0

        saved = save_narratives(conn, event_id, frames, titles)
        return saved


async def main_async(args):
    conn = get_db_connection()

    events = fetch_events_for_extraction(conn, args.limit, args.ctm)
    print("Found %d events eligible for narrative extraction" % len(events))

    if not events:
        print("Nothing to process")
        conn.close()
        return

    if args.dry_run:
        print("\nDry run - would process:")
        for e in events:
            print("  - [%d sources] %s" % (e["source_batch_count"], e["title"]))
        conn.close()
        return

    semaphore = asyncio.Semaphore(args.concurrency)
    stats = {"events": 0, "narratives": 0, "failed": 0}

    for i, event in enumerate(events, 1):
        print(
            "\n[%d/%d] %s (%d sources)"
            % (i, len(events), event["title"], event["source_batch_count"])
        )

        saved = await process_event(conn, event, semaphore)
        if saved > 0:
            stats["events"] += 1
            stats["narratives"] += saved
            print("  -> %d narrative frames saved" % saved)
        else:
            stats["failed"] += 1

    print("\n" + "=" * 50)
    print(
        "Complete: %d events, %d narratives, %d failed"
        % (stats["events"], stats["narratives"], stats["failed"])
    )
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extract narrative frames from high-source events"
    )
    parser.add_argument("--limit", type=int, default=50, help="Max events to process")
    parser.add_argument("--ctm", type=str, help="Filter by CTM ID")
    parser.add_argument(
        "--concurrency", type=int, default=3, help="Max concurrent LLM calls"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be processed"
    )
    args = parser.parse_args()

    print("Event Narrative Extraction")
    print("=" * 50)

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
