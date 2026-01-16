"""
Phase 3: Track Assignment with Dynamic Track Configs

Assigns tracks to titles using centroid-specific track configurations.
Creates/updates CTM records and links titles to their CTM.

Track Resolution Logic:
1. Get title's centroid_ids from Phase 2
2. Determine primary centroid (systemic > theater > macro)
3. Load track config for primary centroid (or use default)
4. Use centroid-specific prompt and track list for LLM classification
5. Create CTM (centroid, track, month) and link title
"""

import asyncio
import os
import sys
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Ensure .env is loaded from project root
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

from core.config import config  # noqa: E402


def get_track_config_for_centroids(conn, centroid_ids: list) -> dict:
    """
    Get track configuration for a list of centroids.
    Prioritizes: systemic > theater > macro
    Returns track config (tracks, prompt, centroid metadata)
    """
    if not centroid_ids:
        raise ValueError("No centroid_ids provided")

    with conn.cursor() as cur:
        # Get all centroids with their configs, ordered by class priority
        cur.execute(
            """
            SELECT
                c.id,
                c.label,
                c.class,
                c.primary_theater,
                tc.tracks,
                tc.llm_prompt
            FROM centroids_v3 c
            LEFT JOIN track_configs tc ON c.track_config_id = tc.id
            WHERE c.id = ANY(%s)
            ORDER BY
                CASE c.class
                    WHEN 'systemic' THEN 1
                    WHEN 'theater' THEN 2
                    WHEN 'macro' THEN 3
                END,
                c.label
        """,
            (centroid_ids,),
        )

        rows = cur.fetchall()

        if not rows:
            raise ValueError(f"No centroids found for IDs: {centroid_ids}")

        # First centroid with custom config wins
        for row in rows:
            centroid_id, label, cls, theater, tracks, prompt = row
            if tracks is not None and prompt is not None:
                # Has custom track config
                return {
                    "centroid_id": centroid_id,
                    "centroid_label": label,
                    "centroid_class": cls,
                    "primary_theater": theater or "N/A",
                    "tracks": tracks,
                    "prompt": prompt,
                }

        # No custom configs found, use default
        cur.execute(
            """
            SELECT tracks, llm_prompt
            FROM track_configs
            WHERE is_default = TRUE
        """
        )
        default_row = cur.fetchone()

        if not default_row:
            raise ValueError("No default track config found in database")

        # Use first centroid's metadata with default config
        first = rows[0]
        return {
            "centroid_id": first[0],
            "centroid_label": first[1],
            "centroid_class": first[2],
            "primary_theater": first[3] or "N/A",
            "tracks": default_row[0],
            "prompt": default_row[1],
        }


async def get_track_from_llm(title_text: str, track_config: dict, month: str) -> str:
    """
    Use Deepseek to assign a track to a title using dynamic track config.
    Returns one of the valid tracks for this centroid.
    """
    # Format prompt with context
    prompt = track_config["prompt"].format(
        centroid_label=track_config["centroid_label"],
        primary_theater=track_config["primary_theater"],
        month=month,
    )

    user_prompt = f'Title: "{title_text}"'

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 30,
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

    # Validate track against centroid-specific track list
    valid_tracks = [t.lower() for t in track_config["tracks"]]
    if track not in valid_tracks:
        # Fallback to first track if LLM returns invalid track
        print(
            f"  WARNING: LLM returned invalid track '{track}', using '{track_config['tracks'][0]}'"
        )
        return track_config["tracks"][0]

    return track


def get_or_create_ctm(conn, centroid_id: str, track: str, month: str) -> str:
    """
    Get existing CTM or create new one.
    CTM uniqueness: (centroid_id, track, month)
    Returns CTM id.

    Note: month format is 'YYYY-MM-DD' (first day of month)
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
            (centroid_id, track, month),
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
            (centroid_id, track, month),
        )
        ctm_id = cur.fetchone()[0]
        conn.commit()

        return ctm_id


async def process_single_title(title_data):
    """Process a single title (for concurrent execution)"""
    title_id, title_text, centroid_ids, pubdate = title_data

    # Create new connection for this title (thread-safe)
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Get track config for this title's centroids
        track_config = get_track_config_for_centroids(conn, centroid_ids)

        # Format month for prompt context and CTM
        month_str = pubdate.strftime("%Y-%m")
        month_date = pubdate.replace(day=1).date()

        # Get track from LLM using centroid-specific config
        track = await get_track_from_llm(title_text, track_config, month_str)

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
        return (title_id, True, None)

    except Exception as e:
        conn.rollback()
        return (title_id, False, str(e))
    finally:
        conn.close()


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
                  AND id NOT IN (SELECT title_id FROM title_assignments)
                ORDER BY pubdate_utc DESC
                {limit_clause}
            """
            )
            titles = cur.fetchall()

        print("\nPhase 3: Track Assignment")
        print("=" * 60)
        print(
            f"Processing {len(titles)} titles with concurrency={config.v3_p3_concurrency}..."
        )

        assigned_count = 0
        error_count = 0

        # Process titles concurrently in batches
        concurrency = config.v3_p3_concurrency
        for i in range(0, len(titles), concurrency):
            batch = titles[i : i + concurrency]

            # Process batch concurrently
            tasks = [process_single_title(title_data) for title_data in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count results
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    print(f"  ERROR: {result}")
                else:
                    title_id, success, error_msg = result
                    if success:
                        assigned_count += 1
                    else:
                        error_count += 1
                        print(f"  ERROR processing {title_id}: {error_msg}")

            # Progress update
            print(f"  Processed {min(i + concurrency, len(titles))}/{len(titles)}...")

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total processed:       {len(titles)}")
        print(f"Successfully assigned: {assigned_count}")
        print(f"Errors:                {error_count}")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 3: Assign tracks using dynamic track configs"
    )
    parser.add_argument(
        "--max-titles", type=int, help="Maximum number of titles to process"
    )

    args = parser.parse_args()

    asyncio.run(process_batch(max_titles=args.max_titles))
