"""
EF Enrichment Processor
Lean micro-prompt system for adding strategic context to Event Families
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from apps.enrich.models import (CanonicalActor, EnrichmentPayload,
                                EnrichmentRecord, Magnitude)
from apps.enrich.prompts import (build_canonicalize_prompt,
                                 extract_magnitudes_from_titles)
from apps.generate.llm_client import get_gen1_llm_client
from core.config import get_config
from core.database import get_db_session


class EFEnrichmentProcessor:
    """
    Lean EF Enrichment Processor

    Implements the micro-prompt approach:
    1. Canonicalize actors + extract policy status (1 LLM call)
    2. Extract magnitudes from titles (regex, no LLM)
    3. Optional: Find official sources (future: 1 web search)

    Guardrails: ≤2 micro-prompts per EF, daily caps, JSON sidecar storage
    """

    def __init__(self):
        self.config = get_config()
        self.llm_client = get_gen1_llm_client()

        # Create enrichment storage directory
        self.enrichment_dir = Path(self.config.project_root) / "data" / "enrichments"
        self.enrichment_dir.mkdir(parents=True, exist_ok=True)

        # Daily processing limits
        self.daily_enrichment_cap = getattr(self.config, "daily_enrichment_cap", 100)

    async def enrich_event_family(self, ef_id: str) -> Optional[EnrichmentRecord]:
        """
        Enrich a single Event Family with lean context

        Args:
            ef_id: Event Family UUID

        Returns:
            EnrichmentRecord with enrichment data or None if failed
        """
        start_time = time.time()

        try:
            logger.debug(f"ENRICH: Starting enrichment for EF {ef_id}")

            # Get Event Family data
            ef_data = await self._get_event_family_data(ef_id)
            if not ef_data:
                logger.warning(f"ENRICH: EF {ef_id} not found")
                return None

            # Get member titles
            member_titles = await self._get_member_titles(ef_id)
            if not member_titles:
                logger.warning(f"ENRICH: No member titles found for EF {ef_id}")
                return None

            logger.debug(
                f"ENRICH: Processing EF '{ef_data['title']}' with {len(member_titles)} titles"
            )

            # Initialize enrichment payload
            enrichment = EnrichmentPayload()

            # Step 1: Canonicalize actors + extract policy status (1 LLM call)
            canonical_data = await self._canonicalize_actors_and_status(
                ef_data, member_titles
            )
            if canonical_data:
                enrichment.canonical_actors = canonical_data.get("canonical_actors", [])
                enrichment.policy_status = canonical_data.get("policy_status")
                enrichment.time_span = canonical_data.get(
                    "time_span", {"start": None, "end": None}
                )
                enrichment.why_strategic = canonical_data.get("why_strategic")

            # Step 2: Extract magnitudes from titles (regex, no LLM)
            magnitude_data = extract_magnitudes_from_titles(member_titles)
            enrichment.magnitude = [
                Magnitude(value=mag["value"], unit=mag["unit"], what=mag["what"])
                for mag in magnitude_data
            ]

            # Step 3: Official sources (placeholder for future web search)
            enrichment.official_sources = await self._find_official_sources(
                ef_data, enrichment
            )

            # Calculate processing metrics
            processing_time_ms = int((time.time() - start_time) * 1000)
            tokens_used = getattr(self.llm_client, "_last_tokens_used", 0)

            # Create enrichment record
            record = EnrichmentRecord(
                ef_id=ef_id,
                enrichment_payload=enrichment,
                sources_found=len(enrichment.official_sources),
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                status="completed",
            )

            # Save to JSON sidecar
            await self._save_enrichment_record(record)

            logger.info(
                f"ENRICH: Completed EF {ef_id} in {processing_time_ms}ms "
                f"({tokens_used} tokens, {len(enrichment.canonical_actors)} actors, "
                f"{len(enrichment.magnitude)} magnitudes)"
            )

            return record

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"ENRICH: Failed to enrich EF {ef_id}: {e}")

            # Create failed record
            record = EnrichmentRecord(
                ef_id=ef_id,
                enrichment_payload=EnrichmentPayload(),
                processing_time_ms=processing_time_ms,
                status="failed",
                error_message=str(e),
            )
            await self._save_enrichment_record(record)
            return record

    async def _get_event_family_data(self, ef_id: str) -> Optional[Dict[str, Any]]:
        """Get Event Family metadata from database"""
        try:
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT id, title, summary, event_type, primary_theater,
                               key_actors, created_at, source_title_ids
                        FROM event_families
                        WHERE id = :ef_id
                    """
                    ),
                    {"ef_id": ef_id},
                ).fetchone()

                if result:
                    return {
                        "id": str(result.id),
                        "title": result.title,
                        "summary": result.summary,
                        "event_type": result.event_type,
                        "primary_theater": result.primary_theater,
                        "key_actors": result.key_actors,
                        "created_at": result.created_at,
                        "source_title_ids": result.source_title_ids,
                    }
                return None

        except Exception as e:
            logger.error(f"ENRICH: Database error getting EF {ef_id}: {e}")
            return None

    async def _get_member_titles(self, ef_id: str) -> List[Dict[str, Any]]:
        """Get member titles for the Event Family"""
        try:
            with get_db_session() as session:
                results = session.execute(
                    text(
                        """
                        SELECT id, title_display as text, url_gnews as url,
                               pubdate_utc, publisher_name as source
                        FROM titles
                        WHERE event_family_id = :ef_id
                        ORDER BY pubdate_utc DESC
                    """
                    ),
                    {"ef_id": ef_id},
                ).fetchall()

                return [
                    {
                        "id": str(result.id),
                        "text": result.text,
                        "url": result.url,
                        "pubdate_utc": result.pubdate_utc,
                        "source": result.source,
                    }
                    for result in results
                ]

        except Exception as e:
            logger.error(f"ENRICH: Database error getting titles for EF {ef_id}: {e}")
            return []

    async def _canonicalize_actors_and_status(
        self, ef_data: Dict[str, Any], member_titles: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Canonicalize actors, extract roles and policy status (Micro-Prompt 1)
        """
        try:
            # Build canonicalization prompt
            system_prompt, user_prompt = build_canonicalize_prompt(
                ef_title=ef_data["title"],
                event_type=ef_data["event_type"],
                primary_theater=ef_data["primary_theater"],
                member_titles=member_titles,
            )

            # Call LLM with conservative settings
            response_text = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=200,  # Bounded response
                temperature=0.0,  # Deterministic
            )

            # Parse JSON response
            response_data = self.llm_client._extract_json(response_text)

            # Validate and clean response
            canonical_actors = []
            for actor_data in response_data.get("canonical_actors", []):
                if (
                    isinstance(actor_data, dict)
                    and "name" in actor_data
                    and "role" in actor_data
                ):
                    canonical_actors.append(
                        CanonicalActor(
                            name=actor_data["name"][:50],  # Limit length
                            role=(
                                actor_data["role"]
                                if actor_data["role"]
                                in ["initiator", "target", "beneficiary", "mediator"]
                                else "initiator"
                            ),
                        )
                    )

            return {
                "canonical_actors": canonical_actors,
                "policy_status": response_data.get("policy_status"),
                "time_span": response_data.get(
                    "time_span", {"start": None, "end": None}
                ),
                "why_strategic": response_data.get("why_strategic", "")[
                    :150
                ],  # Limit length
            }

        except Exception as e:
            logger.warning(f"ENRICH: Failed to canonicalize actors: {e}")
            return None

    async def _find_official_sources(
        self, ef_data: Dict[str, Any], enrichment: EnrichmentPayload
    ) -> List[str]:
        """
        Find official sources (placeholder for future web search implementation)

        Currently returns empty list - implement web search in v1.1
        """
        # TODO: Implement official source search
        # - Build search query from canonical actors + policy status
        # - Search gov/institution domains only
        # - Return max 2 official URLs
        return []

    async def _save_enrichment_record(self, record: EnrichmentRecord) -> None:
        """Save enrichment record to JSON sidecar file"""
        try:
            filename = f"ef_{record.ef_id}_enrichment.json"
            filepath = self.enrichment_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(record.dict(), f, indent=2, default=str)

            logger.debug(f"ENRICH: Saved enrichment record to {filepath}")

        except Exception as e:
            logger.error(f"ENRICH: Failed to save enrichment record: {e}")

    async def get_enrichment_for_ef(self, ef_id: str) -> Optional[EnrichmentRecord]:
        """Load enrichment record from JSON sidecar file"""
        try:
            filename = f"ef_{ef_id}_enrichment.json"
            filepath = self.enrichment_dir / filename

            if not filepath.exists():
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            return EnrichmentRecord(**data)

        except Exception as e:
            logger.error(f"ENRICH: Failed to load enrichment record for {ef_id}: {e}")
            return None

    async def get_enrichment_queue(self, limit: int = 50) -> List[str]:
        """
        Get prioritized list of EF IDs for enrichment

        Priority scoring: recency (days) + size (titles) + strategic keywords
        """
        try:
            with get_db_session() as session:
                # Get candidate EFs (recent, multi-title, not yet enriched)
                results = session.execute(
                    text(
                        """
                        SELECT ef.id, ef.title, ef.created_at,
                               (SELECT COUNT(*) FROM titles t WHERE t.event_family_id = ef.id) as title_count
                        FROM event_families ef
                        WHERE ef.status = 'seed'
                        AND ef.created_at >= NOW() - INTERVAL '7 days'
                        ORDER BY ef.created_at DESC, title_count DESC
                        LIMIT :limit
                    """
                    ),
                    {"limit": limit * 2},  # Get extra candidates for filtering
                ).fetchall()

                # Calculate priority scores and filter out already enriched
                candidates = []
                for result in results:
                    ef_id = str(result.id)

                    # Skip if already enriched
                    existing_enrichment = await self.get_enrichment_for_ef(ef_id)
                    if (
                        existing_enrichment
                        and existing_enrichment.status == "completed"
                    ):
                        continue

                    # Calculate priority score
                    days_old = (datetime.utcnow() - result.created_at).days
                    recency_score = max(0, 7 - days_old)  # Higher for newer
                    size_score = min(result.title_count, 10)  # Cap at 10

                    # Strategic keyword bonus
                    keyword_score = 0
                    strategic_keywords = [
                        "NATO",
                        "nuclear",
                        "sanctions",
                        "invasion",
                        "assassination",
                        "diplomatic",
                        "alliance",
                        "security",
                        "escalation",
                    ]
                    title_lower = result.title.lower()
                    for keyword in strategic_keywords:
                        if keyword.lower() in title_lower:
                            keyword_score += 2

                    total_score = recency_score + size_score + keyword_score
                    candidates.append((ef_id, total_score))

                # Sort by priority and return top candidates
                candidates.sort(key=lambda x: x[1], reverse=True)
                return [ef_id for ef_id, score in candidates[:limit]]

        except Exception as e:
            logger.error(f"ENRICH: Failed to get enrichment queue: {e}")
            return []

    async def process_enrichment_queue(self, max_items: int = None) -> Dict[str, int]:
        """
        Process enrichment queue with daily caps

        Args:
            max_items: Maximum items to process (uses daily cap if None)

        Returns:
            Processing statistics
        """
        if max_items is None:
            max_items = self.daily_enrichment_cap

        logger.info(f"ENRICH: Starting queue processing (max {max_items} items)")

        # Get enrichment queue
        queue = await self.get_enrichment_queue(limit=max_items)
        if not queue:
            logger.info("ENRICH: No items in enrichment queue")
            return {"processed": 0, "succeeded": 0, "failed": 0}

        logger.info(f"ENRICH: Processing {len(queue)} EFs from queue")

        # Process queue items
        results = {"processed": 0, "succeeded": 0, "failed": 0}

        for ef_id in queue:
            try:
                result = await self.enrich_event_family(ef_id)
                results["processed"] += 1

                if result and result.status == "completed":
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(f"ENRICH: Failed to process EF {ef_id}: {e}")
                results["processed"] += 1
                results["failed"] += 1

        logger.info(
            f"ENRICH: Queue processing completed - "
            f"{results['succeeded']}/{results['processed']} succeeded"
        )

        return results
