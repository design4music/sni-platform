"""
Phase 3: Intel Gating + Track Assignment with Centroid Batching

Two-stage processing with full centroid context:
1. Intel Gating: LLM sees all titles for a centroid, rejects non-strategic content
2. Track Assignment: LLM assigns tracks to strategic titles with batch context

Key improvements over single-title processing:
- Pattern detection: LLM can see "15 of 47 titles are sports"
- Context-aware decisions: Better track assignment with full centroid view
- Reduced sport/entertainment dominance
- Block non-strategic content before track assignment
"""

import asyncio
import json
import os
import sys
from collections import defaultdict
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
                tc.llm_track_assignment
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
            SELECT tracks, llm_track_assignment
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


def group_titles_by_all_centroids(titles):
    """
    Group titles by ALL their centroids (not just primary).
    Each title appears in multiple groups if it has multiple centroids.

    Args:
        titles: List of (title_id, title_display, centroid_ids, pubdate)

    Returns:
        dict: {centroid_id: [(title_id, title_display, centroid_ids, pubdate), ...]}
    """
    grouped = defaultdict(list)

    for title_data in titles:
        title_id, title_display, centroid_ids, pubdate = title_data

        # Add title to ALL of its centroid groups
        for centroid_id in centroid_ids:
            grouped[centroid_id].append(title_data)

    return dict(grouped)


async def gate_centroid_batch(
    centroid_id: str, track_config: dict, titles_batch: list
) -> dict:
    """
    Stage 1: Intel Gating

    LLM sees all titles for this centroid batch and identifies which are strategic.

    Args:
        centroid_id: Centroid ID
        track_config: Track configuration with centroid metadata
        titles_batch: List of (title_id, title_display, centroid_ids, pubdate)

    Returns:
        dict: {title_id: "strategic" | "reject"}
    """
    # Build numbered list of titles for LLM
    numbered_titles = []
    title_id_map = {}  # {1: title_id, 2: title_id, ...}

    for idx, (title_id, title_display, centroid_ids, pubdate) in enumerate(
        titles_batch, 1
    ):
        numbered_titles.append(f"{idx}. {title_display}")
        title_id_map[idx] = title_id

    titles_text = "\n".join(numbered_titles)

    # Intel gating prompt
    prompt = f"""You are an intelligence analyst reviewing {len(titles_batch)} news titles for {track_config['centroid_label']}.

TASK: Identify which titles contain strategic intelligence value. Be INCLUSIVE - when in doubt, mark as strategic.

STRATEGIC CONTENT (ACCEPT these):
✓ Government policy, legislation, regulations, executive actions
✓ International relations, diplomacy, summits, bilateral/multilateral talks
✓ Military operations, defense, security matters, terrorism
✓ Economic policy, trade agreements, sanctions, tariffs, major corporate deals
✓ Energy markets, oil/gas, supply disruptions, infrastructure
✓ Political protests, elections, government transitions, coups
✓ Court rulings with policy implications, legal precedents
✓ Strategic resources (water, minerals, food security)
✓ Technology with geopolitical implications (semiconductors, AI, cyber)
✓ Major industrial policy, manufacturing, labor disputes with economic impact

ACCEPT EXAMPLES:
- "Trump encourages Iranian protesters; rights group says 2,000 killed" → political unrest + international relations ✓
- "Oil prices rise on potential Iran supply disruption" → energy markets + geopolitics ✓
- "Supreme Court skeptical of trans athlete ban arguments" → legal policy ✓
- "EU-Mercosur trade pact signals limits of Trump diplomacy" → trade + diplomacy ✓
- "Top Turkish, Iranian diplomats discuss situation" → bilateral diplomacy ✓
- "Trump's Detroit trip puts manufacturing back in focus" → industrial policy ✓

NON-STRATEGIC CONTENT (REJECT these):
✗ Pure sports/entertainment (scores, celebrity gossip, award shows)
✗ Health/wellness tips, recipes, lifestyle advice
✗ Local crime without systemic implications
✗ Human interest stories, feel-good news
✗ Real estate ads, local business openings
✗ Weather forecasts (unless major disaster with economic impact)

REJECT EXAMPLES:
- "How to make mulberry tea for health benefits" → lifestyle advice ✗
- "Local restaurant opens in downtown district" → local business ✗
- "Celebrity couple announces breakup" → entertainment ✗
- "Team wins championship game" → sports result ✗
- "Cheap apartments for rent in city" → real estate ad ✗

Titles:
{titles_text}

Return ONLY valid JSON with title numbers:
{{"strategic": [1,3,5], "reject": [2,4,6]}}

When uncertain, prefer STRATEGIC over reject - we want comprehensive coverage of geopolitical, economic, and policy developments."""

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,  # Increased from 0.0 for more flexible strategic assessment
        "max_tokens": config.v3_p3_max_tokens_gating,
    }

    async with httpx.AsyncClient(timeout=config.v3_p3_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")

        data = response.json()
        llm_response = data["choices"][0]["message"]["content"].strip()

    # Strip markdown code blocks if present
    if llm_response.startswith("```"):
        # Remove ```json or ``` at start and ``` at end
        lines = llm_response.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        llm_response = "\n".join(lines).strip()

    # Parse JSON response
    try:
        result = json.loads(llm_response)
        strategic_nums = result.get("strategic", [])
        reject_nums = result.get("reject", [])

        # Build title_id mapping
        gating_results = {}
        for num in strategic_nums:
            if num in title_id_map:
                gating_results[title_id_map[num]] = "strategic"

        for num in reject_nums:
            if num in title_id_map:
                gating_results[title_id_map[num]] = "reject"

        # Handle any titles not categorized (shouldn't happen, but failsafe)
        for title_id in title_id_map.values():
            if title_id not in gating_results:
                gating_results[title_id] = (
                    "strategic"  # Default to strategic if unclear
                )

        return gating_results

    except json.JSONDecodeError as e:
        print(f"  WARNING: Failed to parse gating JSON: {e}")
        print(f"  LLM response: {llm_response}")
        # Fallback: accept all titles
        return {title_id_map[num]: "strategic" for num in title_id_map}


async def assign_tracks_batch(
    centroid_id: str, track_config: dict, strategic_titles: list, month: str
) -> dict:
    """
    Stage 2: Track Assignment

    LLM sees all strategic titles for this centroid batch and assigns tracks.

    Args:
        centroid_id: Centroid ID
        track_config: Track configuration
        strategic_titles: List of (title_id, title_display, centroid_ids, pubdate)
        month: Month string for context (YYYY-MM)

    Returns:
        dict: {title_id: track_name}
    """
    if not strategic_titles:
        return {}

    # Build numbered list of titles
    numbered_titles = []
    title_id_map = {}

    for idx, (title_id, title_display, centroid_ids, pubdate) in enumerate(
        strategic_titles, 1
    ):
        numbered_titles.append(f"{idx}. {title_display}")
        title_id_map[idx] = title_id

    titles_text = "\n".join(numbered_titles)

    # Track assignment prompt (using existing track config prompt as base)
    tracks_list = "\n".join([f"- {track}" for track in track_config["tracks"]])

    prompt = f"""You are classifying {len(strategic_titles)} strategic news titles for {track_config['centroid_label']}.

Choose the ONE best track for each title based on its dominant theme.

Tracks:
{tracks_list}

Context: {track_config['centroid_label']} | {month}

Titles:
{titles_text}

Return ONLY valid JSON mapping title numbers to tracks:
{{"1": "track_name", "2": "track_name", "3": "track_name"}}"""

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.v3_p3_temperature,
        "max_tokens": config.v3_p3_max_tokens_tracks,
    }

    async with httpx.AsyncClient(timeout=config.v3_p3_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")

        data = response.json()
        llm_response = data["choices"][0]["message"]["content"].strip()

    # Strip markdown code blocks if present
    if llm_response.startswith("```"):
        # Remove ```json or ``` at start and ``` at end
        lines = llm_response.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        llm_response = "\n".join(lines).strip()

    # Parse JSON response
    try:
        result = json.loads(llm_response)

        # Convert string keys to ints, then map to title_ids
        track_assignments = {}
        valid_tracks_lower = [t.lower() for t in track_config["tracks"]]

        for num_str, track in result.items():
            num = int(num_str)
            if num in title_id_map:
                track_lower = track.lower().strip()

                # Validate track
                if track_lower in valid_tracks_lower:
                    track_assignments[title_id_map[num]] = track_lower
                else:
                    # Fallback to first track
                    print(
                        f"  WARNING: Invalid track '{track}' for title {num}, using '{track_config['tracks'][0]}'"
                    )
                    track_assignments[title_id_map[num]] = track_config["tracks"][0]

        # Ensure all titles got a track assignment
        for title_id in title_id_map.values():
            if title_id not in track_assignments:
                print(
                    f"  WARNING: No track for title {title_id}, using '{track_config['tracks'][0]}'"
                )
                track_assignments[title_id] = track_config["tracks"][0]

        return track_assignments

    except (json.JSONDecodeError, ValueError) as e:
        print(f"  WARNING: Failed to parse track JSON: {e}")
        print(f"  LLM response: {llm_response}")
        # Fallback: assign first track to all
        return {title_id_map[num]: track_config["tracks"][0] for num in title_id_map}


def get_or_create_ctm(conn, centroid_id: str, track: str, month_date) -> str:
    """
    Get existing CTM or create new one.
    Returns CTM id.
    """
    with conn.cursor() as cur:
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


async def process_centroid_group(
    centroid_id: str, titles: list, batch_size: int
) -> tuple:
    """
    Process all titles for one centroid in batches.

    Returns:
        (strategic_count, rejected_count, error_count)
    """
    print(f"\nProcessing centroid: {centroid_id}")
    print(f"  Total titles: {len(titles)}")

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Get track config for this specific centroid
        track_config = get_track_config_for_centroids(conn, [centroid_id])

        strategic_total = 0
        rejected_total = 0
        error_total = 0

        # Process in batches of batch_size
        for batch_start in range(0, len(titles), batch_size):
            batch_end = min(batch_start + batch_size, len(titles))
            titles_batch = titles[batch_start:batch_end]

            print(
                f"  Batch {batch_start // batch_size + 1}: Processing {len(titles_batch)} titles..."
            )

            try:
                # Stage 1: Intel Gating
                gating_results = await gate_centroid_batch(
                    centroid_id, track_config, titles_batch
                )

                # Separate strategic vs rejected
                strategic_titles = []
                rejected_title_ids = []

                for title_data in titles_batch:
                    title_id = title_data[0]
                    if gating_results.get(title_id) == "strategic":
                        strategic_titles.append(title_data)
                    else:
                        rejected_title_ids.append(title_id)

                strategic_count = len(strategic_titles)
                rejected_count = len(rejected_title_ids)

                print(
                    f"    Gating: {strategic_count} strategic, {rejected_count} rejected"
                )

                # Update rejected titles
                if rejected_title_ids:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE titles_v3
                            SET processing_status = 'blocked_llm',
                                updated_at = NOW()
                            WHERE id = ANY(%s::uuid[])
                        """,
                            (rejected_title_ids,),
                        )
                    conn.commit()

                # Stage 2: Track Assignment (only for strategic titles)
                if strategic_titles:
                    # Get month for prompt context
                    first_pubdate = strategic_titles[0][3]
                    month_str = first_pubdate.strftime("%Y-%m")
                    month_date = first_pubdate.replace(day=1).date()

                    track_assignments = await assign_tracks_batch(
                        centroid_id, track_config, strategic_titles, month_str
                    )

                    print(f"    Assigned {len(track_assignments)} tracks")

                    # Update titles with tracks and create CTMs
                    title_errors = 0
                    for (
                        title_id,
                        title_display,
                        centroid_ids,
                        pubdate,
                    ) in strategic_titles:
                        if title_id not in track_assignments:
                            print(
                                f"    WARNING: No track assigned for title {title_id}: {title_display[:60]}..."
                            )
                            title_errors += 1
                            continue

                        track = track_assignments[title_id]

                        try:
                            # Create CTM for THIS centroid only
                            ctm_id = get_or_create_ctm(
                                conn, centroid_id, track, month_date
                            )

                            # Increment title count
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

                            # Insert into title_assignments (skip if already exists)
                            with conn.cursor() as cur:
                                cur.execute(
                                    """
                                    INSERT INTO title_assignments (title_id, centroid_id, track, ctm_id)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (title_id, centroid_id, track)
                                    DO NOTHING
                                """,
                                    (title_id, centroid_id, track, ctm_id),
                                )

                            # Commit this title's updates
                            conn.commit()

                        except Exception as title_error:
                            print(
                                f"    ERROR processing title {title_id}: {title_error}"
                            )
                            conn.rollback()
                            title_errors += 1

                    error_total += title_errors

                strategic_total += strategic_count
                rejected_total += rejected_count

            except Exception as e:
                print(f"  ERROR in batch: {e}")
                error_total += len(titles_batch)
                conn.rollback()

        return (strategic_total, rejected_total, error_total)

    finally:
        conn.close()


async def process_batch(max_titles=None):
    """
    Main entry point: Process titles with centroid-batched intel gating and track assignment.
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Load titles needing processing
        # Only process titles not yet in title_assignments to avoid re-processing
        with conn.cursor() as cur:
            limit_clause = f"LIMIT {max_titles}" if max_titles else ""
            cur.execute(
                f"""
                SELECT t.id, t.title_display, t.centroid_ids, t.pubdate_utc
                FROM titles_v3 t
                WHERE t.processing_status = 'assigned'
                  AND t.centroid_ids IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM title_assignments ta
                    WHERE ta.title_id = t.id
                  )
                ORDER BY t.pubdate_utc DESC
                {limit_clause}
            """
            )
            titles = cur.fetchall()

        print("\nPhase 3: Intel Gating + Track Assignment (Centroid-Batched)")
        print("=" * 60)
        print(f"Total titles to process: {len(titles)}")

        if not titles:
            print("No titles to process.")
            return

        # Group by ALL centroids (each title appears in multiple groups)
        grouped = group_titles_by_all_centroids(titles)
        print(f"Grouped into {len(grouped)} centroids")
        print()

        # Process each centroid group
        total_strategic = 0
        total_rejected = 0
        total_errors = 0

        batch_size = config.v3_p3_centroid_batch_size

        for centroid_id, centroid_titles in sorted(grouped.items()):
            strategic, rejected, errors = await process_centroid_group(
                centroid_id, centroid_titles, batch_size
            )

            total_strategic += strategic
            total_rejected += rejected
            total_errors += errors

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Total titles processed:    {len(titles)}")
        print(f"Strategic (assigned):      {total_strategic}")
        print(f"Rejected (blocked_llm):    {total_rejected}")
        print(f"Errors:                    {total_errors}")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 3: Intel Gating + Track Assignment (Centroid-Batched)"
    )
    parser.add_argument(
        "--max-titles",
        type=int,
        help="Maximum titles to process (for testing)",
    )
    args = parser.parse_args()

    asyncio.run(process_batch(max_titles=args.max_titles))
