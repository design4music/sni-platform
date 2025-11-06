"""Test summary generation on a single CTM"""

import asyncio
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

    system_prompt = """You are a strategic intelligence analyst writing monthly summary reports.
Generate a cohesive 150-250 word narrative from the provided events timeline.

Requirements:
- Flow chronologically
- Highlight key developments
- Connect related events
- Provide context for significance
- Maintain journalistic tone
- Focus on strategic implications
- Use present/past tense appropriately
- Write as a single flowing paragraph or 2-3 short paragraphs

Do NOT:
- List events as bullet points
- Include dates in parentheses unless critical
- Use sensational language
- Add speculation beyond events"""

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
        # Get CTM details
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month,
                       c.events_digest, c.title_count,
                       cent.label, cent.class, cent.primary_theater
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

        print("\nGenerating summary...")

        # Generate summary
        summary = await generate_summary(
            centroid_label,
            centroid_class,
            primary_theater,
            track,
            month.strftime("%Y-%m"),
            events_digest,
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
    ctm_id = "114979ac-c9b6-4979-829f-1f5290989a12"
    asyncio.run(test_summary_generation(ctm_id))
