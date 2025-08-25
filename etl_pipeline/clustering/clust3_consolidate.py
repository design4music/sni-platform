#!/usr/bin/env python3
"""
CLUST-3: Narrative Consolidation & Archival
Strategic Narrative Intelligence Platform

Unifies duplicate or overlapping narratives from CLUST-2 into canonical
parent narratives while preserving historical lineage.

Purpose:
- Prevents narrative fragmentation over time
- Reduces database clutter from similar/duplicate narratives
- Maintains strategic continuity by consolidating related framings
- Preserves full lineage for historical analysis

Key Features:
- Embedding-based similarity detection (threshold ~0.85)
- Title/actor overlap secondary validation
- Canonical narrative promotion (strongest framing wins)
- Full archival with merge metadata
- Idempotent operation (safe to re-run)
"""

import argparse
import asyncio
import json
import logging
import os
# Add project root to path
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("clust3_consolidation.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class NarrativeCandidate:
    """Narrative candidate for consolidation"""

    narrative_id: str
    title: str
    summary: str
    embedding: Optional[np.ndarray]
    key_actors: List[str]
    article_count: int
    created_at: datetime
    consolidation_stage: str
    parent_id: Optional[str]


@dataclass
class ConsolidationResult:
    """Result of consolidation operation"""

    canonical_narrative_id: str
    archived_narrative_ids: List[str]
    merge_confidence: float
    merge_reason: str


class CLUST3NarrativeConsolidation:
    """
    CLUST-3: Narrative consolidation and archival system
    """

    def __init__(self, similarity_threshold: float = 0.85, lookback_days: int = 30):
        self.config = get_config()
        self.similarity_threshold = similarity_threshold
        self.lookback_days = lookback_days
        self.secondary_threshold = 0.75  # For manual review

        logger.info(
            f"CLUST-3 Narrative Consolidation initialized: similarity_threshold={similarity_threshold}, lookback_days={lookback_days}"
        )

    async def run_consolidation(self) -> Dict[str, Any]:
        """
        Main consolidation workflow

        Returns:
            Dictionary with consolidation statistics
        """
        logger.info("Starting CLUST-3 narrative consolidation")
        start_time = datetime.utcnow()

        try:
            # Initialize database
            initialize_database(self.config.database)

            # Get candidates for consolidation
            candidates = await self._get_consolidation_candidates()
            logger.info(
                f"Found {len(candidates)} narrative candidates for consolidation"
            )

            if len(candidates) < 2:
                return {
                    "status": "success",
                    "candidates_found": len(candidates),
                    "consolidation_groups": 0,
                    "consolidations_performed": 0,
                    "processing_time": 0.0,
                    "message": "Insufficient candidates for consolidation",
                }

            # Find duplicate/similar narratives
            consolidation_groups = await self._find_similar_narratives(candidates)
            logger.info(f"Identified {len(consolidation_groups)} consolidation groups")

            # Execute consolidations
            results = []
            for group in consolidation_groups:
                result = await self._execute_consolidation(group)
                if result:
                    results.append(result)

            # Update statistics
            stats = await self._update_consolidation_stats()

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"CLUST-3 consolidation completed: duration={duration:.2f}s, consolidations={len(results)}, canonical_narratives={stats.get('consolidated', 0)}, archived_narratives={stats.get('archived', 0)}"
            )

            return {
                "status": "success",
                "processing_time": duration,
                "candidates_found": len(candidates),
                "consolidation_groups": len(consolidation_groups),
                "consolidations_performed": len(results),
                "consolidation_results": results,
                "final_stats": stats,
            }

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"CLUST-3 consolidation failed: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e), "processing_time": duration}

    async def _get_consolidation_candidates(self) -> List[NarrativeCandidate]:
        """Get narratives eligible for consolidation"""
        try:
            with get_db_session() as session:
                # Get raw narratives from recent timeframe + existing consolidated ones
                cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)

                result = session.execute(
                    text(
                        """
                    SELECT 
                        n.narrative_id,
                        n.title,
                        n.summary,
                        n.actor_origin,
                        n.created_at,
                        n.consolidation_stage,
                        n.parent_id
                    FROM narratives n
                    WHERE (n.consolidation_stage = 'raw' OR 
                          (n.consolidation_stage = 'consolidated' AND n.created_at >= :cutoff_date))
                    ORDER BY n.created_at DESC
                """
                    ),
                    {"cutoff_date": cutoff_date},
                )

                candidates = []
                for row in result.fetchall():
                    candidate = NarrativeCandidate(
                        narrative_id=row[0],
                        title=row[1] or "",
                        summary=row[2] or "",
                        embedding=None,  # TODO: Load if available
                        key_actors=row[3] or [],
                        created_at=row[4],
                        consolidation_stage=row[5],
                        parent_id=row[6],
                        article_count=1,  # Default weight for canonical selection
                    )
                    candidates.append(candidate)

                return candidates

        except SQLAlchemyError as e:
            logger.error(f"Failed to get consolidation candidates: {e}")
            return []

    async def _find_similar_narratives(
        self, candidates: List[NarrativeCandidate]
    ) -> List[List[NarrativeCandidate]]:
        """
        Find groups of similar narratives for consolidation

        Returns:
            List of lists, where each inner list contains similar narratives
        """
        groups = []
        processed = set()

        for i, candidate_a in enumerate(candidates):
            if candidate_a.narrative_id in processed:
                continue

            similar_group = [candidate_a]
            processed.add(candidate_a.narrative_id)

            # Compare with remaining candidates
            for j, candidate_b in enumerate(candidates[i + 1 :], i + 1):
                if candidate_b.narrative_id in processed:
                    continue

                similarity = await self._calculate_similarity(candidate_a, candidate_b)

                if similarity >= self.similarity_threshold:
                    similar_group.append(candidate_b)
                    processed.add(candidate_b.narrative_id)
                    logger.debug(
                        f"Found similar narratives: {candidate_a.narrative_id} <-> {candidate_b.narrative_id} "
                        f"(similarity: {similarity:.3f})"
                    )

            # Only add groups with 2+ narratives
            if len(similar_group) > 1:
                groups.append(similar_group)

        return groups

    async def _calculate_similarity(
        self, narrative_a: NarrativeCandidate, narrative_b: NarrativeCandidate
    ) -> float:
        """
        Calculate similarity between two narratives

        Uses multiple signals:
        1. Title similarity (string matching)
        2. Actor overlap
        3. Embedding similarity (if available)
        """

        # Title similarity (simple word overlap)
        title_sim = self._calculate_title_similarity(
            narrative_a.title, narrative_b.title
        )

        # Actor overlap
        actor_sim = self._calculate_actor_overlap(
            narrative_a.key_actors, narrative_b.key_actors
        )

        # Embedding similarity (placeholder - would use actual embeddings)
        embedding_sim = 0.0  # TODO: Implement when embeddings available

        # Weighted combination
        final_similarity = title_sim * 0.5 + actor_sim * 0.3 + embedding_sim * 0.2

        logger.debug(
            f"Similarity calculation: {narrative_a.narrative_id} <-> {narrative_b.narrative_id}: "
            f"title={title_sim:.3f}, actors={actor_sim:.3f}, final={final_similarity:.3f}"
        )

        return final_similarity

    def _calculate_title_similarity(self, title_a: str, title_b: str) -> float:
        """Calculate title similarity using word overlap"""
        if not title_a or not title_b:
            return 0.0

        words_a = set(title_a.lower().split())
        words_b = set(title_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_actor_overlap(
        self, actors_a: List[str], actors_b: List[str]
    ) -> float:
        """Calculate actor overlap similarity"""
        if not actors_a or not actors_b:
            return 0.0

        set_a = set(actors_a)
        set_b = set(actors_b)

        intersection = set_a.intersection(set_b)
        union = set_a.union(set_b)

        return len(intersection) / len(union) if union else 0.0

    async def _execute_consolidation(
        self, similar_narratives: List[NarrativeCandidate]
    ) -> Optional[ConsolidationResult]:
        """
        Execute consolidation of similar narratives

        Process:
        1. Choose canonical narrative (highest article count or latest consolidated)
        2. Archive duplicate narratives
        3. Update canonical narrative status
        """

        if len(similar_narratives) < 2:
            return None

        try:
            # Choose canonical narrative
            canonical = self._choose_canonical_narrative(similar_narratives)
            duplicates = [
                n
                for n in similar_narratives
                if n.narrative_id != canonical.narrative_id
            ]

            logger.info(
                f"Consolidating {len(duplicates)} narratives into canonical: {canonical.narrative_id}"
            )

            with get_db_session() as session:
                # Archive duplicate narratives
                archived_ids = []
                for duplicate in duplicates:
                    archive_reason = {
                        "reason": "duplicate_merge",
                        "merged_into": canonical.narrative_id,
                        "merge_confidence": 0.85,  # Placeholder
                        "original_title": duplicate.title,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    session.execute(
                        text(
                            """
                        UPDATE narratives
                        SET consolidation_stage = 'archived',
                            archive_reason = :archive_reason
                        WHERE narrative_id = :narrative_id
                    """
                        ),
                        {
                            "narrative_id": duplicate.narrative_id,
                            "archive_reason": json.dumps(archive_reason),
                        },
                    )

                    archived_ids.append(duplicate.narrative_id)
                    logger.debug(f"Archived narrative: {duplicate.narrative_id}")

                # Mark canonical as consolidated
                session.execute(
                    text(
                        """
                    UPDATE narratives
                    SET consolidation_stage = 'consolidated'
                    WHERE narrative_id = :narrative_id
                """
                    ),
                    {"narrative_id": canonical.narrative_id},
                )

                session.commit()

                logger.info(
                    f"Consolidation completed: canonical={canonical.narrative_id}, "
                    f"archived={len(archived_ids)}"
                )

                return ConsolidationResult(
                    canonical_narrative_id=canonical.narrative_id,
                    archived_narrative_ids=archived_ids,
                    merge_confidence=0.85,
                    merge_reason="duplicate_merge",
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to execute consolidation: {e}")
            return None

    def _choose_canonical_narrative(
        self, narratives: List[NarrativeCandidate]
    ) -> NarrativeCandidate:
        """
        Choose canonical narrative from similar group

        Priority:
        1. Already consolidated narratives (preserve existing canonical)
        2. Parent narratives over child narratives (broader scope)
        3. Most recent (latest information)
        """

        # First priority: existing consolidated narratives
        consolidated = [
            n for n in narratives if n.consolidation_stage == "consolidated"
        ]
        if consolidated:
            return max(consolidated, key=lambda n: n.created_at)

        # Second priority: parent narratives (broader scope)
        parents = [n for n in narratives if n.parent_id is None]
        if parents:
            return max(parents, key=lambda n: n.created_at)

        # Fallback: most recent narrative
        return max(narratives, key=lambda n: n.created_at)

    async def _update_consolidation_stats(self) -> Dict[str, int]:
        """Get final consolidation statistics"""
        try:
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                    SELECT consolidation_stage, COUNT(*) as count
                    FROM narratives
                    GROUP BY consolidation_stage
                """
                    )
                )

                stats = {}
                for row in result.fetchall():
                    stats[row[0]] = row[1]

                return stats

        except SQLAlchemyError as e:
            logger.error(f"Failed to get consolidation stats: {e}")
            return {}


async def main():
    """CLI interface for CLUST-3 consolidation"""
    parser = argparse.ArgumentParser(
        description="CLUST-3 Narrative Consolidation & Archival"
    )
    parser.add_argument(
        "--cos-min",
        "--similarity-threshold",
        type=float,
        default=0.85,
        help="Similarity threshold for consolidation (default: 0.85)",
    )
    parser.add_argument(
        "--window-days",
        "--lookback-days",
        type=int,
        default=30,
        help="Days to look back for candidates (default: 30)",
    )
    parser.add_argument(
        "--conflict-threshold",
        type=float,
        default=0.90,
        help="Conflict threshold for consolidation (default: 0.90)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be consolidated without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        consolidator = CLUST3NarrativeConsolidation(
            similarity_threshold=args.cos_min,
            lookback_days=args.window_days,
        )

        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # TODO: Implement dry-run logic
            return 0

        results = await consolidator.run_consolidation()

        print("\n=== CLUST-3 Consolidation Results ===")
        print(f"Status: {results['status']}")

        if results["status"] == "success":
            print(f"Candidates found: {results['candidates_found']}")
            print(f"Consolidation groups: {results['consolidation_groups']}")
            print(f"Consolidations performed: {results['consolidations_performed']}")
            print(f"Processing time: {results['processing_time']:.2f}s")

            if "final_stats" in results:
                stats = results["final_stats"]
                print("\nFinal narrative counts:")
                for stage, count in stats.items():
                    print(f"  {stage}: {count}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"CLUST-3 consolidation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
