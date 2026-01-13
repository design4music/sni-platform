"""
Reprocess titles that were blocked_llm with the improved gating prompt.

This script:
1. Fetches all titles with processing_status = 'blocked_llm'
2. Re-runs the improved LLM gating on them
3. For titles now marked as strategic:
   - Updates status to 'pending'
   - Assigns tracks
   - Creates CTMs and title_assignments

Usage:
    python v3/phase_3/reprocess_blocked_llm.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config
from v3.phase_3.assign_tracks_batched import (assign_tracks_batch,
                                              gate_centroid_batch,
                                              get_track_config_for_centroids)


async def reprocess_blocked_titles():
    """Reprocess all blocked_llm titles with improved gating."""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Get all blocked_llm titles grouped by centroid
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    t.id,
                    t.title_display,
                    t.centroid_ids,
                    t.pubdate_utc,
                    unnest(t.centroid_ids) as centroid_id
                FROM titles_v3 t
                WHERE processing_status = 'blocked_llm'
                ORDER BY centroid_id, pubdate_utc DESC
            """
            )
            all_titles = cur.fetchall()

        print(f"Found {len(all_titles)} blocked_llm titles to reprocess")

        if not all_titles:
            print("No titles to reprocess")
            return

        # Group by centroid
        from collections import defaultdict

        centroid_titles = defaultdict(list)

        for (
            title_id,
            title_display,
            centroid_ids,
            pubdate_utc,
            centroid_id,
        ) in all_titles:
            centroid_titles[centroid_id].append(
                (title_id, title_display, centroid_ids, pubdate_utc)
            )

        print(f"Grouped into {len(centroid_titles)} centroids")

        total_rescued = 0
        total_still_rejected = 0

        # Process each centroid
        for centroid_id, titles in centroid_titles.items():
            print(f"\n{'='*60}")
            print(f"Processing {centroid_id}: {len(titles)} titles")

            # Get track config for this centroid
            try:
                track_config = get_track_config_for_centroids(conn, [centroid_id])
            except Exception as e:
                print(f"  WARNING: No track config found ({e}), skipping")
                continue

            if not track_config:
                print("  WARNING: No track config found, skipping")
                continue

            # Process in batches of 50
            batch_size = 50
            centroid_rescued = 0

            for batch_start in range(0, len(titles), batch_size):
                batch_end = min(batch_start + batch_size, len(titles))
                titles_batch = titles[batch_start:batch_end]

                print(
                    f"  Batch {batch_start // batch_size + 1}: {len(titles_batch)} titles"
                )

                try:
                    # Re-run gating with improved prompt
                    gating_results = await gate_centroid_batch(
                        centroid_id, track_config, titles_batch
                    )

                    # Separate strategic vs rejected
                    strategic_titles = []
                    still_rejected_ids = []

                    for title_data in titles_batch:
                        title_id = title_data[0]
                        if gating_results.get(title_id) == "strategic":
                            strategic_titles.append(title_data)
                        else:
                            still_rejected_ids.append(title_id)

                    print(
                        f"    Rescued: {len(strategic_titles)}, Still rejected: {len(still_rejected_ids)}"
                    )

                    centroid_rescued += len(strategic_titles)
                    total_still_rejected += len(still_rejected_ids)

                    # Process rescued titles
                    if strategic_titles:
                        # Get month for prompt context
                        first_pubdate = strategic_titles[0][3]
                        month_str = first_pubdate.strftime("%Y-%m")
                        month_date = first_pubdate.replace(day=1).date()

                        # Assign tracks
                        track_assignments = await assign_tracks_batch(
                            centroid_id, track_config, strategic_titles, month_str
                        )

                        print(f"    Assigned {len(track_assignments)} tracks")

                        # Update titles and create CTMs
                        for (
                            title_id,
                            title_display,
                            centroid_ids,
                            pubdate,
                        ) in strategic_titles:
                            track = track_assignments.get(title_id, "unassigned")

                            if track == "unassigned":
                                continue

                            try:
                                # Update title status to 'assigned'
                                with conn.cursor() as cur:
                                    cur.execute(
                                        """
                                        UPDATE titles_v3
                                        SET processing_status = 'assigned',
                                            updated_at = NOW()
                                        WHERE id = %s
                                    """,
                                        (title_id,),
                                    )

                                # Get or create CTM
                                with conn.cursor() as cur:
                                    cur.execute(
                                        """
                                        SELECT id, title_count
                                        FROM ctm
                                        WHERE centroid_id = %s
                                          AND track = %s
                                          AND month = %s
                                    """,
                                        (centroid_id, track, month_date),
                                    )

                                    ctm_result = cur.fetchone()

                                    if ctm_result:
                                        ctm_id = ctm_result[0]
                                        new_count = ctm_result[1] + 1

                                        cur.execute(
                                            """
                                            UPDATE ctm
                                            SET title_count = %s,
                                                updated_at = NOW()
                                            WHERE id = %s
                                        """,
                                            (new_count, ctm_id),
                                        )
                                    else:
                                        cur.execute(
                                            """
                                            INSERT INTO ctm (
                                                centroid_id, track, month,
                                                title_count, events_digest, is_frozen
                                            )
                                            VALUES (%s, %s, %s, 1, '[]'::jsonb, false)
                                            RETURNING id
                                        """,
                                            (centroid_id, track, month_date),
                                        )
                                        ctm_id = cur.fetchone()[0]

                                # Create title_assignment
                                with conn.cursor() as cur:
                                    cur.execute(
                                        """
                                        INSERT INTO title_assignments (
                                            title_id, centroid_id, track, ctm_id
                                        )
                                        VALUES (%s, %s, %s, %s)
                                        ON CONFLICT (title_id, centroid_id) DO NOTHING
                                    """,
                                        (title_id, centroid_id, track, ctm_id),
                                    )

                                conn.commit()

                            except Exception as e:
                                print(f"    Error processing {title_display[:50]}: {e}")
                                conn.rollback()
                                continue

                except Exception as e:
                    print(f"    Error in batch: {e}")
                    continue

            total_rescued += centroid_rescued
            print(f"  Centroid total rescued: {centroid_rescued}")

        print(f"\n{'='*60}")
        print("REPROCESSING COMPLETE")
        print(f"Total rescued: {total_rescued}")
        print(f"Still rejected: {total_still_rejected}")
        if (total_rescued + total_still_rejected) > 0:
            print(
                f"Success rate: {total_rescued / (total_rescued + total_still_rejected) * 100:.1f}%"
            )
        else:
            print("Success rate: N/A (no titles processed)")

    finally:
        conn.close()


if __name__ == "__main__":
    print("Reprocessing blocked_llm titles with improved gating prompt...")
    print("This will rescue strategic content that was wrongly rejected.\n")

    asyncio.run(reprocess_blocked_titles())
