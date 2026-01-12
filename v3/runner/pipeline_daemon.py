"""
SNI v3 Pipeline Daemon

Orchestrates the complete v3 pipeline with configurable intervals:
- Phase 1: RSS ingestion (frequent)
- Phase 2: Centroid matching (frequent)
- Phase 3: Track assignment & CTM creation (frequent)
- Phase 4: CTM enrichment (less frequent, can wait)

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
# Import phase modules
from v3.phase_1.ingest_feeds import run_ingestion
from v3.phase_2.match_centroids import process_batch as phase2_process
from v3.phase_3.assign_tracks import process_batch as phase3_process
from v3.phase_4.generate_events_digest import \
    process_ctm_batch as phase4_1_process
from v3.phase_4.generate_summaries import process_ctm_batch as phase4_2_process


class PipelineDaemon:
    """SNI v3 Pipeline orchestration daemon"""

    def __init__(self):
        self.config = config
        self.running = True
        self.cycle_count = 0

        # Intervals (in seconds)
        self.phase1_interval = 3600  # 1 hour - RSS feeds
        self.phase2_interval = 300  # 5 minutes - Fast matching
        self.phase3_interval = 600  # 10 minutes - LLM track assignment
        self.phase4_interval = 3600  # 1 hour - Enrichment (can wait)

        # Last run timestamps
        self.last_run = {
            "phase1": 0,
            "phase2": 0,
            "phase3": 0,
            "phase4": 0,
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

                # Phase 3 queue (assigned titles without track)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM titles_v3
                    WHERE processing_status = 'assigned'
                      AND centroid_ids IS NOT NULL
                      AND track IS NULL
                """
                )
                titles_need_track = cur.fetchone()[0]

                # Phase 4.1 queue (CTMs without events digest)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM ctm
                    WHERE title_count > 0
                      AND (events_digest = '[]'::jsonb OR events_digest IS NULL)
                      AND is_frozen = false
                """
                )
                ctms_need_events = cur.fetchone()[0]

                # Phase 4.2 queue (CTMs with events but no summary)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM ctm
                    WHERE events_digest IS NOT NULL
                      AND jsonb_array_length(events_digest) > 0
                      AND summary_text IS NULL
                      AND is_frozen = false
                """
                )
                ctms_need_summary = cur.fetchone()[0]

                return {
                    "pending_titles": pending_titles,
                    "titles_need_track": titles_need_track,
                    "ctms_need_events": ctms_need_events,
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
        print(f"  Pending titles (Phase 2):    {stats['pending_titles']}")
        print(f"  Titles need track (Phase 3): {stats['titles_need_track']}")
        print(f"  CTMs need events (Phase 4.1): {stats['ctms_need_events']}")
        print(f"  CTMs need summary (Phase 4.2): {stats['ctms_need_summary']}")

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

        # Phase 4.1: Events Digest (if interval elapsed and work available)
        if self.should_run_phase("phase4") and stats["ctms_need_events"] > 0:
            await self.run_phase_with_retry(
                "Phase 4.1: Events Digest",
                phase4_1_process,
                max_ctms=self.phase4_batch_size,
            )
            # Don't update last_run yet - wait for Phase 4.2
        else:
            if stats["ctms_need_events"] == 0:
                print("\nPhase 4.1: Skipping (no CTMs need events)")
            else:
                next_run = int(
                    self.phase4_interval - (time.time() - self.last_run["phase4"])
                )
                print(f"\nPhase 4.1: Skipping (next run in {next_run}s)")

        # Phase 4.2: Summaries (if interval elapsed and work available)
        if self.should_run_phase("phase4") and stats["ctms_need_summary"] > 0:
            await self.run_phase_with_retry(
                "Phase 4.2: Summary Generation",
                phase4_2_process,
                max_ctms=self.phase4_batch_size,
            )
            self.last_run["phase4"] = time.time()

            # Monitor summary word counts after generation
            self.monitor_summary_word_counts()
        else:
            if stats["ctms_need_summary"] == 0:
                print("\nPhase 4.2: Skipping (no CTMs need summary)")

        cycle_duration = time.time() - cycle_start
        print(f"\n{'='*70}")
        print(f"Cycle {self.cycle_count} completed in {cycle_duration:.1f}s")
        print(f"{'='*70}")

    async def run(self):
        """Main daemon loop"""
        print(f"{'#'*70}")
        print("# SNI v3 Pipeline Daemon Starting")
        print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*70}")
        print("\nConfiguration:")
        print(f"  Phase 1 interval: {self.phase1_interval}s (RSS ingestion)")
        print(f"  Phase 2 interval: {self.phase2_interval}s (centroid matching)")
        print(f"  Phase 3 interval: {self.phase3_interval}s (track assignment)")
        print(f"  Phase 4 interval: {self.phase4_interval}s (enrichment)")
        print("\nBatch Sizes:")
        print(f"  Phase 2: {self.phase2_batch_size} titles")
        print(f"  Phase 3: {self.phase3_batch_size} CTMs")
        print(f"  Phase 4: {self.phase4_batch_size} CTMs")
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
