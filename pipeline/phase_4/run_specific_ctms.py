"""Run Phase 4 on specific CTM IDs"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psycopg2.extras import Json

from pipeline.phase_4.generate_events_digest import extract_events_from_titles
from pipeline.phase_4.generate_summaries import generate_summary
from pipeline.taxonomy_tools.common import get_db_connection

CTM_IDS = [
    "349d1eab-1490-467f-868d-350f4f5fa172",  # AMERICAS-USA / geo_politics / 578 titles
]


async def process_ctm_phase_4_1(ctm_id: str):
    """Run Phase 4.1 (events digest) on a single CTM"""
    conn = get_db_connection()

    try:
        # Fetch CTM details
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.centroid_id, c.track, c.month, c.title_count,
                       cent.label
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

            ctm_id, centroid_id, track, month, title_count, centroid_label = result

        print(
            f"\nProcessing CTM: {centroid_label} / {track} / {month.strftime('%Y-%m')}"
        )
        print(f"  Title count: {title_count}")

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
            print("  No titles found")
            return

        print(f"  Retrieved {len(titles)} titles")

        # Extract events
        events = await extract_events_from_titles(
            centroid_label, track, month.strftime("%Y-%m"), titles
        )

        if events:
            # Update CTM
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

            print(f"  OK: Extracted {len(events)} events")
            return events
        else:
            print("  X: No events extracted")
            return None

    except Exception as e:
        print(f"  X Error: {e}")
        return None
    finally:
        conn.close()


async def process_ctm_phase_4_2(ctm_id: str):
    """Run Phase 4.2 (summary generation) on a single CTM"""
    conn = get_db_connection()

    try:
        # Fetch CTM details with events digest
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

        print(
            f"\nGenerating summary for: {centroid_label} / {track} / {month.strftime('%Y-%m')}"
        )

        if not events_digest or len(events_digest) == 0:
            print("  X: No events digest available")
            return

        print(f"  Events count: {len(events_digest)}")

        # Generate summary
        summary = await generate_summary(
            centroid_label,
            centroid_class,
            primary_theater,
            track,
            month.strftime("%Y-%m"),
            events_digest,
        )

        if summary:
            # Update CTM
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

            print(f"  OK: Generated summary ({len(summary)} chars)")
            print("\n  Summary preview:")
            print(f"  {summary[:200]}...")
            return summary
        else:
            print("  X: No summary generated")
            return None

    except Exception as e:
        print(f"  X Error: {e}")
        return None
    finally:
        conn.close()


async def main():
    print("=" * 80)
    print("PHASE 4: EVENTS DIGEST AND SUMMARY GENERATION")
    print("=" * 80)

    # Phase 4.1: Events Digest
    print("\n--- PHASE 4.1: EVENTS DIGEST GENERATION ---\n")
    for ctm_id in CTM_IDS:
        await process_ctm_phase_4_1(ctm_id)

    # Phase 4.2: Summary Generation
    print("\n--- PHASE 4.2: SUMMARY GENERATION ---\n")
    for ctm_id in CTM_IDS:
        await process_ctm_phase_4_2(ctm_id)

    print("\n" + "=" * 80)
    print("PHASE 4 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
