"""
Phase 3.5c: Interpretive EF Merging - Merge semantically similar Event Families

Uses LLM micro-prompts to detect if two EFs describe the same strategic narrative,
enabling intelligent merging beyond mechanical ef_key matching.
"""

from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text

from core.config import get_config
from core.database import get_db_session
from core.llm_client import get_llm_client


class EFMerger:
    """
    Phase 3.5c: Interpretive merging of semantically similar Event Families

    Scans EFs with similar theater/event_type and uses micro-prompts to determine
    if they represent facets of the same broader strategic narrative.
    """

    def __init__(self):
        self.config = get_config()
        self.llm_client = get_llm_client()
        self.max_pairs_per_cycle = self.config.p35c_max_pairs_per_cycle

    def find_merge_candidates(
        self, max_pairs: Optional[int] = None, same_theater_only: bool = False
    ) -> List[Tuple[Dict, Dict]]:
        """
        Find candidate EF pairs for potential merging

        Args:
            max_pairs: Maximum number of candidate pairs to return
            same_theater_only: Only consider EFs in same theater

        Returns:
            List of (ef1, ef2) tuples representing candidate pairs
        """
        with get_db_session() as session:
            # Get all active/seed EFs with strategic_purpose
            query = """
            SELECT
                id, title, strategic_purpose, key_actors,
                event_type, primary_theater, source_title_ids, parent_ef_id
            FROM event_families
            WHERE status IN ('seed', 'active')
            AND strategic_purpose IS NOT NULL
            ORDER BY created_at DESC
            """

            efs = session.execute(text(query)).fetchall()

            if len(efs) < 2:
                logger.info("Not enough EFs for merging (need at least 2)")
                return []

            # Build candidate pairs
            candidates = []

            for i in range(len(efs)):
                for j in range(i + 1, len(efs)):
                    ef1 = efs[i]
                    ef2 = efs[j]

                    # Pre-filter: must have same event_type
                    if ef1.event_type != ef2.event_type:
                        continue

                    # Skip siblings (same parent_ef_id) - they were intentionally separated
                    if (
                        ef1.parent_ef_id is not None
                        and ef2.parent_ef_id is not None
                        and ef1.parent_ef_id == ef2.parent_ef_id
                    ):
                        logger.debug(
                            f"Skipping siblings {str(ef1.id)[:8]}... and {str(ef2.id)[:8]}... "
                            f"(split from {str(ef1.parent_ef_id)[:8]}...)"
                        )
                        continue

                    # Optional: must have same theater
                    if same_theater_only and ef1.primary_theater != ef2.primary_theater:
                        continue

                    # Don't merge if theaters are too different (unless both Global)
                    if (
                        ef1.primary_theater != ef2.primary_theater
                        and ef1.primary_theater != "Global"
                        and ef2.primary_theater != "Global"
                    ):
                        continue

                    candidates.append(
                        (
                            {
                                "id": str(ef1.id),
                                "title": ef1.title,
                                "strategic_purpose": ef1.strategic_purpose,
                                "event_type": ef1.event_type,
                                "theater": ef1.primary_theater,
                                "source_title_ids": ef1.source_title_ids or [],
                            },
                            {
                                "id": str(ef2.id),
                                "title": ef2.title,
                                "strategic_purpose": ef2.strategic_purpose,
                                "event_type": ef2.event_type,
                                "theater": ef2.primary_theater,
                                "source_title_ids": ef2.source_title_ids or [],
                            },
                        )
                    )

                    if max_pairs and len(candidates) >= max_pairs:
                        break

                if max_pairs and len(candidates) >= max_pairs:
                    break

            logger.info(f"Found {len(candidates)} candidate EF pairs for merging")
            return candidates

    def should_merge_efs(self, ef1: Dict, ef2: Dict) -> Tuple[bool, Optional[str]]:
        """
        Use LLM micro-prompt to determine if two EFs should merge

        Args:
            ef1: First EF dict with strategic_purpose
            ef2: Second EF dict with strategic_purpose

        Returns:
            Tuple of (should_merge: bool, reason: Optional[str])
        """
        from core.llm_client import build_ef_merge_prompt

        system_prompt, user_prompt = build_ef_merge_prompt(
            ef1["strategic_purpose"], ef2["strategic_purpose"]
        )

        try:
            response = self.llm_client._call_llm_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.p35c_merge_max_tokens,
                temperature=self.config.p35c_merge_temperature,
            )

            answer = response.strip().upper()
            should_merge = "YES" in answer

            reason = f"LLM decision: {answer}"
            return should_merge, reason

        except Exception as e:
            logger.error(f"Merge micro-prompt failed: {e}")
            return False, f"Error: {e}"

    def merge_event_families(self, ef1_id: str, ef2_id: str, reason: str) -> bool:
        """
        Merge two Event Families in database

        Merges ef2 into ef1 (ef1 becomes the primary, ef2 marked as merged)

        Args:
            ef1_id: Primary EF to keep
            ef2_id: Secondary EF to merge into primary
            reason: Reason for merge

        Returns:
            True if successful
        """
        try:
            with get_db_session() as session:
                # Get both EFs
                ef1 = session.execute(
                    text("SELECT * FROM event_families WHERE id = :ef_id"),
                    {"ef_id": ef1_id},
                ).fetchone()

                ef2 = session.execute(
                    text("SELECT * FROM event_families WHERE id = :ef_id"),
                    {"ef_id": ef2_id},
                ).fetchone()

                if not ef1 or not ef2:
                    logger.error("One or both EFs not found")
                    return False

                # Merge title lists
                ef1_titles = ef1.source_title_ids or []
                ef2_titles = ef2.source_title_ids or []
                merged_titles = list(set(ef1_titles + ef2_titles))

                # Update ef1 with merged data
                update_query = """
                UPDATE event_families
                SET
                    source_title_ids = :merged_titles,
                    updated_at = NOW(),
                    processing_notes = CONCAT(
                        COALESCE(processing_notes, ''),
                        '; Merged with EF ',
                        :ef2_id,
                        ' - Reason: ',
                        :reason
                    )
                WHERE id = :ef1_id
                """

                session.execute(
                    text(update_query),
                    {
                        "merged_titles": merged_titles,
                        "ef2_id": ef2_id,
                        "reason": reason[:200],  # Truncate
                        "ef1_id": ef1_id,
                    },
                )

                # Mark ef2 as merged
                merge_query = """
                UPDATE event_families
                SET
                    status = 'merged',
                    merged_into = :ef1_id,
                    merge_rationale = :reason,
                    updated_at = NOW()
                WHERE id = :ef2_id
                """

                session.execute(
                    text(merge_query),
                    {
                        "ef1_id": ef1_id,
                        "reason": reason[:500],
                        "ef2_id": ef2_id,
                    },
                )

                # Update all titles from ef2 to point to ef1
                titles_update = """
                UPDATE titles
                SET event_family_id = :ef1_id
                WHERE event_family_id = :ef2_id
                """

                result = session.execute(
                    text(titles_update), {"ef1_id": ef1_id, "ef2_id": ef2_id}
                )

                titles_moved = result.rowcount

                logger.info(
                    f"Merged EF {ef2_id[:8]}... into {ef1_id[:8]}... "
                    f"({titles_moved} titles moved, {len(merged_titles)} total titles)"
                )

                return True

        except Exception as e:
            logger.error(f"Failed to merge EFs: {e}")
            return False

    def run_merge_cycle(
        self,
        max_pairs: int = 20,
        same_theater_only: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """
        Run a complete merge cycle on existing EFs

        Args:
            max_pairs: Maximum pairs to evaluate
            same_theater_only: Only consider same-theater pairs
            dry_run: If True, only report what would be merged

        Returns:
            Dict with merge statistics
        """
        logger.info("=== PHASE 3.5c: INTERPRETIVE EF MERGING ===")

        # Find candidates
        candidates = self.find_merge_candidates(
            max_pairs=max_pairs, same_theater_only=same_theater_only
        )

        if not candidates:
            logger.info("No merge candidates found")
            return {"evaluated": 0, "merged": 0, "skipped": 0}

        evaluated = 0
        merged = 0
        skipped = 0

        for ef1, ef2 in candidates:
            evaluated += 1

            logger.debug(
                f"Evaluating pair {evaluated}/{len(candidates)}: "
                f"{ef1['title'][:40]}... vs {ef2['title'][:40]}..."
            )

            should_merge, reason = self.should_merge_efs(ef1, ef2)

            if should_merge:
                logger.info(
                    f"MERGE RECOMMENDED: {ef1['id'][:8]}... + {ef2['id'][:8]}... "
                    f"({reason})"
                )

                if not dry_run:
                    success = self.merge_event_families(ef1["id"], ef2["id"], reason)
                    if success:
                        merged += 1
                else:
                    merged += 1  # Count as merged for dry run stats
            else:
                skipped += 1

        logger.info(
            f"Merge cycle complete: {evaluated} pairs evaluated, "
            f"{merged} merged, {skipped} skipped"
        )

        return {
            "evaluated": evaluated,
            "merged": merged,
            "skipped": skipped,
        }


# Global merger instance
_ef_merger: Optional[EFMerger] = None


def get_ef_merger() -> EFMerger:
    """Get global EF merger instance"""
    global _ef_merger
    if _ef_merger is None:
        _ef_merger = EFMerger()
    return _ef_merger


# CLI interface
def run_ef_merging(max_pairs: int = 20, dry_run: bool = False):
    """
    Run Phase 3.5c EF merging on existing Event Families

    Args:
        max_pairs: Maximum pairs to evaluate
        dry_run: If True, only report what would be merged
    """
    merger = EFMerger()
    results = merger.run_merge_cycle(max_pairs=max_pairs, dry_run=dry_run)

    print("\n" + "=" * 60)
    print("PHASE 3.5c: INTERPRETIVE EF MERGING RESULTS")
    print("=" * 60)
    print(f"Pairs evaluated: {results['evaluated']}")
    print(f"EFs merged: {results['merged']}")
    print(f"Pairs skipped: {results['skipped']}")
    if dry_run:
        print("\n[DRY RUN - No changes made]")
    print("=" * 60)

    return results


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv
    max_pairs = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 20

    run_ef_merging(max_pairs, dry_run)
