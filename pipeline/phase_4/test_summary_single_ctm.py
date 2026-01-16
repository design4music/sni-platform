"""Test summary generation on a single CTM"""

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
    """Generate 150-250 word narrative summary from events digest"""
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
        "temperature": 0.5,
        "max_tokens": 500,
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
        summary = data["choices"][0]["message"]["content"].strip()

        return summary


async def test_summary_generation(ctm_id: str):
    """Test summary generation on a single CTM"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Get CTM details with focus lines
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month,
                       c.events_digest, c.title_count,
                       cent.label, cent.class, cent.primary_theater,
                       tc.llm_summary_centroid_focus,
                       tc.llm_summary_track_focus
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                JOIN track_configs tc ON cent.track_config_id = tc.id
                WHERE c.id = %s
            """,
                (ctm_id,),
            )
            result = cur.fetchone()

            if not result:
                print(f"CTM {ctm_id} not found")
                return

            (
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
            ) = result

        print("CTM Details:")
        print(f"  ID: {ctm_id}")
        print(f"  Centroid: {centroid_label} ({centroid_id})")
        print(f"  Class: {centroid_class}")
        if primary_theater:
            print(f"  Theater: {primary_theater}")
        print(f"  Track: {track}")
        print(f"  Month: {month.strftime('%Y-%m')}")
        print(f"  Title Count: {title_count}")
        print(f"  Events in Digest: {len(events_digest) if events_digest else 0}")

        if not events_digest:
            print("\nNo events digest found. Run Phase 4.1 first.")
            return

        print("\nEvents Digest:")
        for i, event in enumerate(events_digest, 1):
            print(f"\n  {i}. {event['date']}: {event['summary']}")

        # Extract track focus
        track_focus = None
        if track_focus_jsonb and centroid_class == "geo":
            try:
                track_focus_map = (
                    json.loads(track_focus_jsonb)
                    if isinstance(track_focus_jsonb, str)
                    else track_focus_jsonb
                )
                track_focus = track_focus_map.get(track)
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        print("\nFocus Lines:")
        print(f"  Centroid: {centroid_focus}")
        if track_focus:
            print(f"  Track: {track_focus}")

        print("\nGenerating summary...")

        # Generate summary
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
        print(f"\nGenerated Summary ({word_count} words):")
        print("=" * 80)
        print(summary)
        print("=" * 80)

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

        print("\nUpdated CTM with summary text")

    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ctm_id = sys.argv[1]
    else:
        ctm_id = "114979ac-c9b6-4979-829f-1f5290989a12"
    asyncio.run(test_summary_generation(ctm_id))
