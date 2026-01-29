"""
SNI v3 Pipeline Daemon

Orchestrates the complete v3 pipeline with configurable intervals:
- Phase 1: RSS ingestion (12 hours)
- Phase 2: Centroid matching (5 minutes)
- Phase 3: Track assignment & CTM creation (10 minutes)
- Phase 3.5: Label extraction (10 minutes)
- Phase 3.6: Entity centroid backfill (after 3.5)
- Phase 4: Event clustering (30 minutes)
- Phase 4.1: Topic aggregation - LLM merge/cleanup (after 4)
- Phase 4.5a: Event summaries - readable text per event (after 4.1)
- Phase 4.5: CTM summary generation (1 hour)

Features:
- Sequential execution with configurable intervals
- Graceful shutdown on SIGTERM/SIGINT
- Basic retry logic with exponential backoff
- Log-based monitoring
- Adaptive batch sizing based on queue depth
"""

import asyncio
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from db.backfills.backfill_entity_centroids import (
    backfill_entity_centroids as phase36_backfill,
)

# Import phase modules
from pipeline.phase_1.ingest_feeds import run_ingestion
from pipeline.phase_2.match_centroids import process_batch as phase2_process
from pipeline.phase_3.assign_tracks_batched import process_batch as phase3_process
from pipeline.phase_3_5.extract_labels import process_titles as phase35_extract
from pipeline.phase_4.aggregate_topics import process_ctm as phase41_aggregate
from pipeline.phase_4.generate_event_summaries_4_5a import (
    process_events as phase45a_event_summaries,
)
from pipeline.phase_4.generate_summaries_4_5 import (
    process_ctm_batch as phase45_summaries,
)
from pipeline.phase_4.incremental_clustering import (
    process_ctm_for_daemon,
)


class PipelineDaemon:
    """SNI v3 Pipeline orchestration daemon"""

    def __init__(self):
        self.config = config
        self.running = True
        self.cycle_count = 0

        # Intervals (in seconds)
        self.phase1_interval = 43200  # 12 hours - RSS feeds
        self.phase2_interval = 900  # 15 minutes - Fast matching (low input rate)
        self.phase3_interval = 600  # 10 minutes - LLM track assignment
        self.phase35_interval = 600  # 10 minutes - Label extraction
        self.phase4_interval = 1800  # 30 minutes - Event clustering
        self.phase45a_interval = (
            self.config.v3_p45a_interval
        )  # 15 min - Event summaries
        self.phase45_interval = 3600  # 1 hour - CTM summary generation

        # Last run timestamps
        self.last_run = {
            "phase1": 0,
            "phase2": 0,
            "phase3": 0,
            "phase35": 0,
            "phase4": 0,
            "phase45a": 0,
            "phase45": 0,
        }

        # Batch sizes
        self.phase2_batch_size = 500  # Titles per Phase 2 run
        self.phase3_batch_size = 100  # CTMs per Phase 3 run
        self.phase4_batch_size = 50  # CTMs per Phase 4 run

        # Retry configuration
        self.max_retries = 3
        self.retry_backoff = 2.0  # Exponential backoff multiplier

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        print(f"\nReceived {signal_name}, shutting down gracefully...")
        self.running = False

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )

    def get_queue_stats(self):
        """Get current queue depths for adaptive scheduling"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Phase 2 queue (pending titles)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM titles_v3
                    WHERE processing_status = 'pending'
                """
                )
                pending_titles = cur.fetchone()[0]

                # Phase 3 queue (assigned titles without track assignment)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM titles_v3
                    WHERE processing_status = 'assigned'
                      AND centroid_ids IS NOT NULL
                      AND id NOT IN (SELECT title_id FROM title_assignments)
                """
                )
                titles_need_track = cur.fetchone()[0]

                # Phase 3.5 queue (titles with track but no labels)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM titles_v3 t
                    WHERE EXISTS (SELECT 1 FROM title_assignments ta WHERE ta.title_id = t.id)
                      AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id)
                """
                )
                titles_need_labels = cur.fetchone()[0]

                # Phase 4 cluster queue (CTMs that may need event regeneration)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM ctm c
                    WHERE c.title_count >= 3
                      AND c.is_frozen = false
                """
                )
                ctms_for_clustering = cur.fetchone()[0]

                # Phase 4.5 summary queue: EVENT-DRIVEN regeneration
                # Regenerate if: no summary, OR new events since last summary
                # With 24h minimum cooldown to prevent thrashing
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM ctm c
                    WHERE c.title_count >= %s
                      AND c.is_frozen = false
                      AND EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = c.id)
                      AND (
                          -- Never had a summary
                          c.summary_text IS NULL
                          OR (
                              -- Has new events since last summary AND cooldown passed
                              (SELECT COUNT(*) FROM events_v3 e WHERE e.ctm_id = c.id)
                                  > COALESCE(c.event_count_at_summary, 0)
                              AND (c.last_summary_at IS NULL
                                   OR c.last_summary_at < NOW() - INTERVAL '24 hours')
                          )
                      )
                """,
                    (self.config.v3_p4_min_titles,),
                )
                ctms_need_summary = cur.fetchone()[0]

                return {
                    "pending_titles": pending_titles,
                    "titles_need_track": titles_need_track,
                    "titles_need_labels": titles_need_labels,
                    "ctms_for_clustering": ctms_for_clustering,
                    "ctms_need_summary": ctms_need_summary,
                }
        finally:
            conn.close()

    def should_run_phase(self, phase_name: str) -> bool:
        """Check if enough time has passed since last run"""
        now = time.time()
        last = self.last_run[phase_name]
        interval = getattr(self, f"{phase_name}_interval")

        return (now - last) >= interval

    def monitor_summary_word_counts(self):
        """Monitor summary word counts to detect length creep"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN array_length(string_to_array(summary_text, ' '), 1) > 250 THEN 1 END) as over_250,
                        MAX(array_length(string_to_array(summary_text, ' '), 1)) as max_words,
                        AVG(array_length(string_to_array(summary_text, ' '), 1))::int as avg_words
                    FROM ctm
                    WHERE summary_text IS NOT NULL
                      AND is_frozen = false
                """
                )
                total, over_250, max_words, avg_words = cur.fetchone()

                print("\nSummary Word Count Monitor:")
                print(
                    f"  Total: {total} | Over 250: {over_250} | Max: {max_words} | Avg: {avg_words}"
                )

                if over_250 > 0:
                    pct = (over_250 / total * 100) if total > 0 else 0
                    print(
                        f"  WARNING: {over_250} summaries ({pct:.1f}%) exceed 250-word target"
                    )

        finally:
            conn.close()

    def print_full_statistics(self):
        """Print comprehensive pipeline statistics"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                print("\n" + "=" * 70)
                print("FULL PIPELINE STATISTICS")
                print("=" * 70)

                # Phase 1 Stats: Titles by date
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_titles,
                        COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as last_7_days,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as last_30_days
                    FROM titles_v3
                """
                )
                total_titles, today, last_7, last_30 = cur.fetchone()
                print("\nPHASE 1 - RSS INGESTION:")
                print(f"  Total titles in DB: {total_titles:,}")
                print(f"  Ingested today: {today:,}")
                print(f"  Last 7 days: {last_7:,}")
                print(f"  Last 30 days: {last_30:,}")

                # Phase 2 Stats: Processing status breakdown
                cur.execute(
                    """
                    SELECT
                        processing_status,
                        COUNT(*) as count
                    FROM titles_v3
                    GROUP BY processing_status
                    ORDER BY count DESC
                """
                )
                print("\nPHASE 2 - CENTROID MATCHING:")
                print("  Processing status breakdown:")
                for status, count in cur.fetchall():
                    pct = (count / total_titles * 100) if total_titles > 0 else 0
                    print(f"    {status}: {count:,} ({pct:.1f}%)")

                # Multi-centroid assignment rate
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_matched,
                        COUNT(CASE WHEN array_length(centroid_ids, 1) > 1 THEN 1 END) as multi_centroid
                    FROM titles_v3
                    WHERE centroid_ids IS NOT NULL AND array_length(centroid_ids, 1) > 0
                """
                )
                total_matched, multi = cur.fetchone()
                if total_matched > 0:
                    multi_pct = multi / total_matched * 100
                    print(f"  Multi-centroid assignments: {multi:,} ({multi_pct:.1f}%)")

                # Phase 3 Stats: Track assignments and CTMs
                cur.execute(
                    """
                    SELECT COUNT(DISTINCT title_id) FROM title_assignments
                """
                )
                titles_with_tracks = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT COUNT(*) FROM title_assignments
                """
                )
                total_assignments = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT COUNT(*) FROM ctm
                """
                )
                total_ctms = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT COUNT(*) FROM ctm WHERE title_count > 0
                """
                )
                active_ctms = cur.fetchone()[0]

                print("\nPHASE 3 - TRACK ASSIGNMENT & CTM CREATION:")
                print(f"  Titles with track assignments: {titles_with_tracks:,}")
                print(
                    f"  Total title-centroid-track assignments: {total_assignments:,}"
                )
                print(f"  Total CTMs created: {total_ctms:,}")
                print(f"  Active CTMs (title_count > 0): {active_ctms:,}")

                # Track distribution
                cur.execute(
                    """
                    SELECT track, COUNT(*) as count
                    FROM title_assignments
                    GROUP BY track
                    ORDER BY count DESC
                    LIMIT 10
                """
                )
                print("  Top 10 tracks by assignment count:")
                for track, count in cur.fetchall():
                    print(f"    {track}: {count:,}")

                # Phase 4 Stats: Enrichment
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_active,
                        COUNT(CASE WHEN EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = c.id) THEN 1 END) as with_events,
                        COUNT(CASE WHEN summary_text IS NOT NULL THEN 1 END) as with_summary
                    FROM ctm c
                    WHERE title_count > 0 AND is_frozen = false
                """
                )
                total_active, with_events, with_summary = cur.fetchone()

                print("\nPHASE 4 - CTM ENRICHMENT:")
                print(f"  Active CTMs: {total_active:,}")
                print(
                    f"  With events: {with_events:,} ({with_events/total_active*100:.1f}%)"
                    if total_active > 0
                    else "  With events: 0"
                )
                print(
                    f"  With summary: {with_summary:,} ({with_summary/total_active*100:.1f}%)"
                    if total_active > 0
                    else "  With summary: 0"
                )

                # Summary word count stats
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        MIN(array_length(string_to_array(summary_text, ' '), 1)) as min_words,
                        MAX(array_length(string_to_array(summary_text, ' '), 1)) as max_words,
                        AVG(array_length(string_to_array(summary_text, ' '), 1))::int as avg_words,
                        COUNT(CASE WHEN array_length(string_to_array(summary_text, ' '), 1) > 250 THEN 1 END) as over_250
                    FROM ctm
                    WHERE summary_text IS NOT NULL AND is_frozen = false
                """
                )
                total_sum, min_w, max_w, avg_w, over_250 = cur.fetchone()
                if total_sum and total_sum > 0:
                    print(
                        f"  Summary word counts: Min={min_w} | Avg={avg_w} | Max={max_w}"
                    )
                    print(
                        f"  Over 250 words: {over_250} ({over_250/total_sum*100:.1f}%)"
                    )

                # Centroid coverage
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_centroids,
                        COUNT(CASE WHEN id IN (SELECT DISTINCT centroid_id FROM ctm WHERE title_count > 0) THEN 1 END) as with_ctms
                    FROM centroids_v3
                    WHERE is_active = true
                """
                )
                total_centroids, with_ctms = cur.fetchone()
                print("\nCENTROID COVERAGE:")
                print(f"  Total active centroids: {total_centroids}")
                print(
                    f"  Centroids with active CTMs: {with_ctms} ({with_ctms/total_centroids*100:.1f}%)"
                    if total_centroids > 0
                    else "  Centroids with active CTMs: 0"
                )

                print("=" * 70)

        finally:
            conn.close()

    def run_event_clustering(self):
        """Run event clustering for all active unfrozen CTMs using incremental clustering"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Get all unfrozen CTMs with enough titles
                cur.execute(
                    """
                    SELECT id, centroid_id, track, TO_CHAR(month, 'YYYY-MM') as month
                    FROM ctm
                    WHERE title_count >= 3 AND is_frozen = false
                    ORDER BY month DESC
                    """
                )
                ctms = cur.fetchall()

            print("Processing {} CTMs for incremental clustering...".format(len(ctms)))
            processed = 0
            total_topics = 0
            for ctm_id, centroid_id, track, month in ctms:
                written = process_ctm_for_daemon(conn, ctm_id, centroid_id, track)
                if written > 0:
                    total_topics += written
                    processed += 1

            print("Clustered {} topics across {} CTMs".format(total_topics, processed))

        finally:
            conn.close()

    def run_topic_aggregation(self, max_ctms: int = 10):
        """
        Run topic aggregation (LLM merge/cleanup) for CTMs with NEW content only.

        INCREMENTAL: Only processes CTMs where title_count increased since last
        aggregation, or CTMs that were never aggregated.

        Limits to max_ctms per cycle to avoid blocking the pipeline.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Get CTMs that have NEW content since last aggregation
                # OR have never been aggregated (last_aggregated_at IS NULL)
                cur.execute(
                    """
                    SELECT id, centroid_id, track, title_count
                    FROM ctm
                    WHERE title_count >= 3 AND is_frozen = false
                      AND EXISTS (SELECT 1 FROM events_v3 e WHERE e.ctm_id = ctm.id)
                      AND (
                          last_aggregated_at IS NULL
                          OR title_count > COALESCE(title_count_at_aggregation, 0)
                      )
                    ORDER BY
                        last_aggregated_at NULLS FIRST,
                        title_count DESC
                    LIMIT %s
                    """,
                    (max_ctms,),
                )
                ctms = cur.fetchall()

            if not ctms:
                print("No CTMs need aggregation (all up-to-date)")
                return

            print(
                "Processing {} CTMs with new content (limit {})...".format(
                    len(ctms), max_ctms
                )
            )
            for ctm_id, centroid_id, track, title_count in ctms:
                try:
                    print(
                        "  Aggregating {} / {} ({} titles)...".format(
                            centroid_id, track, title_count
                        )
                    )
                    phase41_aggregate(ctm_id=ctm_id, dry_run=False)

                    # Mark CTM as aggregated with current title count
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE ctm
                            SET last_aggregated_at = NOW(),
                                title_count_at_aggregation = title_count
                            WHERE id = %s
                            """,
                            (ctm_id,),
                        )
                    conn.commit()

                except Exception as e:
                    print("  Aggregation failed for {}: {}".format(ctm_id[:8], e))

        finally:
            conn.close()

    async def run_event_summaries(self, max_events: int = 100):
        """Generate summaries for events that need them"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Count events needing summaries (have "Topic:" or no title)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM events_v3 e
                    JOIN ctm c ON c.id = e.ctm_id
                    WHERE c.is_frozen = false
                      AND (e.title IS NULL OR e.summary LIKE 'Topic:%%')
                    """
                )
                needs_summary = cur.fetchone()[0]

            if needs_summary == 0:
                print("No events need summaries")
                return

            print(
                "Generating summaries for up to {} events ({} need summaries)...".format(
                    max_events, needs_summary
                )
            )
            await phase45a_event_summaries(
                max_events=max_events, force_regenerate=False
            )

        finally:
            conn.close()

    def run_phase_with_retry(self, phase_name: str, phase_func, *args, **kwargs):
        """
        Run a phase with retry logic.

        Args:
            phase_name: Human-readable phase name
            phase_func: Function to execute
            *args, **kwargs: Arguments to pass to phase_func
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"\n{'='*70}")
                print(f"{phase_name} - Attempt {attempt}/{self.max_retries}")
                print(f"{'='*70}")

                start_time = time.time()
                result = phase_func(*args, **kwargs)
                duration = time.time() - start_time

                print(f"{phase_name} completed in {duration:.1f}s")
                return result

            except Exception as e:
                print(
                    f"{phase_name} failed (attempt {attempt}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries:
                    backoff = self.retry_backoff**attempt
                    print(f"Retrying in {backoff:.1f}s...")
                    time.sleep(backoff)
                else:
                    print(f"{phase_name} failed after {self.max_retries} attempts")
                    raise

    async def run_cycle(self):
        """Run one complete pipeline cycle"""
        self.cycle_count += 1
        cycle_start = time.time()

        print(f"\n{'#'*70}")
        print(f"# PIPELINE CYCLE {self.cycle_count}")
        print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}")

        # Get queue stats
        stats = self.get_queue_stats()
        print("\nQueue Status:")
        print(f"  Pending titles (Phase 2):      {stats['pending_titles']}")
        print(f"  Titles need track (Phase 3):   {stats['titles_need_track']}")
        print(f"  Titles need extraction (Phase 3.5): {stats['titles_need_labels']}")
        print(f"  CTMs for clustering (Phase 4):  {stats['ctms_for_clustering']}")
        print(f"  CTMs need summary (Phase 4):    {stats['ctms_need_summary']}")

        # Phase 1: RSS Ingestion (if interval elapsed)
        if self.should_run_phase("phase1"):
            self.run_phase_with_retry(
                "Phase 1: RSS Ingestion",
                run_ingestion,
                max_feeds=None,  # Process all feeds
            )
            self.last_run["phase1"] = time.time()
        else:
            next_run = int(
                self.phase1_interval - (time.time() - self.last_run["phase1"])
            )
            print(f"\nPhase 1: Skipping (next run in {next_run}s)")

        # Phase 2: Centroid Matching (if interval elapsed and work available)
        if self.should_run_phase("phase2") and stats["pending_titles"] > 0:
            self.run_phase_with_retry(
                "Phase 2: Centroid Matching",
                phase2_process,
                batch_size=100,
                max_titles=self.phase2_batch_size,
            )
            self.last_run["phase2"] = time.time()
        else:
            if stats["pending_titles"] == 0:
                print("\nPhase 2: Skipping (no pending titles)")
            else:
                next_run = int(
                    self.phase2_interval - (time.time() - self.last_run["phase2"])
                )
                print(f"\nPhase 2: Skipping (next run in {next_run}s)")

        # Phase 3: Track Assignment (if interval elapsed and work available)
        if self.should_run_phase("phase3") and stats["titles_need_track"] > 0:
            await self.run_phase_with_retry(
                "Phase 3: Track Assignment",
                phase3_process,
                max_titles=self.phase3_batch_size,
            )
            self.last_run["phase3"] = time.time()
        else:
            if stats["titles_need_track"] == 0:
                print("\nPhase 3: Skipping (no titles need track)")
            else:
                next_run = int(
                    self.phase3_interval - (time.time() - self.last_run["phase3"])
                )
                print(f"\nPhase 3: Skipping (next run in {next_run}s)")

        # Phase 3.5: Label + Signal Extraction (if interval elapsed and work available)
        if self.should_run_phase("phase35") and stats["titles_need_labels"] > 0:
            self.run_phase_with_retry(
                "Phase 3.5: Label + Signal Extraction",
                phase35_extract,
                max_titles=self.config.v3_p35_max_titles,
                batch_size=self.config.v3_p35_batch_size,
                concurrency=self.config.v3_p35_concurrency,
            )
            self.last_run["phase35"] = time.time()

            # Phase 3.6: Entity->Country->Centroid backfill (runs after label extraction)
            self.run_phase_with_retry(
                "Phase 3.6: Entity Centroid Backfill",
                phase36_backfill,
                batch_size=500,
            )
        else:
            if stats["titles_need_labels"] == 0:
                print("\nPhase 3.5: Skipping (no titles need labels)")
            else:
                next_run = int(
                    self.phase35_interval - (time.time() - self.last_run["phase35"])
                )
                print(f"\nPhase 3.5: Skipping (next run in {next_run}s)")

        # Phase 4: Event Clustering (if interval elapsed)
        if self.should_run_phase("phase4"):
            self.run_phase_with_retry(
                "Phase 4: Event Clustering",
                self.run_event_clustering,
            )

            # Phase 4.1: Topic Aggregation (LLM merge/cleanup)
            self.run_phase_with_retry(
                "Phase 4.1: Topic Aggregation",
                self.run_topic_aggregation,
            )

            self.last_run["phase4"] = time.time()
        else:
            next_run = int(
                self.phase4_interval - (time.time() - self.last_run["phase4"])
            )
            print("\nPhase 4: Skipping (next run in {})".format(next_run))

        # Phase 4.5a: Event Summaries (decoupled, own interval)
        if self.should_run_phase("phase45a"):
            await self.run_phase_with_retry(
                "Phase 4.5a: Event Summaries",
                self.run_event_summaries,
                max_events=self.config.v3_p45a_max_events,
            )
            self.last_run["phase45a"] = time.time()
        else:
            next_run = int(
                self.phase45a_interval - (time.time() - self.last_run["phase45a"])
            )
            print("\nPhase 4.5a: Skipping (next run in {}s)".format(next_run))

        # Phase 4.5b: CTM Summary Generation (if interval elapsed and work available)
        if self.should_run_phase("phase45") and stats["ctms_need_summary"] > 0:
            await self.run_phase_with_retry(
                "Phase 4.5b: CTM Summary Generation",
                phase45_summaries,
                max_ctms=self.phase4_batch_size,
            )
            self.last_run["phase45"] = time.time()

            # Monitor summary word counts after generation
            self.monitor_summary_word_counts()
        else:
            if stats["ctms_need_summary"] == 0:
                print("\nPhase 4.5: Skipping (no CTMs need summary)")
            else:
                next_run = int(
                    self.phase45_interval - (time.time() - self.last_run["phase45"])
                )
                print(f"\nPhase 4.5: Skipping (next run in {next_run}s)")

        cycle_duration = time.time() - cycle_start
        print(f"\n{'='*70}")
        print(f"Cycle {self.cycle_count} completed in {cycle_duration:.1f}s")
        print(f"{'='*70}")

        # Print full statistics after cycle completion
        self.print_full_statistics()

    async def run(self):
        """Main daemon loop"""
        print(f"{'#'*70}")
        print("# SNI v3 Pipeline Daemon Starting")
        print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}")
        print("\nConfiguration:")
        print(
            f"  Phase 1 interval: {self.phase1_interval}s ({self.phase1_interval/3600:.1f} hours - RSS ingestion)"
        )
        print(
            f"  Phase 2 interval: {self.phase2_interval}s ({self.phase2_interval/60:.0f} minutes - centroid matching)"
        )
        print(
            f"  Phase 3 interval: {self.phase3_interval}s ({self.phase3_interval/60:.0f} minutes - track assignment)"
        )
        print(
            f"  Phase 3.5 interval: {self.phase35_interval}s ({self.phase35_interval/60:.0f} minutes - label + signal extraction)"
        )
        print(
            f"  Phase 4 interval: {self.phase4_interval}s ({self.phase4_interval/60:.0f} minutes - event clustering)"
        )
        print(
            f"  Phase 4.5a interval: {self.phase45a_interval}s ({self.phase45a_interval/60:.0f} minutes - event summaries)"
        )
        print(
            f"  Phase 4.5b interval: {self.phase45_interval}s ({self.phase45_interval/3600:.0f} hour - CTM summaries)"
        )
        print("\nPress Ctrl+C to shutdown gracefully\n")

        while self.running:
            try:
                await self.run_cycle()

                # Sleep between cycles (short interval for responsiveness)
                sleep_time = 60  # 1 minute between cycle checks
                for _ in range(sleep_time):
                    if not self.running:
                        break
                    await asyncio.sleep(1)

            except KeyboardInterrupt:
                print("\nKeyboard interrupt detected, shutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"\nUnexpected error in main loop: {e}")
                print("Waiting 60s before retry...")
                await asyncio.sleep(60)

        print("\nPipeline daemon stopped")


if __name__ == "__main__":
    daemon = PipelineDaemon()
    asyncio.run(daemon.run())
