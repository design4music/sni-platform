"""
Phase 5: Framed Narratives Generation
Analyzes how different outlets frame the same Event Family
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from loguru import logger
from sqlalchemy import text

from apps.generate.database import get_gen1_database
from apps.generate.models import FramedNarrative
from core.config import get_config
from core.database import get_db_session
from core.llm_client import get_llm_client


class FramingProcessor:
    """Process Event Families to extract distinct narrative framings"""

    def __init__(self):
        self.config = get_config()
        self.db = get_gen1_database()
        self.llm = get_llm_client()

    def get_framing_queue(self, limit: Optional[int] = None) -> List[dict]:
        """
        Get Event Families that need framing analysis.

        Returns only 'active' EFs that don't have framed narratives yet.
        Processes even single-title EFs (strong Russia vs. World narratives).

        Args:
            limit: Maximum number of EFs to return (default: config.phase_5_max_items)

        Returns:
            List of dicts with {id, title, summary, source_title_ids}
        """
        limit = limit or self.config.phase_5_max_items or 50

        query = text(
            """
            SELECT
                ef.id,
                ef.title,
                ef.summary,
                ef.source_title_ids,
                array_length(ef.source_title_ids, 1) as title_count
            FROM event_families ef
            WHERE ef.status = 'active'  -- Only enriched, high-quality EFs
              AND ef.source_title_ids IS NOT NULL
              AND array_length(ef.source_title_ids, 1) >= :min_titles
              AND NOT EXISTS (
                  SELECT 1
                  FROM framed_narratives fn
                  WHERE fn.event_family_id = ef.id
              )  -- Skip EFs that already have framing
            ORDER BY ef.created_at DESC
            LIMIT :limit
        """
        )

        with get_db_session() as session:
            result = session.execute(
                query,
                {
                    "min_titles": self.config.framing_min_titles,
                    "limit": limit,
                },
            )
            rows = result.fetchall()

        queue = []
        for row in rows:
            queue.append(
                {
                    "id": str(row.id),
                    "title": row.title,
                    "summary": row.summary,
                    "source_title_ids": row.source_title_ids,
                    "title_count": row.title_count,
                }
            )

        logger.info(
            f"Framing queue: {len(queue)} active EFs ready for narrative analysis "
            f"(min_titles={self.config.framing_min_titles})"
        )
        return queue

    def get_title_texts(self, title_ids: List[str]) -> List[dict]:
        """
        Fetch title texts and metadata for framing analysis.

        Args:
            title_ids: List of title UUIDs

        Returns:
            List of dicts with {id, title_norm, publisher_domain}
        """
        if not title_ids:
            return []

        # Build safe query with placeholders
        placeholders = ",".join([f"'{tid}'::uuid" for tid in title_ids])
        query = text(
            f"""
            SELECT
                id,
                title_norm,
                publisher_domain
            FROM titles
            WHERE id IN ({placeholders})
        """
        )

        with get_db_session() as session:
            result = session.execute(query)
            rows = result.fetchall()

        titles = []
        for row in rows:
            titles.append(
                {
                    "id": str(row.id),
                    "title_norm": row.title_norm,
                    "publisher_domain": row.publisher_domain,
                }
            )

        return titles

    async def analyze_framing(
        self, ef_data: dict, titles: List[dict]
    ) -> List[FramedNarrative]:
        """
        Use LLM to extract distinct narrative framings from titles.

        Args:
            ef_data: Event Family metadata
            titles: List of title dicts with text and metadata

        Returns:
            List of FramedNarrative objects (1-3 frames maximum)
        """
        from apps.generate.models import EventFamily, LLMFramedNarrativeRequest

        try:
            # Build EventFamily object (minimal required fields)
            event_family = EventFamily(
                id=ef_data["id"],
                title=ef_data["title"],
                summary=ef_data["summary"],
                key_actors=[],  # Not critical for framing analysis
                event_type="",  # Not critical for framing analysis
                primary_theater=None,
                source_title_ids=ef_data.get("source_title_ids", []),
                status="active",
                coherence_reason="Active EF for framing analysis",  # Required field
            )

            # Build titles context for LLM
            titles_context = []
            for t in titles:
                titles_context.append(
                    {
                        "id": t["id"],
                        "text": t["title_norm"],
                        "source": t.get("publisher_domain", "Unknown"),
                    }
                )

            # Build LLM request
            request = LLMFramedNarrativeRequest(
                event_family=event_family,
                titles_context=titles_context,
                framing_instructions=(
                    "Extract distinct narrative framings. "
                    "Each frame MUST cite 2-6 specific headline UUIDs with quotes. "
                    "Focus on evaluative/causal framing differences."
                ),
                max_narratives=self.config.framing_max_narratives,
            )

            # Call LLM
            response = await self.llm.generate_framed_narratives(request)

            # Convert response to FramedNarrative objects
            narratives = []
            for frame_data in response.framed_narratives[
                : self.config.framing_max_narratives
            ]:
                try:
                    narrative = FramedNarrative(
                        event_family_id=ef_data["id"],
                        frame_type=frame_data.get("frame_type", "neutral"),
                        frame_description=frame_data.get("frame_description", ""),
                        stance_summary=frame_data.get("stance_summary", ""),
                        supporting_headlines=frame_data.get("supporting_headlines", []),
                        supporting_title_ids=frame_data.get("supporting_title_ids", []),
                        key_language=frame_data.get("key_language", []),
                        prevalence_score=float(frame_data.get("prevalence_score", 0.5)),
                        evidence_quality=float(frame_data.get("evidence_quality", 0.5)),
                    )
                    narratives.append(narrative)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(
                        f"Failed to parse frame for EF {ef_data['id'][:8]}: {e}"
                    )
                    continue

            logger.info(
                f"Extracted {len(narratives)} frames for EF {ef_data['id'][:8]}"
            )
            return narratives

        except Exception as e:
            logger.error(f"Framing analysis failed for EF {ef_data['id']}: {e}")
            return []

    async def process_event_family(self, ef_data: dict) -> int:
        """
        Process a single Event Family to extract narrative framings.

        Args:
            ef_data: Event Family metadata with source_title_ids

        Returns:
            Number of framed narratives created
        """
        ef_id = ef_data["id"]
        title_count = ef_data["title_count"]

        logger.info(
            f"Processing EF {ef_id[:8]}: '{ef_data['title']}' ({title_count} titles)"
        )

        # 1. Fetch title texts
        titles = self.get_title_texts(ef_data["source_title_ids"])
        if not titles:
            logger.warning(f"No titles found for EF {ef_id[:8]}")
            return 0

        # 2. Analyze framing with LLM
        narratives = await self.analyze_framing(ef_data, titles)
        if not narratives:
            logger.warning(f"No frames extracted for EF {ef_id[:8]}")
            return 0

        # 3. Save to database
        saved_count = 0
        for narrative in narratives:
            success = await self.db.save_framed_narrative(narrative)
            if success:
                saved_count += 1

        logger.info(f"Saved {saved_count}/{len(narratives)} frames for EF {ef_id[:8]}")
        return saved_count

    async def process_batch(self, limit: Optional[int] = None) -> dict:
        """
        Process a batch of Event Families with parallel LLM calls.

        Args:
            limit: Maximum number of EFs to process

        Returns:
            Stats dict with processed/success counts
        """
        start_time = datetime.now()

        # Get queue
        queue = self.get_framing_queue(limit)
        if not queue:
            logger.info("No Event Families in framing queue")
            return {"processed": 0, "total_frames": 0, "failed": 0}

        logger.info(f"Starting Phase 5 framing for {len(queue)} Event Families")

        # Process with concurrency control
        semaphore = asyncio.Semaphore(self.config.phase_5_concurrency)

        async def process_with_semaphore(ef_data: dict):
            async with semaphore:
                try:
                    return await self.process_event_family(ef_data)
                except Exception as e:
                    logger.error(f"Failed to process EF {ef_data['id'][:8]}: {e}")
                    return 0

        # Execute parallel processing
        results = await asyncio.gather(
            *[process_with_semaphore(ef) for ef in queue],
            return_exceptions=True,
        )

        # Calculate stats
        total_frames = sum(r for r in results if isinstance(r, int))
        failed = sum(1 for r in results if isinstance(r, Exception))

        duration = (datetime.now() - start_time).total_seconds()

        stats = {
            "processed": len(queue),
            "total_frames": total_frames,
            "failed": failed,
            "duration_seconds": duration,
        }

        logger.info(
            f"Phase 5 complete: {stats['processed']} EFs processed, "
            f"{stats['total_frames']} frames created, {stats['failed']} failures "
            f"in {duration:.1f}s"
        )

        return stats


async def run_framing_processor(limit: Optional[int] = None) -> dict:
    """
    Main entry point for Phase 5: Framed Narratives.

    Args:
        limit: Maximum number of Event Families to process

    Returns:
        Processing stats
    """
    processor = FramingProcessor()
    return await processor.process_batch(limit)
