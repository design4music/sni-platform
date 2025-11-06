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
    """
    Generate 150-250 word narrative summary from events digest.

    Args:
        centroid_label: Human-readable centroid name
        centroid_class: 'geo' or 'systemic'
        primary_theater: Theater for geo centroids (e.g., 'MIDEAST')
        track: Track category
        month: Month string (YYYY-MM)
        events_digest: List of event dicts

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
        "temperature": 0.5,  # Balanced creativity for narrative flow
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


async def process_ctm_batch(max_ctms=None):
    """Process CTMs that need summary generation"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get CTMs with events_digest but no summary_text
            limit_clause = f"LIMIT {max_ctms}" if max_ctms else ""
            cur.execute(
                f"""
                SELECT c.id, c.centroid_id, c.track, c.month,
                       c.events_digest, c.title_count,
                       cent.label, cent.class, cent.primary_theater
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.events_digest IS NOT NULL
                  AND jsonb_array_length(c.events_digest) > 0
                  AND c.summary_text IS NULL
                  AND c.is_frozen = false
                ORDER BY c.title_count DESC, c.month DESC
                {limit_clause}
            """
            )
            ctms = cur.fetchall()

        print(f"Processing {len(ctms)} CTMs for summary generation...\n")

        processed_count = 0
        error_count = 0

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
        ) in ctms:
            try:
                print(
                    f"Processing CTM: {centroid_label} / {track} / {month.strftime('%Y-%m')}"
                )
                print(f"  {len(events_digest)} events, {title_count} titles")

                # Generate summary using LLM
                summary = await generate_summary(
                    centroid_label,
                    centroid_class,
                    primary_theater,
                    track,
                    month.strftime("%Y-%m"),
                    events_digest,
                )

                word_count = len(summary.split())
                print(f"  ✓ Generated summary ({word_count} words)")

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

                processed_count += 1

            except Exception as e:
                print(f"  ✗ Error processing CTM {ctm_id}: {e}")
                error_count += 1
                conn.rollback()
                continue

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total CTMs:          {len(ctms)}")
        print(f"Successfully processed: {processed_count}")
        print(f"Errors:              {error_count}")

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
