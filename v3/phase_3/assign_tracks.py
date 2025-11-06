"""
Phase 3: Track Assignment with LLM

Assigns tracks to titles that have been assigned centroids in Phase 2.
Creates/updates CTM records and links titles to their CTM.

Primary centroid logic (from Phase 2 centroid_ids array):
1. One or more matching geo-centroids (e.g., Israel and Palestine) - use first as primary
2. If none, matching systemic centroid (e.g., "Climate") - use as primary
3. If none and is_macro, matching superpower centroid (US, CN, RU, EU) - use first as primary
4. If multiple superpowers, add to each - use first as primary
"""

import asyncio
import sys
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

# Valid tracks
TRACKS = [
    "military",
    "diplomacy",
    "economic",
    "tech_cyber",
    "humanitarian",
    "information_media",
    "legal_regulatory",
]


async def get_track_from_llm(title_text: str) -> str:
    """
    Use Deepseek to assign a track to a title.
    Returns one of the 7 valid tracks.
    """
    system_prompt = """You are a news classifier. Assign this news title to exactly ONE track from this list:

1. military - Armed forces, weapons, combat, defense systems, military operations
2. diplomacy - International relations, treaties, summits, diplomatic visits, negotiations
3. economic - Trade, sanctions, markets, finance, business, economic policy
4. tech_cyber - Technology, cybersecurity, digital infrastructure, tech policy
5. humanitarian - Refugees, aid, disasters, human rights, health crises
6. information_media - Propaganda, disinformation, media control, information warfare
7. legal_regulatory - Laws, regulations, court decisions, legal frameworks

Respond with ONLY the track name (one word), nothing else."""

    user_prompt = f'Title: "{title_text}"'

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
        "temperature": 0,
        "max_tokens": 20,
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
        track = data["choices"][0]["message"]["content"].strip().lower()

    # Validate track
    if track not in TRACKS:
        # Fallback to diplomacy if LLM returns invalid track
        return "diplomacy"

    return track


def get_or_create_ctm(conn, centroid_id: str, track: str, month_date: str) -> str:
    """
    Get existing CTM or create new one.
    Returns CTM id.
    """
    with conn.cursor() as cur:
        # Try to find existing CTM
        cur.execute(
            """
            SELECT id
            FROM ctm
            WHERE centroid_id = %s
              AND track = %s
              AND month = %s
        """,
            (centroid_id, track, month_date),
        )
        result = cur.fetchone()

        if result:
            return result[0]

        # Create new CTM
        cur.execute(
            """
            INSERT INTO ctm (centroid_id, track, month, title_count)
            VALUES (%s, %s, %s, 0)
            RETURNING id
        """,
            (centroid_id, track, month_date),
        )
        ctm_id = cur.fetchone()[0]
        conn.commit()

        return ctm_id


async def process_batch(max_titles=None):
    """Process titles that have centroids but no track assignment"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get titles with centroids but no track
            limit_clause = f"LIMIT {max_titles}" if max_titles else ""
            cur.execute(
                f"""
                SELECT id, title_display, centroid_ids, pubdate_utc
                FROM titles_v3
                WHERE processing_status = 'assigned'
                  AND centroid_ids IS NOT NULL
                  AND track IS NULL
                ORDER BY pubdate_utc DESC
                {limit_clause}
            """
            )
            titles = cur.fetchall()

        print(f"Processing {len(titles)} titles for track assignment...")

        assigned_count = 0
        error_count = 0

        for title_id, title_text, centroid_ids, pubdate in titles:
            try:
                # Get track from LLM
                track = await get_track_from_llm(title_text)

                # Get month (first day of month)
                month_date = pubdate.replace(day=1).date()

                # Create CTM for each centroid and collect CTM IDs
                ctm_ids = []
                for centroid_id in centroid_ids:
                    ctm_id = get_or_create_ctm(conn, centroid_id, track, month_date)
                    ctm_ids.append(ctm_id)

                    # Increment title count for this CTM
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE ctm
                            SET title_count = title_count + 1,
                                updated_at = NOW()
                            WHERE id = %s
                        """,
                            (ctm_id,),
                        )

                # Update title with track and all CTM IDs (many-to-many)
                # centroid_ids already set by Phase 2, just add track and ctm_ids
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE titles_v3
                        SET track = %s,
                            ctm_ids = %s::uuid[],
                            updated_at = NOW()
                        WHERE id = %s
                    """,
                        (track, ctm_ids, title_id),
                    )

                conn.commit()
                assigned_count += 1

                if assigned_count % 10 == 0:
                    print(f"  Processed {assigned_count}/{len(titles)}...")

            except Exception as e:
                print(f"Error processing title {title_id}: {e}")
                error_count += 1
                conn.rollback()
                continue

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total processed:     {len(titles)}")
        print(f"Successfully assigned: {assigned_count}")
        print(f"Errors:              {error_count}")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 3: Assign tracks and create CTMs"
    )
    parser.add_argument(
        "--max-titles", type=int, help="Maximum number of titles to process"
    )

    args = parser.parse_args()

    asyncio.run(process_batch(max_titles=args.max_titles))
