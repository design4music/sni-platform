"""
Phase 4.2: Summary Text Generation

Generates 150-250 word narrative summaries for CTMs based on their events digest.

Strategy:
1. Read events_digest from CTM
2. Get centroid metadata for context
3. Use LLM to generate cohesive narrative
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


async def generate_summary(
    centroid_label: str,
    centroid_class: str,
    primary_theater: str,
    track: str,
    month: str,
    events_digest: list,
    centroid_focus: str,
    track_focus: str = None,
) -> str:
    """
    Generate 150-250 word narrative summary from events digest.

    Args:
        centroid_label: Human-readable centroid name
        centroid_class: 'geo' or 'systemic'
        primary_theater: Theater for geo centroids (e.g., 'MIDEAST')
        track: Track category
        month: Month string (YYYY-MM)
        events_digest: List of event dicts
        centroid_focus: Centroid-type focus line from track_configs
        track_focus: Track-specific focus line (optional, GEO only)

    Returns:
        Summary text (150-250 words)
    """
    # Format events timeline
    events_text = "\n".join(
        [f"• {event['date']}: {event['summary']}" for event in events_digest]
    )

    # Build context
    context_parts = [f"Centroid: {centroid_label} ({centroid_class})"]
    if primary_theater:
        context_parts.append(f"Theater: {primary_theater}")
    context_parts.append(f"Track: {track}")
    context_parts.append(f"Month: {month}")

    context = "\n".join(context_parts)

    # Build system prompt with dynamic focus lines
    system_prompt = (
        """You are a strategic intelligence analyst writing monthly summary reports.
Generate a 150-250 word narrative from the provided events timeline.

### Core task

Produce a strategic event synthesis that accurately represents the developments in this period. Events may be thematically related or independent—reflect this natural complexity rather than forcing artificial narrative coherence.

### Requirements:

* Connect events that are genuinely related; separate events that are not
* Group thematically distinct developments into separate paragraphs (2-4 paragraphs as needed)
* Within each thematic group, flow chronologically and explain significance
* Ground all conclusions in explicitly described actions, reactions, or formal statements
* Derive strategic implications from observable developments (e.g., leverage shifts, capability changes, alignment signals, constraints)
* Maintain analytic, neutral, non-normative tone
* Use present/past tense appropriately

### Structure guidance:

* If events form a single coherent story, write 1-2 paragraphs
* If events represent distinct developments, use separate paragraphs for each theme
* Geopolitical reality is complex—multiple unrelated developments can coexist in the same period
* Do NOT force unrelated events into false narrative coherence

### Do NOT:

* List events as bullet points
* Include dates in parentheses unless critical
* Use sensational or emotive language
* Infer motives, intent, or future actions unless explicitly stated by an actor
* Infer current offices or roles (e.g., president/chancellor/opposition leader) unless explicitly stated in the provided events; when uncertain, use name-only references
* Adopt an analyst, editorial, or market-commentary voice
* Add speculation beyond events
* Merge thematically unrelated events into artificial unified narratives

---

### DYNAMIC FOCUS

**Centroid / Structural focus:**
"""
        + centroid_focus
    )

    # Add track focus if provided (GEO only)
    if track_focus:
        system_prompt += "\n\n**Domain / Track focus:**\n" + track_focus

    user_prompt = f"""{context}

Events Timeline:
{events_text}

Generate a 150-250 word narrative summary:"""

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
    events_digest: list,
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
            print(
                f"Processing: {centroid_label} / {track} / {month.strftime('%Y-%m')} ({len(events_digest)} events)"
            )

            # Generate summary using LLM
            summary = await generate_summary(
                centroid_label,
                centroid_class,
                primary_theater,
                track,
                month.strftime("%Y-%m"),
                events_digest,
                centroid_focus,
                track_focus,
            )

            word_count = len(summary.split())
            print(f"  OK: {word_count} words")

            # Update CTM with summary
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ctm
                    SET summary_text = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """,
                    (summary, ctm_id),
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
            # Get CTMs for daily processing with focus lines from track_configs
            # Prioritize: 1) NULL summaries first, 2) then existing if not updated in 24h
            limit_clause = f"LIMIT {max_ctms}" if max_ctms else ""
            cur.execute(
                f"""
                SELECT c.id, c.centroid_id, c.track, c.month,
                       c.events_digest, c.title_count,
                       cent.label, cent.class, cent.primary_theater,
                       tc.llm_summary_centroid_focus,
                       tc.llm_summary_track_focus
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                JOIN track_configs tc ON cent.track_config_id = tc.id
                WHERE c.events_digest IS NOT NULL
                  AND jsonb_array_length(c.events_digest) > 0
                  AND c.is_frozen = false
                  AND c.title_count >= %s
                  AND (
                      c.summary_text IS NULL
                      OR (c.summary_text IS NOT NULL AND c.updated_at < NOW() - INTERVAL '24 hours')
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
            events_digest,
            title_count,
            centroid_label,
            centroid_class,
            primary_theater,
            centroid_focus,
            track_focus_jsonb,
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
                    events_digest,
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
        description="Phase 4.2: Generate summary text for CTMs"
    )
    parser.add_argument(
        "--max-ctms", type=int, help="Maximum number of CTMs to process"
    )

    args = parser.parse_args()

    asyncio.run(process_ctm_batch(max_ctms=args.max_ctms))
