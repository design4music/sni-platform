"""
EF Enrichment Processor
Lean micro-prompt system for adding strategic context to Event Families
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from apps.enrich.centroid_matcher import CentroidMatcher
from apps.enrich.models import (CanonicalActor, ComparableEvent, EFContext,
                                EnrichmentPayload, EnrichmentRecord, Magnitude)
from apps.enrich.prompts import (build_canonicalize_prompt,
                                 build_macro_link_prompt,
                                 build_narrative_summary_prompt,
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
        self.centroid_matcher = CentroidMatcher()

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
                enrichment.temporal_pattern = canonical_data.get("temporal_pattern")
                enrichment.magnitude_baseline = canonical_data.get("magnitude_baseline")
                enrichment.systemic_context = canonical_data.get("systemic_context")
                enrichment.why_strategic = canonical_data.get("why_strategic")
                enrichment.tags = canonical_data.get("tags", [])

            # Step 2: Extract magnitudes from titles (regex, no LLM)
            magnitude_data = extract_magnitudes_from_titles(member_titles)
            enrichment.magnitude = [
                Magnitude(value=mag["value"], unit=mag["unit"], what=mag["what"])
                for mag in magnitude_data
            ]

            # Step 3: Centroid matching and ef_context population
            ef_context_data = await self._populate_ef_context(
                ef_data, enrichment, member_titles
            )
            if ef_context_data:
                enrichment.ef_context = ef_context_data

            # Step 4: Official sources (placeholder for future web search)
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

            # Create enriched summary paragraph (use narrative prompt if available)
            enriched_summary = await self._create_enriched_summary(
                ef_data, enrichment, member_titles
            )

            # Update database with enriched summary, tags, and ef_context
            await self._update_ef_summary_and_context(
                ef_id, enriched_summary, enrichment.tags, enrichment.ef_context
            )

            # Change status from seed to active
            await self._update_ef_status(ef_id, "active")

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
            # Record is automatically saved via database updates
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

            # Call LLM with conservative settings - no token limit, rely on prompt instructions
            response_text = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
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
                            name=actor_data["name"],
                            role=(
                                actor_data["role"]
                                if actor_data["role"]
                                in ["initiator", "target", "beneficiary", "mediator"]
                                else "initiator"
                            ),
                        )
                    )

            # Validate tags
            tags = response_data.get("tags", [])
            if isinstance(tags, list) and len(tags) <= 3:
                validated_tags = [str(tag) for tag in tags[:3]]  # Keep first 3 tags
            else:
                validated_tags = []

            return {
                "canonical_actors": canonical_actors,
                "policy_status": response_data.get("policy_status"),
                "time_span": response_data.get(
                    "time_span", {"start": None, "end": None}
                ),
                "temporal_pattern": response_data.get("temporal_pattern", ""),
                "magnitude_baseline": response_data.get("magnitude_baseline", ""),
                "systemic_context": response_data.get("systemic_context", ""),
                "why_strategic": response_data.get("why_strategic", ""),
                "tags": validated_tags,
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

    async def _update_ef_status(self, ef_id: str, status: str) -> None:
        """
        Update event_families.status after enrichment
        """
        try:
            with get_db_session() as session:
                session.execute(
                    text(
                        """
                        UPDATE event_families
                        SET status = :status,
                            updated_at = NOW()
                        WHERE id = :ef_id
                        """
                    ),
                    {"ef_id": ef_id, "status": status},
                )
                session.commit()

            logger.debug(f"ENRICH: Updated status to {status} for EF {ef_id}")

        except Exception as e:
            logger.error(f"ENRICH: Failed to update status for EF {ef_id}: {e}")

    async def get_enrichment_for_ef(self, ef_id: str) -> Optional[EnrichmentRecord]:
        """Check if EF has been enriched by looking at status field"""
        try:
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT status
                        FROM event_families
                        WHERE id = :ef_id
                        AND status = 'active'
                        """
                    ),
                    {"ef_id": ef_id},
                ).fetchone()

                if result:
                    # Status is 'active' = already enriched
                    return EnrichmentRecord(
                        ef_id=ef_id,
                        enrichment_payload=EnrichmentPayload(),
                        status="completed",
                    )
                return None

        except Exception as e:
            logger.error(f"ENRICH: Failed to check enrichment status for {ef_id}: {e}")
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

    async def _populate_ef_context(
        self,
        ef_data: Dict[str, Any],
        enrichment: EnrichmentPayload,
        member_titles: List[Dict[str, Any]],
    ) -> EFContext:
        """
        Populate ef_context using centroid matching and LLM assessment
        """
        try:
            # Step 1: Mechanical centroid matching
            actor_names = [actor.name for actor in enrichment.canonical_actors]
            match_result = self.centroid_matcher.match_centroid(
                ef_title=ef_data["title"],
                ef_summary=ef_data["summary"],
                ef_actors=actor_names,
                primary_theater=ef_data["primary_theater"],
                event_type=ef_data.get("event_type", ""),
            )

            ef_context = EFContext()

            # High confidence mechanical match
            if match_result.confidence_score >= 0.7:
                ef_context.macro_link = match_result.centroid_id
                logger.debug(
                    f"ENRICH: High confidence centroid match: {match_result.centroid_id}"
                )

            # Medium/Low confidence - use LLM for macro-link assessment
            elif match_result.requires_llm_verification:
                logger.debug(
                    f"ENRICH: Using LLM for centroid assessment (score: {match_result.confidence_score:.3f})"
                )

                # Get top candidates for LLM assessment
                top_candidates = self.centroid_matcher.get_top_candidates(
                    ef_title=ef_data["title"],
                    ef_summary=ef_data["summary"],
                    ef_actors=actor_names,
                    primary_theater=ef_data["primary_theater"],
                    event_type=ef_data.get("event_type", ""),
                    top_n=5,
                )

                # Format centroids for LLM prompt
                available_centroids = []
                for centroid_id, score, components in top_candidates:
                    centroid_data = next(
                        (
                            c
                            for c in self.centroid_matcher.centroids
                            if c["id"] == centroid_id
                        ),
                        None,
                    )
                    if centroid_data:
                        available_centroids.append(centroid_data)

                # Build macro-link assessment prompt
                system_prompt, user_prompt = build_macro_link_prompt(
                    ef_title=ef_data["title"],
                    ef_summary=ef_data["summary"],
                    event_type=ef_data.get("event_type", ""),
                    primary_theater=ef_data["primary_theater"],
                    canonical_actors=actor_names,
                    available_centroids=available_centroids,
                )

                # Call LLM for macro-link assessment
                response_text = await self.llm_client._call_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.0,
                )

                # Parse LLM response
                response_data = self.llm_client._extract_json(response_text)
                ef_context_data = response_data.get("ef_context", {})

                # Populate ef_context from LLM response
                ef_context.macro_link = (
                    ef_context_data.get("macro_link")
                    if ef_context_data.get("macro_link") != "null"
                    else None
                )

                # Parse comparables
                comparables_data = ef_context_data.get("comparables", [])
                ef_context.comparables = [
                    ComparableEvent(
                        event_description=comp.get("event_description", ""),
                        timeframe=comp.get("timeframe", ""),
                        similarity_reason=comp.get("similarity_reason", ""),
                    )
                    for comp in comparables_data[:3]  # Limit to 3
                    if isinstance(comp, dict) and comp.get("event_description")
                ]

                ef_context.abnormality = (
                    ef_context_data.get("abnormality")
                    if ef_context_data.get("abnormality") != "null"
                    else None
                )

            return ef_context

        except Exception as e:
            logger.warning(f"ENRICH: Failed to populate ef_context: {e}")
            return EFContext()

    async def _create_enriched_summary(
        self,
        ef_data: Dict[str, Any],
        enrichment: EnrichmentPayload,
        member_titles: List[Dict[str, Any]],
    ) -> str:
        """
        Create enhanced narrative summary using LLM if ef_context is populated
        """
        try:
            # If we have ef_context with meaningful data, use narrative summary prompt
            if enrichment.ef_context and (
                enrichment.ef_context.macro_link
                or enrichment.ef_context.comparables
                or enrichment.ef_context.abnormality
            ):

                actor_names = [actor.name for actor in enrichment.canonical_actors]

                # Build narrative summary prompt
                system_prompt, user_prompt = build_narrative_summary_prompt(
                    ef_title=ef_data["title"],
                    current_summary=ef_data["summary"],
                    event_type=ef_data.get("event_type", ""),
                    primary_theater=ef_data["primary_theater"],
                    canonical_actors=actor_names,
                    member_titles=member_titles,
                )

                # Call LLM for narrative enhancement
                response_text = await self.llm_client._call_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.1,  # Slight creativity for narrative flow
                )

                # Use LLM response as enhanced summary
                enhanced_summary = response_text.strip()
                if (
                    enhanced_summary and len(enhanced_summary) > 50
                ):  # Basic quality check
                    return enhanced_summary

            # Fallback to original method if no ef_context or LLM fails
            return await self._create_basic_enriched_summary(ef_data, enrichment)

        except Exception as e:
            logger.warning(
                f"ENRICH: Failed to create narrative summary, using fallback: {e}"
            )
            return await self._create_basic_enriched_summary(ef_data, enrichment)

    async def _create_basic_enriched_summary(
        self, ef_data: Dict[str, Any], enrichment: EnrichmentPayload
    ) -> str:
        """
        Create a smooth, readable enriched summary paragraph (original method)
        """
        try:
            original_summary = ef_data.get("summary", "")

            # Build narrative components
            narrative_parts = []

            # Start with original summary
            if original_summary:
                narrative_parts.append(original_summary)

            # Weave in temporal pattern naturally
            if enrichment.temporal_pattern:
                narrative_parts.append(
                    f"This follows a documented pattern of {enrichment.temporal_pattern.lower()}."
                )

            # Add systemic context
            if enrichment.systemic_context:
                narrative_parts.append(
                    f"The development fits within {enrichment.systemic_context.lower()}."
                )

            # Include strategic significance
            if enrichment.why_strategic:
                narrative_parts.append(
                    f"The event carries significance as {enrichment.why_strategic.lower()}."
                )

            # Add policy dimension if relevant
            if enrichment.policy_status and enrichment.policy_status != "null":
                status_map = {
                    "proposed": "remains under consideration",
                    "passed": "has been approved",
                    "signed": "has been formally enacted",
                    "in_force": "is currently active",
                    "enforced": "is being actively implemented",
                    "suspended": "has been temporarily halted",
                    "cancelled": "has been terminated",
                }
                status_text = status_map.get(
                    enrichment.policy_status, enrichment.policy_status
                )
                narrative_parts.append(f"The policy dimension {status_text}.")

            # Combine into flowing paragraph
            enriched_summary = " ".join(narrative_parts)
            return enriched_summary

        except Exception as e:
            logger.warning(f"ENRICH: Failed to create basic enriched summary: {e}")
            return ef_data.get("summary", "")

    async def _update_ef_summary_and_context(
        self, ef_id: str, enriched_summary: str, tags: List[str], ef_context: EFContext
    ) -> None:
        """
        Update event_families with enriched summary, tags, and ef_context
        """
        try:
            with get_db_session() as session:
                session.execute(
                    text(
                        """
                        UPDATE event_families
                        SET summary = :enriched_summary,
                            tags = :tags_json,
                            ef_context = :ef_context_json,
                            updated_at = NOW()
                        WHERE id = :ef_id
                        """
                    ),
                    {
                        "ef_id": ef_id,
                        "enriched_summary": enriched_summary,
                        "tags_json": json.dumps(tags),
                        "ef_context_json": json.dumps(ef_context.model_dump()),
                    },
                )
                session.commit()

            logger.debug(
                f"ENRICH: Updated summary, tags, and ef_context for EF {ef_id}"
            )

        except Exception as e:
            logger.error(
                f"ENRICH: Failed to update summary/context for EF {ef_id}: {e}"
            )
