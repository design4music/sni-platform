"""
Phase 4 Month-End Finalization

Processes ALL CTMs before freezing them, regardless of title count.
This ensures complete historical record even for low-volume CTMs.

Run this script at the end of each month before setting is_frozen=true.
"""

import asyncio
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import config
from v3.phase_4.generate_events_digest import extract_events_from_titles
from v3.phase_4.generate_summaries import generate_summary


async def finalize_month(target_month: str = None):
    """
    Process all CTMs for a specific month before freezing.

    Args:
        target_month: Month to finalize in YYYY-MM format (e.g., "2026-01")
                     If None, processes all unfrozen CTMs
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # Get all unfrozen CTMs (regardless of title count)
        with conn.cursor() as cur:
            if target_month:
                cur.execute(
                    """
                    SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                           cent.label, cent.class, cent.primary_theater
                    FROM ctm c
                    JOIN centroids_v3 cent ON c.centroid_id = cent.id
                    WHERE c.is_frozen = false
                      AND TO_CHAR(c.month, 'YYYY-MM') = %s
                    ORDER BY c.title_count DESC
                """,
                    (target_month,),
                )
            else:
                cur.execute(
                    """
                    SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                           cent.label, cent.class, cent.primary_theater
                    FROM ctm c
                    JOIN centroids_v3 cent ON c.centroid_id = cent.id
                    WHERE c.is_frozen = false
                    ORDER BY c.month, c.title_count DESC
                """
                )

            ctms = cur.fetchall()

        print("=" * 80)
        print("PHASE 4 MONTH-END FINALIZATION")
        print("=" * 80)
        print(f"\nTarget month: {target_month or 'All unfrozen CTMs'}")
        print(f"Total CTMs to finalize: {len(ctms)}")
        print()

        # Statistics
        by_title_count = {}
        for row in ctms:
            count = row[4]
            if count == 0:
                bracket = "0"
            elif count < 10:
                bracket = "1-9"
            elif count < 20:
                bracket = "10-19"
            elif count < 50:
                bracket = "20-49"
            elif count < 100:
                bracket = "50-99"
            else:
                bracket = "100+"
            by_title_count[bracket] = by_title_count.get(bracket, 0) + 1

        print("CTMs by title count:")
        for bracket in ["0", "1-9", "10-19", "20-49", "50-99", "100+"]:
            if bracket in by_title_count:
                print(f"  {bracket:8s}: {by_title_count[bracket]:3d} CTMs")
        print()

        processed = 0
        skipped = 0
        errors = 0

        for (
            ctm_id,
            centroid_id,
            track,
            month,
            title_count,
            centroid_label,
            centroid_class,
            primary_theater,
        ) in ctms:
            try:
                print(
                    f"[{processed + skipped + errors + 1}/{len(ctms)}] {centroid_label} / {track} ({title_count} titles)"
                )

                # Fetch titles
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT t.id, t.title_display, t.pubdate_utc
                        FROM title_assignments ta
                        JOIN titles_v3 t ON ta.title_id = t.id
                        WHERE ta.ctm_id = %s
                        ORDER BY t.pubdate_utc ASC
                    """,
                        (ctm_id,),
                    )
                    titles = cur.fetchall()

                if not titles:
                    print("  Skipped: No titles found")
                    skipped += 1
                    continue

                # Phase 4.1: Extract events
                events = await extract_events_from_titles(
                    centroid_label, track, month.strftime("%Y-%m"), titles
                )

                if events:
                    # Update events digest
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE ctm
                            SET events_digest = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """,
                            (Json(events), ctm_id),
                        )
                    conn.commit()

                    # Phase 4.2: Generate summary
                    summary = await generate_summary(
                        centroid_label,
                        centroid_class,
                        primary_theater,
                        track,
                        month.strftime("%Y-%m"),
                        events,
                    )

                    if summary:
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

                        print(f"  OK: {len(events)} events, summary generated")
                        processed += 1
                    else:
                        print(f"  Partial: {len(events)} events, no summary")
                        processed += 1
                else:
                    print("  Skipped: No events extracted")
                    skipped += 1

            except Exception as e:
                print(f"  ERROR: {e}")
                errors += 1
                conn.rollback()
                continue

        print()
        print("=" * 80)
        print("FINALIZATION COMPLETE")
        print("=" * 80)
        print(f"Successfully processed: {processed}")
        print(f"Skipped (no titles/events): {skipped}")
        print(f"Errors: {errors}")
        print()

        if target_month and errors == 0:
            print(f"Ready to freeze month {target_month}")
            print(
                "Run: UPDATE ctm SET is_frozen = true WHERE TO_CHAR(month, 'YYYY-MM') = '{target_month}'"
            )

    finally:
        conn.close()


if __name__ == "__main__":
    # Get target month from command line or use None for all unfrozen
    target_month = sys.argv[1] if len(sys.argv) > 1 else None

    if target_month:
        print(f"Finalizing month: {target_month}")
    else:
        print("Finalizing all unfrozen CTMs")

    asyncio.run(finalize_month(target_month))
