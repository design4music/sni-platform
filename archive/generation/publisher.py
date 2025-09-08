#!/usr/bin/env python3
"""
SNI Publisher - Draft to Published Narrative Promotion
Evaluates consolidated narratives against evidence, content, and safety gates
to determine publication readiness with proper narrative-scoped evidence checking.
"""

import argparse
import json
import logging
import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NarrativePublisher:
    """
    SNI Narrative Publisher with Proper Evidence Scoping

    Evaluates narratives for publication readiness using evidence, content,
    and safety gates, with all evidence checks scoped to narrative-specific clusters.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

        # RAI service configuration
        self.rai_enabled = os.getenv("RAI_ENABLED", "false").lower() == "true"

        # Evidence gate thresholds
        self.evidence_days = self.config.get("evidence_days", 7)
        self.parent_days = self.config.get("parent_days", 14)
        self.min_articles = self.config.get("min_articles", 4)
        self.min_sources = self.config.get("min_sources", 3)
        self.entropy_max = self.config.get("entropy_max", 2.40)

        # Content gate thresholds
        self.title_min_words = self.config.get("title_min_words", 8)
        self.title_max_words = self.config.get("title_max_words", 14)
        self.summary_min_sentences = self.config.get("summary_min_sentences", 2)

        # Safety gate thresholds
        self.rai_confidence_min = self.config.get("rai_confidence_min", 0.6)
        self.archive_inactive_days = self.config.get("archive_inactive_days", 21)

        logger.info(
            f"Publisher initialized: evidence_days={self.evidence_days}, "
            f"min_articles={self.min_articles}, entropy_max={self.entropy_max}, rai_enabled={self.rai_enabled}"
        )

    def get_db_connection(self):
        """Get database connection."""
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "narrative_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )

    def load_publication_candidates(self, conn) -> List[Dict]:
        """Load narratives eligible for publication review."""
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        query = """
        SELECT
            id,
            narrative_id,
            title,
            summary,
            publication_status,
            consolidation_stage,
            update_status,
            rai_analysis,
            source_stats,
            created_at,
            updated_at,
            parent_id,
            version_history,
            archive_reason,
            activity_timeline
        FROM narratives
        WHERE publication_status = 'draft'  -- Only draft narratives eligible for publication
        AND consolidation_stage = 'consolidated'
        AND archive_reason IS NULL
        AND (
            -- RAI enabled path: require GEN-3 completion
            (update_status->'gen'->>'gen3_done_at') IS NOT NULL OR
            (
                -- RAI disabled path: require GEN-2 completion and publication ready flag
                (update_status->'gen'->>'gen2_done_at') IS NOT NULL AND
                COALESCE((update_status->'gen'->>'publication_ready')::boolean, false) = true
            )
        )
        ORDER BY updated_at DESC
        """

        cursor.execute(query)
        candidates = [dict(row) for row in cursor.fetchall()]

        cursor.close()
        logger.info(f"Loaded {len(candidates)} publication candidates")
        return candidates

    def get_narrative_cluster_ids(
        self, conn, narrative_id: int, days_back: int
    ) -> List[str]:
        """Get cluster_ids attached to narrative from activity_timeline (last N days)."""
        cursor = conn.cursor()

        # First try new format (array of timeline entries)
        query_new = """
        SELECT DISTINCT e->>'cluster_id' AS cluster_id
        FROM narratives n,
             jsonb_array_elements(n.activity_timeline) e
        WHERE n.id = %s
          AND e->>'cluster_id' IS NOT NULL
          AND (e->>'ts')::timestamptz >= NOW() - INTERVAL '%s days'
        """

        # Use a single query that handles both formats with COALESCE
        query_combined = """
        WITH timeline_entries AS (
            SELECT n.id, 
                   CASE 
                     WHEN jsonb_typeof(n.activity_timeline) = 'array' THEN n.activity_timeline
                     WHEN jsonb_typeof(n.activity_timeline) = 'object' AND n.activity_timeline ? 'cluster_evidence' 
                       THEN n.activity_timeline->'cluster_evidence'
                     ELSE '[]'::jsonb
                   END as timeline_array
            FROM narratives n
            WHERE n.id = %s
        )
        SELECT DISTINCT e->>'cluster_id' AS cluster_id
        FROM timeline_entries te,
             jsonb_array_elements(te.timeline_array) e
        WHERE e->>'cluster_id' IS NOT NULL
          AND (e->>'ts')::timestamptz >= NOW() - INTERVAL '%s days'
        """

        try:
            cursor.execute(query_combined, (narrative_id, days_back))
            cluster_ids = [
                row[0]
                for row in cursor.fetchall()
                if row[0] is not None and row[0] != ""
            ]
            cursor.close()
            logger.debug(
                f"Found {len(cluster_ids)} cluster_ids for narrative {narrative_id}"
            )
            return cluster_ids
        except Exception as e:
            logger.warning(f"Timeline query failed for narrative {narrative_id}: {e}")
            cursor.close()
            return []

    def get_cluster_evidence(
        self, conn, cluster_ids: List[str], days_back: int
    ) -> Dict:
        """Get cluster evidence for narrative-specific clusters."""
        if not cluster_ids:
            return {
                "qualifying_clusters": 0,
                "max_cluster_size": 0,
                "max_source_count": 0,
                "latest_cluster_date": None,
            }

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Evidence gate (size + sources) on narrative's cluster_ids only
        query = """
        SELECT m.cluster_id,
               COUNT(*)                       AS size,
               COUNT(DISTINCT a.source_name)  AS source_count,
               MAX(a.created_at)              AS latest_cluster_date
        FROM article_cluster_members m
        JOIN articles a ON a.id = m.article_id
        WHERE m.cluster_id = ANY(%s::uuid[])
          AND a.created_at >= NOW() - INTERVAL '%s days'
        GROUP BY m.cluster_id
        HAVING COUNT(*) >= %s AND COUNT(DISTINCT a.source_name) >= %s
        ORDER BY latest_cluster_date DESC
        """

        cursor.execute(
            query, (cluster_ids, days_back, self.min_articles, self.min_sources)
        )
        clusters = cursor.fetchall()

        evidence = {
            "qualifying_clusters": len(clusters),
            "max_cluster_size": max([c["size"] for c in clusters]) if clusters else 0,
            "max_source_count": (
                max([c["source_count"] for c in clusters]) if clusters else 0
            ),
            "latest_cluster_date": (
                clusters[0]["latest_cluster_date"] if clusters else None
            ),
        }

        cursor.close()
        return evidence

    def check_parent_evidence(self, conn, parent_id: int) -> Dict:
        """Check parent narrative evidence (>=2 qualifying clusters in parent_days)."""
        if not parent_id:
            return {"parent_qualifying_clusters": 0}

        # Get parent's cluster_ids
        parent_cluster_ids = self.get_narrative_cluster_ids(
            conn, parent_id, self.parent_days
        )

        if not parent_cluster_ids:
            return {"parent_qualifying_clusters": 0}

        # Check evidence on parent's clusters
        parent_evidence = self.get_cluster_evidence(
            conn, parent_cluster_ids, self.parent_days
        )

        return {"parent_qualifying_clusters": parent_evidence["qualifying_clusters"]}

    def calculate_cluster_entropy(
        self, conn, cluster_ids: List[int], days_back: int
    ) -> float:
        """Calculate median entropy across narrative's attached clusters only."""
        if not cluster_ids:
            return 0.0

        cursor = conn.cursor()
        entropies = []

        # Calculate entropy for each attached cluster
        for cluster_id in cluster_ids:
            query = """
            SELECT
                a.source_name,
                COUNT(*) as article_count
            FROM article_cluster_members m
            JOIN articles a ON a.id = m.article_id
            WHERE m.cluster_id = %s::uuid
              AND a.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY a.source_name
            ORDER BY article_count DESC
            """

            cursor.execute(query, (cluster_id, days_back))
            source_counts = cursor.fetchall()

            if source_counts:
                total_articles = sum(count for _, count in source_counts)
                if total_articles > 0:
                    # Calculate Shannon entropy
                    entropy = 0.0
                    for _, count in source_counts:
                        if count > 0:
                            p = count / total_articles
                            entropy -= p * math.log2(p)
                    entropies.append(entropy)

        cursor.close()

        # Return median entropy
        if entropies:
            entropies.sort()
            n = len(entropies)
            if n % 2 == 0:
                return (entropies[n // 2 - 1] + entropies[n // 2]) / 2
            else:
                return entropies[n // 2]
        return 0.0

    def has_event_signal(self, conn, cluster_ids: List[int], days_back: int) -> bool:
        """Check if narrative's attached clusters have event signals."""
        if not cluster_ids:
            return False

        cursor = conn.cursor()

        # Event signal check scoped to narrative's clusters
        query = """
        SELECT EXISTS (
          SELECT 1
          FROM article_cluster_members m
          JOIN articles a ON a.id = m.article_id
          JOIN article_core_keywords ack ON ack.article_id = m.article_id
          JOIN event_signals_30d es ON es.signal = ack.token
          WHERE m.cluster_id = ANY(%s::uuid[])
            AND a.created_at >= NOW() - INTERVAL '%s days'
          LIMIT 1
        ) as has_event_signal
        """

        cursor.execute(query, (cluster_ids, days_back))
        result = cursor.fetchone()
        has_signal = result[0] if result else False

        cursor.close()
        return has_signal

    def check_evidence_gates(self, conn, candidate: Dict) -> Tuple[bool, Dict]:
        """Check evidence gates for publication eligibility with narrative scoping."""
        narrative_id = candidate["id"]  # Use database ID for queries
        parent_id = candidate.get("parent_id")

        # Get narrative's attached cluster_ids from activity_timeline
        cluster_ids = self.get_narrative_cluster_ids(
            conn, narrative_id, self.evidence_days
        )

        # If no attached clusters, evidence fails immediately
        if not cluster_ids:
            logger.debug(f"No cluster_ids found for narrative {narrative_id}")
            return False, {
                "evidence_passed": False,
                "entropy_passed": False,
                "event_signal_passed": False,
                "qualifying_clusters": 0,
                "parent_qualifying_clusters": 0,
                "entropy": 0.0,
                "has_event_signal": False,
                "cluster_ids_found": 0,
            }

        # Get cluster evidence scoped to narrative's clusters
        evidence = self.get_cluster_evidence(conn, cluster_ids, self.evidence_days)

        # Check parent evidence if no direct clusters qualify
        parent_evidence = {}
        if evidence["qualifying_clusters"] == 0 and parent_id:
            parent_evidence = self.check_parent_evidence(conn, parent_id)

        # Calculate entropy and check event signal on narrative's clusters
        entropy = self.calculate_cluster_entropy(conn, cluster_ids, self.evidence_days)
        has_event = self.has_event_signal(conn, cluster_ids, self.evidence_days)

        # Evidence gate logic
        direct_evidence = evidence["qualifying_clusters"] >= 1
        parent_evidence_sufficient = (
            parent_evidence.get("parent_qualifying_clusters", 0) >= 2
        )

        evidence_passed = direct_evidence or parent_evidence_sufficient
        entropy_passed = entropy <= self.entropy_max
        event_signal_passed = has_event

        gate_results = {
            "evidence_passed": evidence_passed,
            "entropy_passed": entropy_passed,
            "event_signal_passed": event_signal_passed,
            "qualifying_clusters": evidence["qualifying_clusters"],
            "parent_qualifying_clusters": parent_evidence.get(
                "parent_qualifying_clusters", 0
            ),
            "entropy": entropy,
            "has_event_signal": has_event,
            "cluster_ids_found": len(cluster_ids),
        }

        all_evidence_passed = evidence_passed and entropy_passed and event_signal_passed

        return all_evidence_passed, gate_results

    def check_content_gates(self, candidate: Dict) -> Tuple[bool, Dict]:
        """Check content quality gates."""
        title = candidate.get("title", "") or ""
        summary = candidate.get("summary", "") or ""

        # Title check (8-14 words)
        title_words = len(title.split()) if title else 0
        title_passed = self.title_min_words <= title_words <= self.title_max_words

        # Summary check (>=2 sentences)
        sentence_count = (
            len([s for s in summary.split(".") if s.strip()]) if summary else 0
        )
        summary_passed = sentence_count >= self.summary_min_sentences

        # Basic content presence
        content_present = bool(title.strip() and summary.strip())

        gate_results = {
            "title_passed": title_passed,
            "summary_passed": summary_passed,
            "content_present": content_present,
            "title_words": title_words,
            "summary_sentences": sentence_count,
        }

        all_content_passed = title_passed and summary_passed and content_present

        return all_content_passed, gate_results

    def check_safety_gates(self, candidate: Dict) -> Tuple[bool, Dict]:
        """Check safety and quality gates."""
        update_status = candidate.get("update_status", {})
        rai_analysis = candidate.get("rai_analysis", {})

        # Update status check
        if isinstance(update_status, dict):
            status_value = update_status.get("status", "ok")
        else:
            status_value = str(update_status) if update_status else "ok"

        update_status_passed = status_value not in ("needs_review", "hold")

        # RAI analysis check (if present)
        rai_passed = True
        rai_confidence = None

        if rai_analysis:
            if isinstance(rai_analysis, dict):
                rai_confidence = rai_analysis.get("confidence_rating", 1.0)
                if rai_confidence is not None:
                    rai_passed = float(rai_confidence) >= self.rai_confidence_min

        gate_results = {
            "update_status_passed": update_status_passed,
            "rai_passed": rai_passed,
            "update_status": status_value,
            "rai_confidence": rai_confidence,
        }

        all_safety_passed = update_status_passed and rai_passed

        return all_safety_passed, gate_results

    def promote_to_published(self, conn, candidate: Dict, gate_results: Dict):
        """Promote narrative to published status."""
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            # Update version history
            version_history = candidate.get("version_history", []) or []
            new_version = {
                "version": f"{len(version_history) + 1}.0",
                "date": datetime.now().isoformat(),
                "change": "Published via evidence gates",
                "gate_results": gate_results,
            }
            version_history.append(new_version)

            # Update record
            update_query = """
            UPDATE narratives
            SET
                publication_status = 'published',
                update_status = %s,
                version_history = %s,
                updated_at = %s
            WHERE id = %s
            """

            update_status = {
                "status": "ok",
                "last_updated": datetime.now().isoformat(),
                "update_trigger": "publisher_promotion",
                "gate_validation": "passed",
            }

            cursor.execute(
                update_query,
                (
                    json.dumps(update_status),
                    json.dumps(version_history),
                    datetime.now(),
                    candidate["id"],
                ),
            )

            conn.commit()
            logger.info(f"Published narrative {candidate['narrative_id']}")

        except Exception as e:
            conn.rollback()
            logger.error(
                f"Failed to publish narrative {candidate['narrative_id']}: {e}"
            )
            raise
        finally:
            cursor.close()

    def archive_inactive_narratives(self, conn) -> int:
        """Archive narratives inactive for >21 days."""
        cursor = conn.cursor()

        archive_cutoff = datetime.now() - timedelta(days=self.archive_inactive_days)

        # Fixed archive query with correct status fields
        query = """
        UPDATE narratives
        SET
            publication_status = 'archived',
            archive_reason = %s,
            updated_at = %s
        WHERE publication_status IN ('draft', 'published')
        AND consolidation_stage IN ('consolidated', 'published')
        AND updated_at < %s
        AND archive_reason IS NULL
        """

        archive_reason = {
            "reason": "inactive_21d",
            "archived_at": datetime.now().isoformat(),
            "last_activity": archive_cutoff.isoformat(),
        }

        cursor.execute(
            query, (json.dumps(archive_reason), datetime.now(), archive_cutoff)
        )

        archived_count = cursor.rowcount
        conn.commit()
        cursor.close()

        if archived_count > 0:
            logger.info(f"Archived {archived_count} inactive narratives (>21 days)")

        return archived_count

    def run_publication_review(self) -> Dict[str, int]:
        """Run the complete publication review process."""
        results = {
            "candidates_reviewed": 0,
            "published": 0,
            "failed_evidence": 0,
            "failed_content": 0,
            "failed_safety": 0,
            "already_published": 0,
            "archived_inactive": 0,
        }

        with self.get_db_connection() as conn:
            # Load candidates
            candidates = self.load_publication_candidates(conn)
            results["candidates_reviewed"] = len(candidates)

            # Review each candidate
            for candidate in candidates:
                narrative_id = candidate["narrative_id"]
                current_status = candidate["publication_status"]

                if current_status == "published":
                    results["already_published"] += 1
                    continue

                logger.info(f"Reviewing narrative {narrative_id}")

                # Check all gates with narrative-scoped evidence
                evidence_passed, evidence_results = self.check_evidence_gates(
                    conn, candidate
                )
                content_passed, content_results = self.check_content_gates(candidate)
                safety_passed, safety_results = self.check_safety_gates(candidate)

                # Combined gate results for logging
                all_gate_results = {
                    **evidence_results,
                    **content_results,
                    **safety_results,
                }

                # Decision logic
                if evidence_passed and content_passed and safety_passed:
                    self.promote_to_published(conn, candidate, all_gate_results)
                    results["published"] += 1
                else:
                    # Log failure reasons
                    if not evidence_passed:
                        results["failed_evidence"] += 1
                        logger.info(
                            f"  {narrative_id}: Evidence gates failed "
                            f"(clusters: {evidence_results.get('cluster_ids_found', 0)}, "
                            f"qualifying: {evidence_results.get('qualifying_clusters', 0)})"
                        )
                    if not content_passed:
                        results["failed_content"] += 1
                        logger.info(f"  {narrative_id}: Content gates failed")
                    if not safety_passed:
                        results["failed_safety"] += 1
                        logger.info(f"  {narrative_id}: Safety gates failed")

            # Archive inactive narratives
            results["archived_inactive"] = self.archive_inactive_narratives(conn)

        return results

    def print_summary(self, results: Dict[str, int]):
        """Print publication review summary."""
        print("\n=== PUBLICATION REVIEW SUMMARY ===")
        print(f"Candidates reviewed: {results['candidates_reviewed']}")
        print(f"Promoted to published: {results['published']}")
        print(f"Already published: {results['already_published']}")
        print(f"Failed evidence gates: {results['failed_evidence']}")
        print(f"Failed content gates: {results['failed_content']}")
        print(f"Failed safety gates: {results['failed_safety']}")
        print(f"Archived inactive: {results['archived_inactive']}")
        print()

        active_candidates = (
            results["candidates_reviewed"] - results["already_published"]
        )
        if active_candidates > 0:
            success_rate = (results["published"] / active_candidates) * 100
            print(f"Publication success rate: {success_rate:.1f}%")
        else:
            print("Publication success rate: N/A (no active candidates)")


def main():
    """Main entry point with CLI arguments."""
    parser = argparse.ArgumentParser(
        description="SNI Narrative Publisher - Draft to Published Promotion",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--evidence-days",
        type=int,
        default=7,
        help="Days to look back for cluster evidence",
    )
    parser.add_argument(
        "--parent-days",
        type=int,
        default=14,
        help="Days to look back for parent narrative evidence",
    )
    parser.add_argument(
        "--min-articles",
        type=int,
        default=4,
        help="Minimum articles per qualifying cluster",
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=3,
        help="Minimum sources per qualifying cluster",
    )
    parser.add_argument(
        "--entropy-max",
        type=float,
        default=2.40,
        help="Maximum cluster entropy threshold",
    )

    args = parser.parse_args()

    config = {
        "evidence_days": args.evidence_days,
        "parent_days": args.parent_days,
        "min_articles": args.min_articles,
        "min_sources": args.min_sources,
        "entropy_max": args.entropy_max,
    }

    # Run publisher
    publisher = NarrativePublisher(config)
    results = publisher.run_publication_review()
    publisher.print_summary(results)

    # Exit with appropriate code
    sys.exit(
        0 if results["published"] > 0 or results["candidates_reviewed"] == 0 else 1
    )


if __name__ == "__main__":
    main()
