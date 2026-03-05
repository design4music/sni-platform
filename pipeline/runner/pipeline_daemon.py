"""
SNI v3 Pipeline Daemon -- 4-Slot Architecture

Scheduling slots (phases run sequentially within each slot):
- Slot 1 INGESTION   (12h):  Phase 1 (RSS) + Phase 2 (centroid matching)
- Slot 2 CLASSIFICATION (15m): Phase 3.1 (labels) + 3.2 (backfill) + 3.3 (tracks)
- Slot 3 CLUSTERING  (30m):  Phase 4 (event clustering) + 4.1 (topic aggregation)
- Slot 4 ENRICHMENT  (6h):   Phase 4.5a (event summaries) + 4.5b (CTM summaries)
- Daily purge: Remove rejected titles + reset api_error_count

Features:
- Sequential execution with configurable intervals
- Graceful shutdown on SIGTERM/SIGINT
- Retry logic with exponential backoff
- Phase-level timeouts to prevent hangs
"""

import asyncio
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from psycopg2.pool import ThreadedConnectionPool

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import MAX_API_ERRORS, config

# Import phase modules
from pipeline.phase_1.ingest_feeds import run_ingestion
from pipeline.phase_2.match_centroids import process_batch as phase2_process
from pipeline.phase_3_1.extract_labels import process_titles as phase31_extract
from pipeline.phase_3_2.backfill_entity_centroids import (
    backfill_entity_centroids as phase32_backfill,
)
from pipeline.phase_3_3.assign_tracks_batched import process_batch as phase33_process
from pipeline.phase_4.consolidate_topics import process_ctm as phase41_aggregate
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

        # 4-slot intervals (seconds)
        self.ingestion_interval = 43200  # 12 hours - Phase 1 + 2
        self.classification_interval = 900  # 15 minutes - Phase 3.1 + 3.2 + 3.3
        self.clustering_interval = 1800  # 30 minutes - Phase 4 + 4.1
        self.enrichment_interval = 21600  # 6 hours - Phase 4.5a + 4.5b
        self.social_interval = 10800  # 3 hours - Slot 5: Social Posting
        self.purge_interval = 86400  # 24 hours - daily cleanup

        # Last run timestamps
        self.last_run = {
            "ingestion": 0,
            "classification": 0,
            "clustering": 0,
            "enrichment": 0,
            "social": 0,
            "purge": 0,
        }

        # Batch sizes
        self.classification_batch_size = 500  # Titles per 3.1 and 3.3 run
        self.aggregation_max_ctms = 25  # CTMs per 4.1 run
        self.enrichment_max_events = 2000  # Events per 4.5a run
        self.enrichment_max_ctms = 200  # CTMs per 4.5b run

        # Retry configuration
        self.max_retries = 3
        self.retry_backoff = 2.0  # Exponential backoff multiplier

        # Slot-level timeouts (seconds) -- prevents daemon from hanging
        self.timeout_ingestion = 1200  # 20 min for RSS + centroid matching
        self.timeout_classification = 1200  # 20 min for 3.1 + 3.2 + 3.3
        self.timeout_clustering = 900  # 15 min for Phase 4 + 4.1
        self.timeout_enrichment = 7200  # 120 min for 4.5a + 4.5b
        self.timeout_social = 300  # 5 min for social posting
        self.timeout_purge = 300  # 5 min for daily cleanup

        # Connection pool (minconn=2, maxconn=10)
        self.pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        print(f"\nReceived {signal_name}, shutting down gracefully...")
        self.running = False

    def get_connection(self):
        """Get database connection from pool"""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        if conn:
            self.pool.putconn(conn)

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

                # Phase 3.1 queue (assigned titles without labels)
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM titles_v3 t
                    WHERE t.processing_status = 'assigned'
                      AND t.centroid_ids IS NOT NULL
                      AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id)
                """
                )
                titles_need_labels = cur.fetchone()[0]

                # Phase 3.3 queue (assigned titles without track assignment)
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
            self.return_connection(conn)

    def should_run_slot(self, slot_name: str) -> bool:
        """Check if enough time has passed since last run of this slot"""
        now = time.time()
        last = self.last_run[slot_name]
        interval = getattr(self, "%s_interval" % slot_name)
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
            self.return_connection(conn)

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

                print("\nPHASE 3.3 - TRACK ASSIGNMENT & CTM CREATION:")
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
            self.return_connection(conn)

    def run_event_clustering(self):
        """Run event clustering only for CTMs with NEW titles since last clustering.

        Skips CTMs where title_count hasn't changed to preserve Phase 4.5a enrichment.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Only re-cluster CTMs with new titles since last clustering
                cur.execute(
                    """
                    SELECT id, centroid_id, track, TO_CHAR(month, 'YYYY-MM') as month
                    FROM ctm
                    WHERE title_count >= 3 AND is_frozen = false
                      AND (
                          title_count_at_clustering IS NULL
                          OR title_count > title_count_at_clustering
                      )
                    ORDER BY month DESC
                    """
                )
                ctms = cur.fetchall()

                # Also count skipped for logging
                cur.execute(
                    """
                    SELECT COUNT(*) FROM ctm
                    WHERE title_count >= 3 AND is_frozen = false
                      AND title_count_at_clustering IS NOT NULL
                      AND title_count = title_count_at_clustering
                    """
                )
                skipped = cur.fetchone()[0]

            if not ctms:
                print(
                    "No CTMs have new titles - skipping clustering ({} unchanged)".format(
                        skipped
                    )
                )
                return

            print(
                "Clustering {} CTMs with new titles ({} unchanged, skipped)...".format(
                    len(ctms), skipped
                )
            )

            processed = 0
            total_topics = 0
            for ctm_id, centroid_id, track, month in ctms:
                written = process_ctm_for_daemon(conn, ctm_id, centroid_id, track)
                if written > 0:
                    total_topics += written
                    processed += 1

                # Mark as clustered at current title_count
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE ctm SET title_count_at_clustering = title_count WHERE id = %s",
                        (ctm_id,),
                    )
                conn.commit()

            print("Clustered {} topics across {} CTMs".format(total_topics, processed))

        finally:
            self.return_connection(conn)

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
            self.return_connection(conn)

    def run_materialize_signals(self):
        """Materialize top signals per centroid for current unfrozen months."""
        from pipeline.phase_4.materialize_centroid_signals import materialize

        materialize()

    def run_materialize_signal_graph(self):
        """Materialize signal co-occurrence graph (rolling 30d)."""
        from pipeline.phase_4.materialize_signal_graph import materialize

        materialize(period="rolling")

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
            self.return_connection(conn)

    def _run_social(self):
        """Run social posting (Slot 5)."""
        conn = self.get_connection()
        try:
            from pipeline.social.social_posting import run_social_posting

            return run_social_posting(conn, self.config)
        finally:
            self.return_connection(conn)

    def run_daily_purge(self):
        """Purge rejected titles older than 24h to tombstone table."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            rejected = ("out_of_scope", "blocked_stopword", "blocked_llm")

            # Count
            cur.execute(
                """
                SELECT processing_status, COUNT(*)
                FROM titles_v3
                WHERE processing_status = ANY(%s)
                  AND updated_at < NOW() - INTERVAL '24 hours'
                GROUP BY processing_status
                """,
                (list(rejected),),
            )
            status_counts = dict(cur.fetchall())
            total = sum(status_counts.values())

            if total == 0:
                print("  No rejected titles to purge")
                return {"purged": 0}

            for status, count in status_counts.items():
                print("  %s: %d" % (status, count))

            # Tombstone
            cur.execute(
                """
                INSERT INTO titles_purged (url_hash, original_title, source_domain, reason)
                SELECT md5(url_gnews), LEFT(title_display, 500), publisher_name, processing_status
                FROM titles_v3
                WHERE processing_status = ANY(%s)
                  AND updated_at < NOW() - INTERVAL '24 hours'
                ON CONFLICT (url_hash) DO NOTHING
                """,
                (list(rejected),),
            )
            tombstoned = cur.rowcount

            # Delete
            cur.execute(
                """
                DELETE FROM titles_v3
                WHERE processing_status = ANY(%s)
                  AND updated_at < NOW() - INTERVAL '24 hours'
                """,
                (list(rejected),),
            )
            deleted = cur.rowcount
            conn.commit()

            print("  Purged %d titles (%d tombstoned)" % (deleted, tombstoned))

            # Reset API error circuit breakers so transient failures don't block titles permanently
            cur.execute(
                "UPDATE titles_v3 SET api_error_count = 0 WHERE api_error_count >= %s",
                (MAX_API_ERRORS,),
            )
            if cur.rowcount:
                print("  Reset api_error_count for %d titles" % cur.rowcount)
                conn.commit()

            return {"purged": deleted}

        finally:
            self.return_connection(conn)

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

    async def run_with_timeout(self, phase_name, coro, timeout_seconds):
        """Run an async coroutine with a timeout. Returns None on timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            print(f"{phase_name} timed out after {timeout_seconds}s, moving on")
            return None

    async def run_cycle(self):
        """Run one complete pipeline cycle (4 slots + daily purge)"""
        self.cycle_count += 1
        cycle_start = time.time()

        print("\n" + "#" * 70)
        print("# PIPELINE CYCLE %d" % self.cycle_count)
        print("# %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("#" * 70)

        # Get queue stats
        stats = self.get_queue_stats()
        print("\nQueue Status:")
        print("  Pending titles (Phase 2):        %d" % stats["pending_titles"])
        print("  Titles need labels (Phase 3.1):  %d" % stats["titles_need_labels"])
        print("  Titles need track (Phase 3.3):   %d" % stats["titles_need_track"])
        print("  CTMs for clustering (Phase 4):   %d" % stats["ctms_for_clustering"])
        print("  CTMs need summary (Phase 4.5b):  %d" % stats["ctms_need_summary"])

        # --- SLOT 1: INGESTION (Phase 1 + Phase 2) ---
        if self.should_run_slot("ingestion"):
            await self.run_with_timeout(
                "Phase 1: RSS Ingestion",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 1: RSS Ingestion",
                    run_ingestion,
                    max_feeds=None,
                ),
                self.timeout_ingestion,
            )
            await self.run_with_timeout(
                "Phase 2: Centroid Matching",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 2: Centroid Matching",
                    phase2_process,
                    batch_size=100,
                    max_titles=None,
                ),
                self.timeout_ingestion,
            )
            self.last_run["ingestion"] = time.time()
        else:
            remaining = int(
                self.ingestion_interval - (time.time() - self.last_run["ingestion"])
            )
            print("\nSlot 1 INGESTION: next in %ds" % remaining)

        # --- SLOT 2: CLASSIFICATION (Phase 3.1 + 3.2 + 3.3) ---
        if self.should_run_slot("classification"):
            has_work = stats["titles_need_labels"] > 0 or stats["titles_need_track"] > 0
            if has_work:
                # Phase 3.1: Label + Signal Extraction
                if stats["titles_need_labels"] > 0:
                    await self.run_with_timeout(
                        "Phase 3.1: Label + Signal Extraction",
                        asyncio.to_thread(
                            self.run_phase_with_retry,
                            "Phase 3.1: Label + Signal Extraction",
                            phase31_extract,
                            max_titles=self.config.v3_p31_max_titles,
                            batch_size=self.config.v3_p31_batch_size,
                            concurrency=self.config.v3_p31_concurrency,
                        ),
                        self.timeout_classification,
                    )
                    # Phase 3.2: Entity Centroid Backfill (always after 3.1)
                    await self.run_with_timeout(
                        "Phase 3.2: Entity Centroid Backfill",
                        asyncio.to_thread(
                            self.run_phase_with_retry,
                            "Phase 3.2: Entity Centroid Backfill",
                            phase32_backfill,
                            batch_size=500,
                        ),
                        self.timeout_classification,
                    )

                # Phase 3.3: Intel Gating + Track Assignment
                if stats["titles_need_track"] > 0:
                    await self.run_with_timeout(
                        "Phase 3.3: Intel Gating + Track Assignment",
                        self.run_phase_with_retry(
                            "Phase 3.3: Intel Gating + Track Assignment",
                            phase33_process,
                            max_titles=self.classification_batch_size,
                        ),
                        self.timeout_classification,
                    )
            else:
                print("\nSlot 2 CLASSIFICATION: no work")
            self.last_run["classification"] = time.time()
        else:
            remaining = int(
                self.classification_interval
                - (time.time() - self.last_run["classification"])
            )
            print("\nSlot 2 CLASSIFICATION: next in %ds" % remaining)

        # --- SLOT 3: CLUSTERING (Phase 4 + Phase 4.1) ---
        if self.should_run_slot("clustering"):
            # Phase 4: Event Clustering
            await self.run_with_timeout(
                "Phase 4: Event Clustering",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 4: Event Clustering",
                    self.run_event_clustering,
                ),
                self.timeout_clustering,
            )
            # Phase 4.1: Topic Aggregation
            await self.run_with_timeout(
                "Phase 4.1: Topic Aggregation",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 4.1: Topic Aggregation",
                    self.run_topic_aggregation,
                    max_ctms=self.aggregation_max_ctms,
                ),
                self.timeout_clustering,
            )
            # Phase 4.2: Materialize pre-computed views (mv_* tables)
            await self.run_with_timeout(
                "Phase 4.2a: Centroid Top Signals",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 4.2a: Centroid Top Signals",
                    self.run_materialize_signals,
                ),
                300,
            )
            await self.run_with_timeout(
                "Phase 4.2b: Signal Graph",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 4.2b: Signal Graph",
                    self.run_materialize_signal_graph,
                ),
                300,
            )
            self.last_run["clustering"] = time.time()
        else:
            remaining = int(
                self.clustering_interval - (time.time() - self.last_run["clustering"])
            )
            print("\nSlot 3 CLUSTERING: next in %ds" % remaining)

        # --- SLOT 4: ENRICHMENT (Phase 4.5a + Phase 4.5b) ---
        if self.should_run_slot("enrichment"):
            # Phase 4.5a: Event Summaries
            await self.run_with_timeout(
                "Phase 4.5a: Event Summaries",
                self.run_phase_with_retry(
                    "Phase 4.5a: Event Summaries",
                    self.run_event_summaries,
                    max_events=self.enrichment_max_events,
                ),
                self.timeout_enrichment,
            )
            # Phase 4.5b: CTM Summary Generation
            if stats["ctms_need_summary"] > 0:
                await self.run_with_timeout(
                    "Phase 4.5b: CTM Summary Generation",
                    self.run_phase_with_retry(
                        "Phase 4.5b: CTM Summary Generation",
                        phase45_summaries,
                        max_ctms=self.enrichment_max_ctms,
                    ),
                    self.timeout_enrichment,
                )
                self.monitor_summary_word_counts()
            self.last_run["enrichment"] = time.time()
        else:
            remaining = int(
                self.enrichment_interval - (time.time() - self.last_run["enrichment"])
            )
            print("\nSlot 4 ENRICHMENT: next in %ds" % remaining)

        # --- SLOT 5: SOCIAL POSTING ---
        if self.should_run_slot("social") and self.config.social_posting_enabled:
            await self.run_with_timeout(
                "Phase 5: Social Posting",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Phase 5: Social Posting",
                    self._run_social,
                ),
                self.timeout_social,
            )
            self.last_run["social"] = time.time()
        elif self.config.social_posting_enabled:
            remaining = int(
                self.social_interval - (time.time() - self.last_run["social"])
            )
            print("\nSlot 5 SOCIAL: next in %ds" % remaining)

        # --- DAILY PURGE ---
        if self.should_run_slot("purge"):
            await self.run_with_timeout(
                "Daily Purge",
                asyncio.to_thread(
                    self.run_phase_with_retry,
                    "Daily Purge",
                    self.run_daily_purge,
                ),
                self.timeout_purge,
            )
            self.last_run["purge"] = time.time()
        else:
            remaining = int(
                self.purge_interval - (time.time() - self.last_run["purge"])
            )
            print("\nDaily Purge: next in %ds" % remaining)

        cycle_duration = time.time() - cycle_start
        print("\n" + "=" * 70)
        print("Cycle %d completed in %.1fs" % (self.cycle_count, cycle_duration))
        print("=" * 70)

        # Print full statistics after cycle completion
        self.print_full_statistics()

    async def run(self):
        """Main daemon loop"""
        print("#" * 70)
        print("# SNI v3 Pipeline Daemon Starting (4-Slot Architecture)")
        print("# %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("#" * 70)
        print("\nScheduling Slots:")
        print(
            "  Slot 1 INGESTION:      %dh  (Phase 1 + 2)"
            % (self.ingestion_interval // 3600)
        )
        print(
            "  Slot 2 CLASSIFICATION: %dm  (Phase 3.1 + 3.2 + 3.3)"
            % (self.classification_interval // 60)
        )
        print(
            "  Slot 3 CLUSTERING:     %dm  (Phase 4 + 4.1)"
            % (self.clustering_interval // 60)
        )
        print(
            "  Slot 4 ENRICHMENT:     %dh  (Phase 4.5a + 4.5b)"
            % (self.enrichment_interval // 3600)
        )
        if self.config.social_posting_enabled:
            print(
                "  Slot 5 SOCIAL:         %dh  (Social Posting)"
                % (self.social_interval // 3600)
            )
        print("  Daily Purge:           %dh" % (self.purge_interval // 3600))
        print("\nBatch Sizes:")
        print("  Classification: %d titles/run" % self.classification_batch_size)
        print("  Aggregation:    %d CTMs/run" % self.aggregation_max_ctms)
        print("  Event summaries: %d events/run" % self.enrichment_max_events)
        print("  CTM summaries:   %d CTMs/run" % self.enrichment_max_ctms)
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

        # Close connection pool
        if hasattr(self, "pool") and self.pool:
            self.pool.closeall()
            print("Connection pool closed")
        print("\nPipeline daemon stopped")


if __name__ == "__main__":
    daemon = PipelineDaemon()
    asyncio.run(daemon.run())
