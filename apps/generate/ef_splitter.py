"""
Phase 3.5d: Interpretive EF Splitting - Split mixed-narrative Event Families

Uses LLM to detect when an EF contains multiple distinct strategic narratives
and splits them into coherent sub-EFs.
"""

import json
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text

from core.config import get_config
from core.database import get_db_session
from core.llm_client import get_llm_client


class EFSplitter:
    """
    Phase 3.5d: Interpretive splitting of mixed-narrative Event Families

    Scans EFs with >N titles and uses LLM to determine if they contain
    multiple distinct strategic narratives that should be separated.
    """

    def __init__(self):
        self.config = get_config()
        self.llm_client = get_llm_client()
        self.min_titles_for_split = self.config.p35d_min_titles_for_split
        self.max_efs_per_cycle = self.config.p35d_max_efs_per_cycle

    def find_split_candidates(self, max_efs: Optional[int] = None) -> List[Dict]:
        """
        Find candidate EFs for potential splitting

        Args:
            max_efs: Maximum number of EFs to return

        Returns:
            List of EF dicts with id, title, strategic_purpose, source_title_ids
        """
        with get_db_session() as session:
            # Get EFs with more than threshold titles
            query = """
            SELECT
                ef.id,
                ef.title,
                ef.strategic_purpose,
                ef.event_type,
                ef.primary_theater,
                ef.key_actors,
                ef.source_title_ids,
                ARRAY_LENGTH(ef.source_title_ids, 1) as title_count
            FROM event_families ef
            WHERE ef.status IN ('seed', 'active')
            AND ARRAY_LENGTH(ef.source_title_ids, 1) > :min_titles
            ORDER BY ARRAY_LENGTH(ef.source_title_ids, 1) DESC
            """

            if max_efs:
                query += f" LIMIT {max_efs}"

            efs = session.execute(
                text(query), {"min_titles": self.min_titles_for_split}
            ).fetchall()

            if not efs:
                logger.info(
                    f"No EFs with >{self.min_titles_for_split} titles found for splitting"
                )
                return []

            candidates = []
            for ef in efs:
                # Get actual title texts for LLM analysis
                title_ids_str = ",".join([f"'{tid}'" for tid in ef.source_title_ids])
                titles_query = f"""
                SELECT id, title_display as text
                FROM titles
                WHERE id::text IN ({title_ids_str})
                ORDER BY pubdate_utc DESC
                """

                titles = session.execute(text(titles_query)).fetchall()

                candidates.append(
                    {
                        "id": str(ef.id),
                        "title": ef.title,
                        "strategic_purpose": ef.strategic_purpose,
                        "event_type": ef.event_type,
                        "theater": ef.primary_theater,
                        "key_actors": ef.key_actors or [],
                        "source_title_ids": ef.source_title_ids,
                        "title_count": ef.title_count,
                        "titles": [{"id": str(t.id), "text": t.text} for t in titles],
                    }
                )

            logger.info(
                f"Found {len(candidates)} EFs with >{self.min_titles_for_split} titles"
            )

            return candidates

    def should_split_ef(self, ef_data: Dict) -> Tuple[bool, Optional[List[Dict]]]:
        """
        Use LLM to determine if EF should be split

        Args:
            ef_data: EF dict with titles

        Returns:
            Tuple of (should_split: bool, split_plan: Optional[List[Dict]])
            split_plan is list of narrative groups if splitting
        """
        system_prompt = """You are a strategic intelligence analyst. Analyze a collection of headlines to determine if they describe ONE cohesive strategic narrative or MULTIPLE distinct narratives that should be separated.

Your task:
1. Review all headlines
2. Determine if they describe:
   - ONE narrative (coherent story/theme)
   - MULTIPLE narratives (distinct stories mixed together)

If MULTIPLE narratives, identify them and group the headlines accordingly.

IMPORTANT - Narrative Naming:
- Create SPECIFIC, DESCRIPTIVE titles that include:
  * Specific actors/entities involved (e.g., "Israel", "Hamas", "Trump")
  * Theater/location context (e.g., "Gaza", "Ukraine", "United States")
  * Strategic action or purpose (e.g., "Ceasefire Implementation", "Military Operations")
- BAD: "Economic & Market Reactions" (too generic)
- GOOD: "Gaza Economic Impact: Oil and Stock Market Reactions to Israel-Hamas Ceasefire"
- BAD: "Government Shutdown Strategy"
- GOOD: "Trump Administration Government Shutdown to Advance Policy Objectives"

Respond in JSON format:
{
  "should_split": true/false,
  "rationale": "brief explanation",
  "narratives": [
    {
      "narrative_name": "Specific, descriptive narrative title with actors and theater",
      "strategic_purpose": "One-sentence strategic purpose",
      "key_actors": ["Actor1", "Actor2", ...],
      "title_ids": ["uuid1", "uuid2", ...]
    },
    ...
  ]
}

For key_actors:
- Extract the primary actors/entities relevant to THIS specific narrative
- Include countries, organizations, leaders, groups
- Only include actors that are central to this narrative's headlines
- Parent EF may have been over-merged, so don't include irrelevant actors

If should_split is false, narratives can be empty array."""

        # Build title list for LLM
        title_list = "\n".join(
            [
                f"{i+1}. [{t['id'][:8]}] {t['text']}"
                for i, t in enumerate(ef_data["titles"])
            ]
        )

        user_prompt = f"""Event Family: {ef_data['title']}
Strategic Purpose: {ef_data['strategic_purpose']}

Headlines ({len(ef_data['titles'])} total):
{title_list}

Analyze these headlines. Do they describe ONE cohesive narrative or MULTIPLE distinct narratives?

JSON Response:"""

        try:
            response = self.llm_client._call_llm_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.p35d_split_max_tokens,
                temperature=self.config.p35d_split_temperature,
            )

            # Log raw response for debugging
            logger.debug(f"Raw LLM response: {response[:500]}...")

            # Try to extract JSON from response (might have markdown formatting)
            response_clean = response.strip()

            # Remove markdown code blocks if present
            if "```json" in response_clean:
                response_clean = (
                    response_clean.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0].strip()

            # Parse JSON response
            result = json.loads(response_clean)

            should_split = result.get("should_split", False)
            rationale = result.get("rationale", "")
            narratives = result.get("narratives", [])

            if should_split and len(narratives) >= 2:
                # Map shortened UUIDs back to full UUIDs
                # LLM sees first 8 chars for readability, we need to expand them
                id_mapping = {t["id"][:8]: t["id"] for t in ef_data["titles"]}

                for narrative in narratives:
                    full_ids = []
                    for short_id in narrative["title_ids"]:
                        # Try exact match first (if LLM returned full UUID)
                        if short_id in [t["id"] for t in ef_data["titles"]]:
                            full_ids.append(short_id)
                        # Otherwise expand shortened ID
                        elif short_id in id_mapping:
                            full_ids.append(id_mapping[short_id])
                        else:
                            logger.warning(f"Unknown title ID: {short_id}")
                    narrative["title_ids"] = full_ids

                logger.info(
                    f"EF '{ef_data['title'][:40]}...' should split into {len(narratives)} narratives: {rationale}"
                )
                return True, narratives
            else:
                logger.debug(
                    f"EF '{ef_data['title'][:40]}...' is cohesive: {rationale}"
                )
                return False, None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse split response: {e}")
            logger.error(f"Response was: {response[:200]}...")
            return False, None
        except Exception as e:
            logger.error(f"Split micro-prompt failed: {e}")
            return False, None

    def split_event_family(
        self, ef_id: str, split_plan: List[Dict], original_ef_data: Dict
    ) -> bool:
        """
        Split an Event Family into multiple EFs based on split plan

        Args:
            ef_id: Original EF ID to split
            split_plan: List of narrative dicts from LLM
            original_ef_data: Original EF data

        Returns:
            True if successful
        """
        try:
            with get_db_session() as session:
                # Import models
                import uuid
                from datetime import datetime

                from apps.generate.models import EventFamily

                # Create new EFs for each narrative
                new_ef_ids = []

                for narrative in split_plan:
                    # Get key_actors from LLM response, fallback to parent EF's actors
                    key_actors = narrative.get(
                        "key_actors", original_ef_data.get("key_actors", [])
                    )

                    # Create new EF
                    new_ef = EventFamily(
                        id=str(uuid.uuid4()),
                        title=narrative["narrative_name"],
                        summary=narrative["narrative_name"],  # Will be enriched later
                        strategic_purpose=narrative["strategic_purpose"],
                        key_actors=key_actors,
                        event_type=original_ef_data["event_type"],
                        primary_theater=original_ef_data["theater"],
                        source_title_ids=narrative["title_ids"],
                        status="seed",  # New split EFs start as seed
                        parent_ef_id=ef_id,  # Track parent for sibling detection
                        coherence_reason=f"Split from EF {ef_id[:8]}... - {narrative['narrative_name']}",
                        processing_notes=f"P3.5d: Split from mixed EF {ef_id[:8]}...",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    # Generate ef_key
                    from apps.generate.ef_key import generate_ef_key

                    new_ef.ef_key = generate_ef_key(
                        new_ef.key_actors, new_ef.primary_theater, new_ef.event_type
                    )

                    # Insert new EF
                    insert_query = """
                    INSERT INTO event_families (
                        id, title, summary, strategic_purpose, key_actors, event_type, primary_theater,
                        ef_key, status, parent_ef_id, source_title_ids, coherence_reason, processing_notes,
                        created_at, updated_at
                    ) VALUES (
                        :id, :title, :summary, :strategic_purpose, :key_actors, :event_type, :primary_theater,
                        :ef_key, :status, :parent_ef_id, :source_title_ids, :coherence_reason, :processing_notes,
                        :created_at, :updated_at
                    )
                    """

                    session.execute(
                        text(insert_query),
                        {
                            "id": new_ef.id,
                            "title": new_ef.title,
                            "summary": new_ef.summary,
                            "strategic_purpose": new_ef.strategic_purpose,
                            "key_actors": new_ef.key_actors,
                            "event_type": new_ef.event_type,
                            "primary_theater": new_ef.primary_theater,
                            "ef_key": new_ef.ef_key,
                            "status": new_ef.status,
                            "parent_ef_id": new_ef.parent_ef_id,
                            "source_title_ids": new_ef.source_title_ids,
                            "coherence_reason": new_ef.coherence_reason,
                            "processing_notes": new_ef.processing_notes,
                            "created_at": new_ef.created_at,
                            "updated_at": new_ef.updated_at,
                        },
                    )

                    new_ef_ids.append(new_ef.id)

                    # Update titles to point to new EF
                    title_ids_list = (
                        "ARRAY["
                        + ",".join([f"'{tid}'::uuid" for tid in narrative["title_ids"]])
                        + "]"
                    )

                    update_titles_query = f"""
                    UPDATE titles
                    SET event_family_id = :new_ef_id,
                        processing_status = 'assigned'
                    WHERE id = ANY({title_ids_list})
                    """

                    session.execute(text(update_titles_query), {"new_ef_id": new_ef.id})

                    logger.info(
                        f"Created split EF {new_ef.id[:8]}...: '{new_ef.title}' "
                        f"({len(narrative['title_ids'])} titles)"
                    )

                # Mark original EF as 'split'
                split_note = (
                    f"P3.5d: Split into {len(split_plan)} narratives: "
                    + ", ".join([n["narrative_name"][:30] for n in split_plan])
                )

                update_original_query = """
                UPDATE event_families
                SET status = 'split',
                    processing_notes = CONCAT(COALESCE(processing_notes, ''), '; ', :split_note),
                    updated_at = NOW()
                WHERE id = :ef_id
                """

                session.execute(
                    text(update_original_query),
                    {"ef_id": ef_id, "split_note": split_note},
                )

                logger.info(
                    f"Marked original EF {ef_id[:8]}... as 'split' "
                    f"(created {len(new_ef_ids)} new EFs)"
                )

                session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to split EF: {e}")
            return False

    def run_split_cycle(
        self, max_efs: Optional[int] = None, dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Run a complete split cycle on existing EFs

        Args:
            max_efs: Maximum EFs to evaluate
            dry_run: If True, only report what would be split

        Returns:
            Dict with split statistics
        """
        logger.info("=== PHASE 3.5d: INTERPRETIVE EF SPLITTING ===")

        # Find candidates
        candidates = self.find_split_candidates(max_efs or self.max_efs_per_cycle)

        if not candidates:
            logger.info("No split candidates found")
            return {"evaluated": 0, "split": 0, "kept": 0}

        evaluated = 0
        split_count = 0
        kept_count = 0

        for ef_data in candidates:
            evaluated += 1

            logger.debug(
                f"Evaluating EF {evaluated}/{len(candidates)}: "
                f"{ef_data['title'][:40]}... ({ef_data['title_count']} titles)"
            )

            should_split, split_plan = self.should_split_ef(ef_data)

            if should_split and split_plan:
                logger.info(
                    f"SPLIT RECOMMENDED: {ef_data['id'][:8]}... into {len(split_plan)} narratives"
                )

                for i, narrative in enumerate(split_plan):
                    logger.info(
                        f"  Narrative {i+1}: '{narrative['narrative_name']}' "
                        f"({len(narrative['title_ids'])} titles)"
                    )

                if not dry_run:
                    success = self.split_event_family(
                        ef_data["id"], split_plan, ef_data
                    )
                    if success:
                        split_count += 1
                else:
                    split_count += 1  # Count as split for dry run stats
            else:
                kept_count += 1

        logger.info(
            f"Split cycle complete: {evaluated} EFs evaluated, "
            f"{split_count} split, {kept_count} kept"
        )

        return {
            "evaluated": evaluated,
            "split": split_count,
            "kept": kept_count,
        }


# Global splitter instance
_ef_splitter: Optional[EFSplitter] = None


def get_ef_splitter() -> EFSplitter:
    """Get global EF splitter instance"""
    global _ef_splitter
    if _ef_splitter is None:
        _ef_splitter = EFSplitter()
    return _ef_splitter


# CLI interface
def run_ef_splitting(max_efs: int = 50, dry_run: bool = False):
    """
    Run Phase 3.5d EF splitting on existing Event Families

    Args:
        max_efs: Maximum EFs to evaluate
        dry_run: If True, only report what would be split
    """
    splitter = EFSplitter()
    results = splitter.run_split_cycle(max_efs=max_efs, dry_run=dry_run)

    print("\n" + "=" * 60)
    print("PHASE 3.5d: INTERPRETIVE EF SPLITTING RESULTS")
    print("=" * 60)
    print(f"EFs evaluated: {results['evaluated']}")
    print(f"EFs split: {results['split']}")
    print(f"EFs kept (cohesive): {results['kept']}")
    if dry_run:
        print("\n[DRY RUN - No changes made]")
    print("=" * 60)

    return results


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv
    max_efs = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 50

    run_ef_splitting(max_efs, dry_run)
