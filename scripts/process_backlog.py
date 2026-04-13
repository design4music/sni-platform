"""One-shot backlog processor: runs all pipeline phases sequentially until queues are clear."""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import MAX_API_ERRORS, config


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def count_queue(query, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()[0]
    finally:
        conn.close()


def print_queues():
    labels = count_queue(
        "SELECT COUNT(*) FROM titles_v3 t WHERE t.processing_status = 'assigned' "
        "AND t.centroid_ids IS NOT NULL "
        "AND (t.api_error_count IS NULL OR t.api_error_count < %s) "
        "AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id)",
        (MAX_API_ERRORS,),
    )
    tracks = count_queue(
        "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'assigned' "
        "AND centroid_ids IS NOT NULL "
        "AND id NOT IN (SELECT title_id FROM title_assignments)"
    )
    clustering = count_queue(
        "SELECT COUNT(*) FROM ctm WHERE title_count >= 3 AND is_frozen = false "
        "AND (title_count_at_clustering IS NULL OR title_count > title_count_at_clustering)"
    )
    summaries = count_queue(
        "SELECT COUNT(*) FROM events_v3 e JOIN ctm c ON c.id = e.ctm_id "
        "WHERE c.is_frozen = false AND (e.title IS NULL OR e.summary LIKE 'Topic:%%')"
    )
    print("\n--- Queue Status ---")
    print("  Labels (3.1):     %d" % labels)
    print("  Tracks (3.3):     %d" % tracks)
    print("  Clustering (4):   %d" % clustering)
    print("  Summaries (4.5a): %d" % summaries)
    return labels, tracks, clustering, summaries


async def main():
    start = time.time()
    print("=" * 60)
    print("BACKLOG PROCESSOR - started at %s" % time.strftime("%H:%M:%S"))
    print("=" * 60)

    print_queues()

    # Phase 3.1: Label extraction (500/run until done)
    from pipeline.phase_3_1.extract_labels import process_titles as phase31_extract
    from pipeline.phase_3_2.backfill_entity_centroids import (
        backfill_entity_centroids as phase32_backfill,
    )

    run = 0
    stall_count = 0
    prev_remaining = None
    while True:
        remaining = count_queue(
            "SELECT COUNT(*) FROM titles_v3 t WHERE t.processing_status = 'assigned' "
            "AND t.centroid_ids IS NOT NULL "
            "AND (t.api_error_count IS NULL OR t.api_error_count < %s) "
            "AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id)",
            (MAX_API_ERRORS,),
        )
        if remaining == 0:
            break
        # Stall detection: if remaining hasn't decreased in 3 consecutive runs, abort phase
        if prev_remaining is not None and remaining >= prev_remaining:
            stall_count += 1
            if stall_count >= 3:
                print(
                    "[3.1] STALLED - remaining stuck at %d after %d runs, moving on"
                    % (remaining, run),
                    flush=True,
                )
                break
        else:
            stall_count = 0
        prev_remaining = remaining
        run += 1
        print("\n[3.1] Run %d - %d titles remaining..." % (run, remaining), flush=True)
        t0 = time.time()
        result = phase31_extract(max_titles=500, batch_size=25, concurrency=5)
        written = result.get("written", 0) if isinstance(result, dict) else 0
        print(
            "[3.1] Run %d done in %.0fs (wrote %d)" % (run, time.time() - t0, written),
            flush=True,
        )

    # Phase 3.2: Entity centroid backfill
    print("\n[3.2] Entity centroid backfill...", flush=True)
    phase32_backfill(batch_size=500)

    print_queues()

    # Phase 3.3: Mechanical track assignment from sector labels (ELO v3.0)
    # Rejection happens at Phase 3.1 via NON_STRATEGIC sector; there is no LLM gate here.
    from pipeline.phase_3_3.assign_tracks_mechanical import (
        process_batch as phase33_process,
    )

    run = 0
    stall_count = 0
    prev_remaining = None
    while True:
        remaining = count_queue(
            "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'assigned' "
            "AND centroid_ids IS NOT NULL "
            "AND id NOT IN (SELECT title_id FROM title_assignments)"
        )
        if remaining == 0:
            break
        if prev_remaining is not None and remaining >= prev_remaining:
            stall_count += 1
            if stall_count >= 3:
                print(
                    "[3.3] STALLED - remaining stuck at %d after %d runs, moving on"
                    % (remaining, run),
                    flush=True,
                )
                break
        else:
            stall_count = 0
        prev_remaining = remaining
        run += 1
        print("\n[3.3] Run %d - %d titles remaining..." % (run, remaining), flush=True)
        t0 = time.time()
        await phase33_process(max_titles=500)
        print("[3.3] Run %d done in %.0fs" % (run, time.time() - t0), flush=True)

    print_queues()

    # Phase 4: Event clustering
    from pipeline.phase_4.incremental_clustering import process_ctm_for_daemon

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, centroid_id, track FROM ctm "
            "WHERE title_count >= 3 AND is_frozen = false "
            "AND (title_count_at_clustering IS NULL OR title_count > title_count_at_clustering) "
            "ORDER BY title_count DESC"
        )
        ctms = cur.fetchall()
        print("\n[4] Clustering %d CTMs..." % len(ctms), flush=True)
        for i, (ctm_id, centroid_id, track) in enumerate(ctms):
            process_ctm_for_daemon(conn, ctm_id, centroid_id, track)
            cur.execute(
                "UPDATE ctm SET title_count_at_clustering = title_count WHERE id = %s",
                (ctm_id,),
            )
            conn.commit()
            if (i + 1) % 25 == 0:
                print("[4] %d/%d CTMs clustered" % (i + 1, len(ctms)), flush=True)
        print("[4] Clustering done (%d CTMs)" % len(ctms), flush=True)
    finally:
        conn.close()

    print_queues()

    # Phase 4.1: Topic aggregation
    from pipeline.phase_4.consolidate_topics import process_ctm as phase41_aggregate

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, centroid_id, track, title_count FROM ctm "
            "WHERE title_count >= 3 AND is_frozen = false "
            "AND EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = ctm.id) "
            "AND (last_aggregated_at IS NULL OR title_count > COALESCE(title_count_at_aggregation, 0)) "
            "ORDER BY title_count DESC LIMIT 50"
        )
        ctms = cur.fetchall()
        print("\n[4.1] Aggregating %d CTMs..." % len(ctms), flush=True)
        for ctm_id, centroid_id, track, tc in ctms:
            try:
                print("  %s / %s (%d titles)" % (centroid_id, track, tc), flush=True)
                phase41_aggregate(ctm_id=ctm_id, dry_run=False)
                cur.execute(
                    "UPDATE ctm SET last_aggregated_at = NOW(), title_count_at_aggregation = title_count WHERE id = %s",
                    (ctm_id,),
                )
                conn.commit()
            except Exception as e:
                print("  ERROR: %s" % e, flush=True)
                conn.rollback()
        print("[4.1] Aggregation done", flush=True)
    finally:
        conn.close()

    print_queues()

    # Phase 4.5a: Event summaries
    from pipeline.phase_4.generate_event_summaries_4_5a import (
        process_events as phase45a,
    )

    print("\n[4.5a] Generating event summaries (up to 500)...", flush=True)
    await phase45a(max_events=500, force_regenerate=False)
    print("[4.5a] Event summaries done", flush=True)

    # Phase 4.5b: CTM summaries
    from pipeline.phase_4.generate_summaries_4_5 import process_ctm_batch as phase45b

    print("\n[4.5b] Generating CTM summaries (up to 50)...", flush=True)
    await phase45b(max_ctms=50)
    print("[4.5b] CTM summaries done", flush=True)

    print_queues()

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print("BACKLOG PROCESSOR COMPLETE - %.0f minutes total" % (elapsed / 60))
    print("=" * 60, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
