"""
Phase 3.5: Thematic Validation - Micro-prompt EF assignment

Uses strategic_purpose as semantic anchor to validate if new titles
belong to existing Event Families using cheap YES/NO micro-prompts.
"""

from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text

from apps.generate.theater_inference import infer_theater_from_entities
from core.config import get_config
from core.database import get_db_session
from core.llm_client import get_llm_client


class ThematicValidator:
    """
    Phase 3.5: Continuous thematic validation for EF assignment

    Pre-filters candidate EFs using:
    - event_type match (required)
    - EITHER same theater OR 50%+ actor overlap

    Then uses micro-prompts to validate thematic fit.
    """

    def __init__(self):
        self.config = get_config()
        self.llm_client = get_llm_client()

    def process_unassigned_titles(
        self, max_titles: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Process unassigned strategic titles through thematic validation

        Args:
            max_titles: Maximum number of titles to process

        Returns:
            Dict with processing stats
        """
        logger.info("=== PHASE 3.5: THEMATIC VALIDATION ===")

        with get_db_session() as session:
            # Get unassigned strategic titles
            query = """
            SELECT id, title_display, entities, gate_keep
            FROM titles
            WHERE gate_keep = true
            AND event_family_id IS NULL
            """

            if max_titles:
                query += f" LIMIT {max_titles}"

            titles = session.execute(text(query)).fetchall()

            if not titles:
                logger.info("No unassigned strategic titles found")
                return {"processed": 0, "assigned": 0, "skipped": 0}

            logger.info(f"Processing {len(titles)} unassigned strategic titles")

        assigned_count = 0
        skipped_count = 0

        for title_row in titles:
            title_id = str(title_row.id)
            title_text = title_row.title_display
            title_entities = (
                title_row.entities if isinstance(title_row.entities, list) else []
            )

            # Infer event_type and theater for this title
            # (In real pipeline, these would come from Phase 2 metadata)
            event_type, theater = self._infer_title_metadata(title_entities)

            # Get candidate EFs
            candidates = self._get_candidate_efs(title_entities, event_type, theater)

            if not candidates:
                logger.debug(
                    f"No candidate EFs for title {title_id[:8]}... - will create new seed"
                )
                skipped_count += 1
                continue

            # Try to assign to best matching EF
            assigned_ef_id = self._validate_and_assign_title(
                title_id, title_text, title_entities, candidates
            )

            if assigned_ef_id:
                assigned_count += 1
                logger.info(
                    f"Assigned title {title_id[:8]}... to EF {assigned_ef_id[:8]}..."
                )
            else:
                skipped_count += 1

        logger.info(
            f"Phase 3.5 complete: {assigned_count} assigned, {skipped_count} skipped (will create new seeds)"
        )

        return {
            "processed": len(titles),
            "assigned": assigned_count,
            "skipped": skipped_count,
        }

    def _infer_title_metadata(self, title_entities: List[str]) -> Tuple[str, str]:
        """
        Infer event_type and theater for a title

        For now, uses heuristics. In production, would come from Phase 2.
        """
        # Infer theater from entities
        theater, _ = infer_theater_from_entities(title_entities, None)

        # Default event type (in production, would be determined by Phase 2)
        event_type = "Strategy/Tactics"  # Fallback

        return event_type, theater

    def _get_candidate_efs(
        self,
        title_entities: List[str],
        event_type: str,
        theater: str,
    ) -> List[Dict]:
        """
        Pre-filter candidate EFs using:
        1. event_type match (REQUIRED)
        2. EITHER same theater OR 50%+ actor overlap

        Returns:
            List of candidate EF dicts with id, title, strategic_purpose, key_actors, theater
        """
        with get_db_session() as session:
            # Get all active/seed EFs with matching event_type
            query = """
            SELECT id, title, strategic_purpose, key_actors, primary_theater
            FROM event_families
            WHERE event_type = :event_type
            AND status IN ('seed', 'active')
            AND strategic_purpose IS NOT NULL
            ORDER BY created_at DESC
            """

            efs = session.execute(text(query), {"event_type": event_type}).fetchall()

            if not efs:
                return []

            candidates = []

            for ef in efs:
                ef_id = str(ef.id)
                ef_theater = ef.primary_theater
                ef_actors = ef.key_actors if ef.key_actors else []

                # Check 1: Same theater?
                if ef_theater == theater:
                    candidates.append(
                        {
                            "id": ef_id,
                            "title": ef.title,
                            "strategic_purpose": ef.strategic_purpose,
                            "key_actors": ef_actors,
                            "theater": ef_theater,
                            "match_reason": "same_theater",
                        }
                    )
                    continue

                # Check 2: 50%+ actor overlap?
                overlap = self._calculate_actor_overlap(ef_actors, title_entities)
                if overlap >= 0.5:
                    candidates.append(
                        {
                            "id": ef_id,
                            "title": ef.title,
                            "strategic_purpose": ef.strategic_purpose,
                            "key_actors": ef_actors,
                            "theater": ef_theater,
                            "match_reason": f"actor_overlap_{overlap:.0%}",
                        }
                    )

            logger.debug(
                f"Found {len(candidates)} candidate EFs for event_type={event_type}, theater={theater}"
            )

            return candidates

    def _calculate_actor_overlap(
        self, ef_actors: List[str], title_entities: List[str]
    ) -> float:
        """
        Calculate percentage of EF actors that appear in title entities

        Args:
            ef_actors: List of actors from existing EF
            title_entities: List of entities from new title

        Returns:
            Overlap percentage (0.0 to 1.0)
        """
        if not ef_actors:
            return 0.0

        ef_set = set(actor.lower() for actor in ef_actors)
        title_set = set(entity.lower() for entity in title_entities)

        overlap_count = len(ef_set.intersection(title_set))
        overlap_pct = overlap_count / len(ef_set)

        return overlap_pct

    def _validate_and_assign_title(
        self,
        title_id: str,
        title_text: str,
        title_entities: List[str],
        candidates: List[Dict],
    ) -> Optional[str]:
        """
        Use micro-prompts to validate if title fits any candidate EF

        Args:
            title_id: Title UUID
            title_text: Title text
            title_entities: List of entities in title
            candidates: List of candidate EF dicts

        Returns:
            EF ID if assigned, None otherwise
        """
        # Sort candidates by match_reason priority
        # Priority: same_theater > higher actor_overlap
        candidates.sort(
            key=lambda c: (
                c["match_reason"] == "same_theater",
                (
                    float(c["match_reason"].split("_")[-1].rstrip("%")) / 100
                    if "overlap" in c["match_reason"]
                    else 0
                ),
            ),
            reverse=True,
        )

        # Try each candidate with micro-prompt
        for candidate in candidates[:5]:  # Limit to top 5 candidates
            ef_id = candidate["id"]
            strategic_purpose = candidate["strategic_purpose"]

            # Micro-prompt: Does this title fit the strategic purpose?
            fits = self._check_thematic_fit(title_text, strategic_purpose)

            if fits:
                # Assign title to this EF
                success = self._assign_title_to_ef(title_id, ef_id)
                if success:
                    logger.debug(
                        f"Title fits EF {ef_id[:8]}... via {candidate['match_reason']}"
                    )
                    return ef_id

        return None

    def _check_thematic_fit(self, title_text: str, strategic_purpose: str) -> bool:
        """
        Micro-prompt: Does this headline fit the strategic purpose?

        Args:
            title_text: Headline text
            strategic_purpose: EF's strategic purpose

        Returns:
            True if fits, False otherwise
        """
        system_prompt = """You are a strategic news analyst. Your job is to determine if a headline fits a given strategic narrative.

Answer with ONLY "YES" or "NO" - no explanation needed."""

        user_prompt = f"""Strategic Purpose: {strategic_purpose}

Headline: {title_text}

Does this headline fit the strategic purpose above?

Answer: """

        try:
            response = self.llm_client._call_llm_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.p35b_assignment_max_tokens,
                temperature=self.config.p35b_assignment_temperature,
            )

            answer = response.strip().upper()
            return "YES" in answer

        except Exception as e:
            logger.error(f"Micro-prompt failed: {e}")
            return False

    def _assign_title_to_ef(self, title_id: str, ef_id: str) -> bool:
        """
        Assign title to Event Family in database

        Args:
            title_id: Title UUID
            ef_id: Event Family UUID

        Returns:
            True if successful
        """
        try:
            with get_db_session() as session:
                # Update title with EF assignment
                update_query = """
                UPDATE titles
                SET event_family_id = :ef_id
                WHERE id = :title_id
                AND gate_keep = true
                AND event_family_id IS NULL
                """

                result = session.execute(
                    text(update_query), {"ef_id": ef_id, "title_id": title_id}
                )

                if result.rowcount > 0:
                    # Update EF's source_title_ids
                    update_ef_query = """
                    UPDATE event_families
                    SET source_title_ids = array_append(source_title_ids, :title_id::uuid),
                        updated_at = NOW()
                    WHERE id = :ef_id
                    """

                    session.execute(
                        text(update_ef_query), {"ef_id": ef_id, "title_id": title_id}
                    )

                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to assign title to EF: {e}")
            return False


# CLI interface
def run_thematic_validation(max_titles: int = 50):
    """
    Run Phase 3.5 thematic validation on unassigned titles

    Args:
        max_titles: Maximum number of titles to process
    """
    validator = ThematicValidator()
    results = validator.process_unassigned_titles(max_titles)

    print("\n" + "=" * 60)
    print("PHASE 3.5: THEMATIC VALIDATION RESULTS")
    print("=" * 60)
    print(f"Titles processed: {results['processed']}")
    print(f"Assigned to existing EFs: {results['assigned']}")
    print(f"Skipped (will create new EFs): {results['skipped']}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    import sys

    max_titles = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_thematic_validation(max_titles)
