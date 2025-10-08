"""
RAI (Risk Assessment Intelligence) Processor for SNI-v2
Sends Framed Narratives to external RAI service for analysis
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from loguru import logger
from sqlalchemy import text

from core.config import get_config
from core.database import get_db_session


class RAIProcessor:
    """Process Framed Narratives through external RAI analysis service"""

    def __init__(self):
        self.config = get_config()

        # Validate RAI configuration
        if not self.config.rai_api_key:
            raise ValueError("RAI_API_KEY not configured in environment")
        if not self.config.rai_api_url:
            raise ValueError("RAI_API_URL not configured in environment")

    def get_rai_queue(self, limit: Optional[int] = None) -> List[dict]:
        """
        Get Framed Narratives that need RAI analysis

        Returns FNs where:
        - rai_analysis IS NULL (never analyzed)
        - Parent Event Family is 'active' or 'enriched'
        """
        with get_db_session() as session:
            query = text(
                """
                SELECT
                    fn.id,
                    fn.event_family_id,
                    fn.frame_description,
                    fn.stance_summary,
                    fn.supporting_headlines,
                    fn.created_at,
                    fn.updated_at,

                    -- Event Family context
                    ef.title,
                    ef.summary,
                    ef.key_actors,
                    ef.event_type,
                    ef.primary_theater,
                    ef.tags,
                    ef.ef_context,
                    ef.status

                FROM framed_narratives fn
                JOIN event_families ef ON fn.event_family_id = ef.id
                WHERE fn.rai_analysis IS NULL
                  AND ef.status IN ('active', 'enriched')
                ORDER BY fn.created_at DESC
                LIMIT :limit
            """
            )

            result = session.execute(query, {"limit": limit or 1000})
            return [dict(row._mapping) for row in result.fetchall()]

    async def analyze_narrative(self, fn_data: dict) -> Optional[Dict]:
        """
        Send single Framed Narrative to RAI service for analysis

        Args:
            fn_data: Combined FN + EF data from get_rai_queue()

        Returns:
            RAI analysis dict or None on failure
        """
        try:
            # Build request payload for RAI backend
            # RAI expects: {"content": {"title": "...", "summary": "...", "excerpts": [...]}}

            # Combine EF and FN into a narrative for analysis
            narrative_title = f"{fn_data['title']} - {fn_data['frame_description']}"
            narrative_summary = f"""
Event Summary: {fn_data['summary']}

Narrative Framing: {fn_data['stance_summary']}

Key Actors: {', '.join(fn_data['key_actors']) if fn_data['key_actors'] else 'N/A'}
Event Type: {fn_data['event_type']}
Theater: {fn_data['primary_theater'] or 'N/A'}
""".strip()

            # Supporting headlines as excerpts
            excerpts = (
                fn_data["supporting_headlines"]
                if fn_data["supporting_headlines"]
                else []
            )

            payload = {
                "content": {
                    "title": narrative_title,
                    "summary": narrative_summary,
                    "excerpts": excerpts,
                },
                "analysis_type": "guided",  # Use guided mode for comprehensive analysis
            }

            # Make HTTP POST request to RAI service
            async with httpx.AsyncClient(
                timeout=self.config.rai_timeout_seconds
            ) as client:
                response = await client.post(
                    self.config.rai_api_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.config.rai_api_key}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"RAI service error for FN {fn_data['id']}: "
                        f"status={response.status_code}, body={response.text}"
                    )
                    return None

                # Parse response
                rai_result = response.json()

                logger.debug(
                    f"RAI analysis complete for FN {fn_data['id']}: "
                    f"adequacy_score={rai_result.get('adequacy_score')}"
                )

                return rai_result

        except httpx.TimeoutException:
            logger.error(
                f"RAI service timeout for FN {fn_data['id']} "
                f"(>{self.config.rai_timeout_seconds}s)"
            )
            return None
        except Exception as e:
            logger.error(
                f"RAI analysis failed for FN {fn_data['id']}: {e}",
                exc_info=True,
            )
            return None

    async def process_batch(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Process batch of Framed Narratives with RAI analysis

        Args:
            limit: Maximum FNs to process (None = use config default)

        Returns:
            Statistics dict
        """
        start_time = datetime.now()

        stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
        }

        # Get queue
        queue = self.get_rai_queue(limit=limit or self.config.phase_6_max_items)

        if not queue:
            logger.info("No Framed Narratives pending RAI analysis")
            return stats

        logger.info(f"Starting RAI analysis for {len(queue)} Framed Narratives")

        # Process with concurrency control
        semaphore = asyncio.Semaphore(self.config.phase_6_concurrency)

        async def process_one(fn_data: dict) -> tuple:
            """Process single FN with semaphore"""
            async with semaphore:
                rai_result = await self.analyze_narrative(fn_data)
                return fn_data["id"], rai_result

        # Execute all analyses
        tasks = [process_one(fn_data) for fn_data in queue]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Store results in database
        with get_db_session() as session:
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"RAI task failed with exception: {result}")
                    stats["failed"] += 1
                    continue

                fn_id, rai_result = result
                stats["processed"] += 1

                if rai_result:
                    # Store RAI analysis in framed_narratives table
                    session.execute(
                        text(
                            """
                            UPDATE framed_narratives
                            SET rai_analysis = CAST(:rai_analysis AS jsonb),
                                updated_at = NOW()
                            WHERE id = :fn_id
                        """
                        ),
                        {"fn_id": fn_id, "rai_analysis": json.dumps(rai_result)},
                    )
                    stats["success"] += 1
                    logger.info(
                        f"Stored RAI analysis for FN {fn_id}: "
                        f"adequacy={rai_result.get('adequacy_score', 'N/A')}"
                    )
                else:
                    stats["failed"] += 1

        stats["duration_seconds"] = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"RAI batch complete: {stats['success']}/{stats['processed']} succeeded, "
            f"{stats['failed']} failed in {stats['duration_seconds']:.1f}s"
        )

        return stats


async def run_rai_processor(limit: Optional[int] = None) -> Dict[str, int]:
    """
    Main entry point for RAI processing

    Args:
        limit: Maximum FNs to process

    Returns:
        Statistics dict
    """
    processor = RAIProcessor()
    return await processor.process_batch(limit=limit)


if __name__ == "__main__":
    # CLI testing
    import sys

    asyncio.run(
        run_rai_processor(limit=int(sys.argv[1]) if len(sys.argv) > 1 else None)
    )
