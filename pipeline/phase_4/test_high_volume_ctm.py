"""Test Phase 4 on high-volume CTM (578 titles)"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from psycopg2.extras import Json

from pipeline.phase_4.generate_events_digest import extract_events_from_titles
from pipeline.phase_4.generate_summaries import generate_summary
from pipeline.taxonomy_tools.common import get_db_connection

CTM_ID = "349d1eab-1490-467f-868d-350f4f5fa172"


async def test_high_volume():
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
                (CTM_ID,),
            )

            result = cur.fetchone()
            if not result:
                print(f"CTM {CTM_ID} not found")
                return

            ctm_id, centroid_id, track, month, title_count, centroid_label = result

        print("=" * 80)
        print("HIGH-VOLUME CTM TEST")
        print("=" * 80)
        print(f"\nCTM: {centroid_label} / {track} / {month.strftime('%Y-%m')}")
        print(f"Title count: {title_count}")
        print()

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
            print("No titles found")
            return

        print(f"Retrieved {len(titles)} titles")
        print(f"Date range: {titles[0][2]} to {titles[-1][2]}")
        print()

        # Show sample of titles
        print("Sample titles (first 10):")
        for i, (tid, text, pubdate) in enumerate(titles[:10]):
            safe_text = text[:80].encode("ascii", "replace").decode("ascii")
            print(f"  [{i}] {pubdate.strftime('%Y-%m-%d')}: {safe_text}")
        print(f"  ... ({len(titles) - 10} more)")
        print()

        # Phase 4.1: Extract events
        print("--- PHASE 4.1: EXTRACTING EVENTS ---")
        print(f"Sending {len(titles)} titles to LLM for deduplication...")
        print()

        import time

        start = time.time()
        events = await extract_events_from_titles(
            centroid_label, track, month.strftime("%Y-%m"), titles
        )
        elapsed = time.time() - start

        if events:
            print(f"OK: Extracted {len(events)} distinct events in {elapsed:.1f}s")
            print(f"Compression ratio: {len(titles)} titles -> {len(events)} events ({len(events)/len(titles)*100:.1f}%)")
            print()

            # Show events
            print("EVENTS EXTRACTED:")
            print("-" * 80)
            for i, event in enumerate(events, 1):
                print(f"\n{i}. {event['date']}")
                summary_safe = event["summary"][:200].encode("ascii", "replace").decode("ascii")
                print(f"   {summary_safe}")
                print(f"   Sources: {len(event['source_title_ids'])} titles")

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
            print()
            print("CTM updated with events digest")

            # Phase 4.2: Generate summary
            print()
            print("--- PHASE 4.2: GENERATING SUMMARY ---")
            print()

            # Fetch centroid details for summary
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT class, primary_theater
                    FROM centroids_v3
                    WHERE id = %s
                """,
                    (centroid_id,),
                )
                centroid_class, primary_theater = cur.fetchone()

            start = time.time()
            summary = await generate_summary(
                centroid_label,
                centroid_class,
                primary_theater,
                track,
                month.strftime("%Y-%m"),
                events,
            )
            elapsed = time.time() - start

            if summary:
                print(f"OK: Generated summary in {elapsed:.1f}s ({len(summary)} chars)")
                print()
                print("SUMMARY:")
                print("-" * 80)
                print(summary)
                print("-" * 80)

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
                print()
                print("CTM updated with summary")
            else:
                print("X: No summary generated")

        else:
            print("X: No events extracted")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(test_high_volume())
