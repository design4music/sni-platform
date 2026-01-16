"""Test to find maximum batch size for Phase 4.1"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.phase_4.generate_events_digest import extract_events_from_titles
from pipeline.taxonomy_tools.common import get_db_connection

CTM_ID = "349d1eab-1490-467f-868d-350f4f5fa172"  # USA geo_politics, 578 titles


async def test_batch_size(batch_size: int):
    """Test Phase 4.1 with a specific batch size"""
    conn = get_db_connection()

    try:
        # Fetch CTM details
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.centroid_id, c.track, c.month,
                       cent.label
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.id = %s
            """,
                (CTM_ID,),
            )

            result = cur.fetchone()
            if not result:
                return False, "CTM not found"

            centroid_id, track, month, centroid_label = result

        # Fetch titles (limited to batch_size)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT t.id, t.title_display, t.pubdate_utc
                FROM title_assignments ta
                JOIN titles_v3 t ON ta.title_id = t.id
                WHERE ta.ctm_id = %s
                ORDER BY t.pubdate_utc ASC
                LIMIT {batch_size}
            """,
                (CTM_ID,),
            )
            titles = cur.fetchall()

        print(f"\nTesting batch size: {batch_size} titles")
        print(f"  Date range: {titles[0][2]} to {titles[-1][2]}")

        import time

        start = time.time()

        try:
            events = await extract_events_from_titles(
                centroid_label, track, month.strftime("%Y-%m"), titles
            )
            elapsed = time.time() - start

            if events:
                print(f"  OK: {len(events)} events in {elapsed:.1f}s")
                print(f"  Compression: {len(titles)} -> {len(events)} ({len(events)/len(titles)*100:.1f}%)")
                return True, elapsed
            else:
                print("  FAIL: No events extracted")
                return False, "No events"

        except Exception as e:
            elapsed = time.time() - start
            error_type = type(e).__name__
            print(f"  FAIL: {error_type} after {elapsed:.1f}s")
            return False, str(e)

    finally:
        conn.close()


async def main():
    print("=" * 80)
    print("BATCH SIZE LIMIT TEST")
    print("=" * 80)
    print("\nTesting with USA geo_politics CTM (578 total titles)")
    print("Finding maximum safe batch size for Phase 4.1")
    print()

    # Test progressively larger batches
    batch_sizes = [100, 150, 200, 250, 300, 350, 400, 450, 500]

    results = []
    max_working = 0

    for size in batch_sizes:
        success, info = await test_batch_size(size)
        results.append((size, success, info))

        if success:
            max_working = size
        else:
            print(f"\n  Breaking point found at {size} titles")
            break

        # Small delay between tests
        await asyncio.sleep(2)

    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print()

    for size, success, info in results:
        status = "OK" if success else "FAIL"
        if success:
            print(f"{size:3d} titles: {status} ({info:.1f}s)")
        else:
            print(f"{size:3d} titles: {status}")

    if max_working > 0:
        print()
        print(f"Maximum working batch size: {max_working} titles")
        print(f"Recommended batch size: {int(max_working * 0.8)} titles (80% of max)")


if __name__ == "__main__":
    asyncio.run(main())
