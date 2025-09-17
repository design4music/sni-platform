#!/usr/bin/env python3
"""
GEN-1 Multi-Pass Processor
Implements sophisticated multi-pass Event Family generation:
1. Entity-coherent EF assembly (basic metadata only)
2. Intelligent EF merging + Framed Narrative generation
3. Historical integration (future)
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import text

from apps.generate.database import get_gen1_database
from apps.generate.ef_key import (generate_ef_key_from_data,
                              validate_ef_key_components)
from apps.generate.llm_client import get_gen1_llm_client
from apps.generate.models import (EventFamily, FramedNarrative,
                              LLMEventFamilyRequest, LLMFramedNarrativeRequest,
                              ProcessingResult)
from apps.generate.sequential_batcher import group_titles_sequentially
from core.config import get_config
from core.database import get_db_session


class MultiPassProcessor:
    """
    Multi-pass Event Family processor with intelligent merging
    """

    def __init__(self):
        self.db = get_gen1_database()
        self.llm_client = get_gen1_llm_client()

    async def run_pass1_entity_assembly(
        self,
        max_titles: Optional[int] = None,
        batch_size: int = 50,
        dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Pass 1: Entity-coherent Event Family assembly

        Process titles in entity-coherent batches to create basic Event Families.
        No Framed Narratives generated at this stage.

        Args:
            max_titles: Maximum titles to process (None for all)
            batch_size: Target size for entity batches
            dry_run: Don't save to database

        Returns:
            ProcessingResult with basic Event Families
        """
        start_time = datetime.now()
        logger.info("=== GEN-1 PASS 1: Entity-Coherent EF Assembly ===")

        try:
            # Get unassigned strategic titles
            titles = self.db.get_unassigned_strategic_titles(
                limit=max_titles, order_by="newest_first"
            )

            if not titles:
                logger.warning("No unassigned strategic titles found")
                return ProcessingResult(
                    total_titles_processed=0,
                    event_families=[],
                    framed_narratives=[],
                    success_rate=0.0,
                    processing_time_seconds=0.0,
                    errors=["No unassigned strategic titles found"],
                    warnings=[],
                )

            logger.info(f"Found {len(titles)} unassigned strategic titles")

            # Group titles sequentially (no entity complexity)
            # Use configurable batch size for reliable processing
            config = get_config()
            sequential_batches = group_titles_sequentially(
                titles, batch_size=config.ef_batch_size
            )
            logger.info(f"Created {len(sequential_batches)} sequential batches")

            # Process each entity batch
            all_event_families = []
            processing_errors = []
            processing_warnings = []

            for i, batch_info in enumerate(sequential_batches, 1):
                batch_key = batch_info["batch_key"]
                batch_titles = batch_info["titles"]
                logger.info(
                    f"Pass 1: Processing sequential batch {i}/{len(sequential_batches)} "
                    f"({len(batch_titles)} titles, batch_key='{batch_key}')"
                )

                try:
                    # Generate basic Event Families (no Framed Narratives)
                    ef_results = await self._generate_pass1_event_families(batch_titles)

                    for ef_data in ef_results.get("event_families", []):
                        # Generate ef_key for this Event Family
                        actors = ef_data.get("key_actors", [])
                        primary_theater = ef_data.get(
                            "geography", ef_data.get("primary_theater")
                        )
                        event_type = ef_data.get("event_type", "")

                        # Validate ef_key components
                        if validate_ef_key_components(
                            actors, primary_theater, event_type
                        ):
                            ef_key = generate_ef_key_from_data(
                                {
                                    "key_actors": actors,
                                    "primary_theater": primary_theater,
                                    "event_type": event_type,
                                }
                            )
                            logger.debug(
                                f"Generated ef_key: {ef_key} for EF: {ef_data['title']}"
                            )
                        else:
                            ef_key = None
                            logger.warning(
                                f"Invalid ef_key components for EF: {ef_data['title']}"
                            )

                        # Create EventFamily object (basic metadata only)
                        event_family = EventFamily(
                            title=ef_data["title"],
                            summary=ef_data["summary"],
                            key_actors=actors,
                            event_type=event_type,
                            primary_theater=primary_theater,
                            ef_key=ef_key,
                            event_start=datetime.fromisoformat(ef_data["event_start"]),
                            event_end=(
                                datetime.fromisoformat(ef_data["event_end"])
                                if ef_data.get("event_end")
                                else None
                            ),
                            source_title_ids=ef_data.get("source_title_ids", []),
                            confidence_score=ef_data.get("confidence_score", 0.5),
                            coherence_reason=ef_data.get("coherence_reason", ""),
                            processing_notes=f"Pass 1: Sequential batch '{batch_key}'",
                        )

                        if not dry_run:
                            # Use ef_key upsert for continuous merging
                            success, existing_ef_id = (
                                await self.db.upsert_event_family_by_ef_key(
                                    event_family
                                )
                            )

                            if success:
                                if existing_ef_id:
                                    logger.info(
                                        f"Pass 1: Merged into existing EF: {existing_ef_id}"
                                    )
                                    final_ef_id = existing_ef_id
                                else:
                                    logger.debug(
                                        f"Pass 1: Created new EF: {event_family.title}"
                                    )
                                    final_ef_id = event_family.id

                                # Assign titles to the Event Family (new or existing)
                                await self.db.assign_titles_to_event_family(
                                    title_ids=ef_data.get("source_title_ids", []),
                                    event_family_id=final_ef_id,
                                    confidence=ef_data.get("confidence_score", 0.5),
                                    reason=f"Pass 1 sequential batch: {batch_key}",
                                )
                            else:
                                processing_errors.append(
                                    f"Failed to upsert Event Family: {event_family.title}"
                                )

                        all_event_families.append(event_family)

                except Exception as e:
                    logger.error(
                        f"Pass 1: Error processing sequential batch {batch_key}: {e}"
                    )
                    processing_errors.append(f"Sequential batch {batch_key}: {e}")
                    continue

            # Calculate final stats
            processing_time = (datetime.now() - start_time).total_seconds()
            total_processed = sum(
                batch_info["size"] for batch_info in sequential_batches
            )
            success_rate = (
                len(all_event_families) / max(total_processed, 1)
                if all_event_families
                else 0.0
            )

            logger.info(
                f"Pass 1 completed: {len(all_event_families)} Event Families from {total_processed} titles",
                processing_time=f"{processing_time:.1f}s",
                success_rate=f"{success_rate:.1%}",
            )

            return ProcessingResult(
                total_titles_processed=total_processed,
                event_families=all_event_families,
                framed_narratives=[],  # No FNs in Pass 1
                success_rate=success_rate,
                processing_time_seconds=processing_time,
                errors=processing_errors,
                warnings=processing_warnings,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Pass 1 failed: {e}")
            return ProcessingResult(
                total_titles_processed=0,
                event_families=[],
                framed_narratives=[],
                success_rate=0.0,
                processing_time_seconds=processing_time,
                errors=[f"Pass 1 failed: {e}"],
                warnings=[],
            )

    async def run_pass2a_ef_merging(
        self,
        max_event_families: Optional[int] = None,
        dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Pass 2A: EF merging based on theater + event_type matching with LLM decisions

        Finds Event Families with same primary_theater + event_type but different ef_keys
        and uses LLM to decide if they should be merged based on actor compatibility.

        Args:
            max_event_families: Maximum EFs to analyze (None for all active)
            dry_run: Don't save changes to database

        Returns:
            ProcessingResult with merge operations
        """
        start_time = datetime.now()
        logger.info("=== GEN-1 PASS 2A: EF Theater+Type Merging ===")

        try:
            # Get active Event Families for merging analysis
            with get_db_session() as session:
                query = """
                SELECT id, title, summary, key_actors, event_type, primary_theater,
                       ef_key, event_start, event_end, source_title_ids,
                       confidence_score, coherence_reason, created_at
                FROM event_families 
                WHERE status = 'active' AND ef_key IS NOT NULL
                ORDER BY created_at DESC
                """

                if max_event_families:
                    query += f" LIMIT {max_event_families}"

                results = session.execute(text(query)).fetchall()

                event_families = []
                for row in results:
                    ef = EventFamily(
                        id=str(row.id),
                        title=row.title,
                        summary=row.summary,
                        key_actors=row.key_actors or [],
                        event_type=row.event_type,
                        primary_theater=row.primary_theater,
                        ef_key=row.ef_key,
                        event_start=row.event_start,
                        event_end=row.event_end,
                        source_title_ids=row.source_title_ids or [],
                        confidence_score=row.confidence_score or 0.5,
                        coherence_reason=row.coherence_reason or "",
                        created_at=row.created_at,
                    )
                    event_families.append(ef)

            if not event_families:
                logger.warning("No active Event Families found for Pass 2A merging")
                return ProcessingResult(
                    total_titles_processed=0,
                    event_families=[],
                    framed_narratives=[],
                    success_rate=0.0,
                    processing_time_seconds=0.0,
                    errors=["No active Event Families found"],
                    warnings=[],
                )

            logger.info(
                f"Found {len(event_families)} active Event Families for Pass 2A analysis"
            )

            # Group by theater + event_type to find merge candidates
            merge_candidates = {}
            for ef in event_families:
                key = f"{ef.primary_theater}|{ef.event_type}"
                if key not in merge_candidates:
                    merge_candidates[key] = []
                merge_candidates[key].append(ef)

            # Find groups with multiple EFs (merge candidates)
            merge_groups = {k: v for k, v in merge_candidates.items() if len(v) > 1}
            logger.info(
                f"Found {len(merge_groups)} theater+type groups with merge candidates"
            )

            merged_families = []
            processing_errors = []
            processing_warnings = []
            total_merges = 0

            # Process each merge group
            for group_key, efs in merge_groups.items():
                theater, event_type = group_key.split("|", 1)
                logger.info(
                    f"Pass 2A: Analyzing {len(efs)} EFs for {theater}/{event_type}"
                )

                try:
                    # Use LLM to determine merge compatibility
                    merge_decision = await self._llm_merge_decision(
                        efs, theater, event_type
                    )

                    if merge_decision.get("should_merge", False):
                        # Merge the Event Families
                        merged_ef = await self._execute_ef_merge(
                            efs, merge_decision, dry_run
                        )
                        if merged_ef:
                            merged_families.append(merged_ef)
                            total_merges += len(efs) - 1  # Count merged EFs
                            logger.info(
                                f"Pass 2A: Merged {len(efs)} EFs into: {merged_ef.title}"
                            )
                        else:
                            processing_errors.append(
                                f"Failed to merge {group_key} group"
                            )
                    else:
                        # Keep separate - add to result
                        merged_families.extend(efs)
                        logger.info(
                            f"Pass 2A: Kept {len(efs)} EFs separate for {group_key}"
                        )

                except Exception as e:
                    logger.error(
                        f"Pass 2A: Error processing merge group {group_key}: {e}"
                    )
                    processing_errors.append(f"Group {group_key}: {e}")
                    # Keep original EFs if merge fails
                    merged_families.extend(efs)

            # Add single EFs (no merge candidates)
            for group_key, efs in merge_candidates.items():
                if len(efs) == 1:
                    merged_families.extend(efs)

            # Calculate final stats
            processing_time = (datetime.now() - start_time).total_seconds()
            success_rate = (
                total_merges / max(len(event_families), 1) if total_merges else 0.0
            )

            logger.info(
                f"Pass 2A completed: {total_merges} merges from {len(event_families)} EFs",
                processing_time=f"{processing_time:.1f}s",
                success_rate=f"{success_rate:.1%}",
            )

            return ProcessingResult(
                total_titles_processed=0,  # Pass 2A processes EFs, not titles
                event_families=merged_families,
                framed_narratives=[],  # No narratives in Pass 2A
                success_rate=success_rate,
                processing_time_seconds=processing_time,
                errors=processing_errors,
                warnings=processing_warnings,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Pass 2A failed: {e}")
            return ProcessingResult(
                total_titles_processed=0,
                event_families=[],
                framed_narratives=[],
                success_rate=0.0,
                processing_time_seconds=processing_time,
                errors=[f"Pass 2A failed: {e}"],
                warnings=[],
            )

    async def _generate_pass1_event_families(
        self, titles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate basic Event Families for Pass 1 (no Framed Narratives)

        Args:
            titles: List of title dictionaries

        Returns:
            Dictionary with event_families list
        """
        # Build simplified prompt for Pass 1 - focus on basic EF assembly
        titles_context = []
        for i, title in enumerate(titles):
            titles_context.append(
                {
                    "headline_id": title[
                        "id"
                    ],  # Use actual title ID instead of fake headline{i}
                    "headline": title["text"],
                    "source": title.get("source", "Unknown"),
                    "pubdate": (
                        title.get("pubdate_utc", "").strftime("%Y-%m-%d %H:%M")
                        if title.get("pubdate_utc")
                        else "Unknown"
                    ),
                    "actors": (
                        title.get("actors", {}).get("actors", [])
                        if isinstance(title.get("actors"), dict)
                        else []
                    ),
                }
            )

        prompt = f"""You are assembling long-lived Event Families (Sagas) by (key_actors + geography + event_type). Do not create families for single incidents; absorb repeated incidents into one family.

PASS 1 OBJECTIVE: Create basic Event Families with essential metadata using STANDARDIZED taxonomies. 
Do NOT generate Framed Narratives or extensive analysis - keep it focused and efficient.

HEADLINES TO PROCESS ({len(titles_context)} titles from mixed sources and topics):
{self._format_titles_for_llm(titles_context)}

STANDARDIZED TAXONOMIES (MUST USE THESE EXACT VALUES):

EVENT_TYPE (choose exactly one):
- Strategy/Tactics: Military operations, defense planning, strategic movements
- Humanitarian: Refugee crises, disaster response, aid operations  
- Alliances/Geopolitics: NATO/alliance activities, coalition building, geopolitical shifts
- Diplomacy/Negotiations: Peace talks, diplomatic summits, treaty negotiations
- Sanctions/Economy: Economic sanctions, trade wars, economic diplomacy
- Domestic Politics: Internal politics, elections, domestic policy changes
- Procurement/Force-gen: Military procurement, force generation, defense industry
- Tech/Cyber/OSINT: Cyber operations, technology warfare, intelligence operations
- Legal/ICC: International law, war crimes, legal proceedings
- Information/Media/Platforms: Media operations, information warfare, platform policies
- Energy/Infrastructure: Energy security, infrastructure attacks, resource conflicts

PRIMARY_THEATER (choose exactly one):
- UKRAINE: Ukraine conflict theater (Russia-Ukraine war zone)
- GAZA: Gaza/Palestine theater (Israel-Palestine conflict zone)
- TAIWAN_STRAIT: Taiwan Strait theater (China-Taiwan tensions)
- IRAN_NUCLEAR: Iran nuclear program and sanctions
- EUROPE_SECURITY: European/NATO security matters
- US_DOMESTIC: US internal politics and domestic policy
- CHINA_TRADE: US-China economic competition
- MEAST_REGIONAL: Broader Middle East conflicts
- CYBER_GLOBAL: Global cyber operations
- CLIMATE_GLOBAL: Climate/energy security issues
- AFRICA_SECURITY: African conflicts and operations
- KOREA_PENINSULA: North Korea nuclear program
- LATAM_REGIONAL: Latin America regional politics
- ARCTIC: Arctic sovereignty and competition
- GLOBAL_SUMMIT: International summits and diplomacy

INSTRUCTIONS:
1. Group headlines into LONG-LIVED EVENT FAMILIES representing ongoing strategic situations
2. Use canonical actor names from our databases (e.g., "Donald Trump", "Vladimir Putin", "NATO")
3. Choose PRIMARY_THEATER and EVENT_TYPE from the standardized lists above (EXACT spelling required)
4. Create comprehensive families that can absorb future related incidents
5. Focus on key_actors + primary_theater + event_type coherence for ef_key generation
6. Create 3-12 Event Families maximum (prioritize consolidation over fragmentation)

RESPOND IN THIS JSON FORMAT:
{{
    "event_families": [
        {{
            "title": "Strategic, long-lived family title",
            "summary": "Comprehensive 2-3 sentence summary covering the ongoing situation",
            "key_actors": ["Canonical Name 1", "Canonical Name 2"],
            "event_type": "EXACT value from EVENT_TYPE list above",
            "primary_theater": "EXACT value from PRIMARY_THEATER list above",
            "event_start": "2025-09-11T10:00:00+00:00",
            "event_end": "2025-09-11T12:00:00+00:00",
            "source_title_ids": ["headline_id_1", "headline_id_2"],
            "confidence_score": 0.85,
            "coherence_reason": "Why these headlines form a strategic, long-lived Event Family"
        }}
    ]
}}

CRITICAL: Use ONLY the exact event_type and primary_theater values listed above. This enables deterministic ef_key generation for continuous merging."""

        try:
            # Create LLM request
            request = LLMEventFamilyRequest(
                title_context=titles_context,
                processing_instructions=prompt,
                max_event_families=20,  # Allow more intelligent content-driven EF generation
            )

            response = await self.llm_client.assemble_event_families_from_titles(
                request
            )

            # Parse response
            if hasattr(response, "event_families"):
                return {"event_families": response.event_families}
            else:
                return response

        except Exception as e:
            logger.error(f"Pass 1 LLM generation failed: {e}")
            raise

    def _format_titles_for_llm(self, titles_context: List[Dict[str, Any]]) -> str:
        """Format titles for LLM prompt"""
        formatted = []
        for title in titles_context:
            actors_str = (
                ", ".join(title.get("actors", [])) if title.get("actors") else "None"
            )
            formatted.append(
                f"{title['headline_id']}: {title['headline']} "
                f"[{title['source']}, {title['pubdate']}, actors: {actors_str}]"
            )
        return "\n".join(formatted)

    async def run_pass2_cross_merging(
        self,
        max_event_families: Optional[int] = None,
        generate_narratives: bool = True,
        dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Pass 2: Cross-merge Event Families and generate Framed Narratives

        Analyzes existing Event Families for potential merging opportunities
        and generates Framed Narratives for final Event Families.

        Args:
            max_event_families: Maximum EFs to analyze (None for all recent)
            generate_narratives: Whether to generate Framed Narratives
            dry_run: Don't save changes to database

        Returns:
            ProcessingResult with merged EFs and Framed Narratives
        """
        start_time = datetime.now()
        logger.info("=== GEN-1 PASS 2: Cross-Merging & Narrative Generation ===")

        try:
            # Get recent Event Families for cross-analysis
            event_families = await self.db.get_event_families(
                since_hours=48, limit=max_event_families  # Look at last 2 days
            )

            if not event_families:
                logger.warning("No Event Families found for Pass 2")
                return ProcessingResult(
                    total_titles_processed=0,
                    event_families=[],
                    framed_narratives=[],
                    success_rate=0.0,
                    processing_time_seconds=0.0,
                    errors=["No Event Families found for Pass 2"],
                    warnings=[],
                )

            logger.info(
                f"Found {len(event_families)} Event Families for Pass 2 analysis"
            )

            # Analyze for merge opportunities
            merged_families = await self._analyze_merge_opportunities(
                event_families, dry_run
            )

            # Generate Framed Narratives if requested
            all_narratives = []
            processing_errors = []
            processing_warnings = []

            if generate_narratives:
                logger.info("Generating Framed Narratives for Event Families...")

                # Get Event Families to process (merged ones or original ones)
                families_to_process = (
                    merged_families if merged_families else event_families[:10]
                )  # Limit for testing

                for i, event_family in enumerate(families_to_process, 1):
                    logger.info(
                        f"Pass 2: Generating narratives for EF {i}/{len(families_to_process)}: {event_family.title}"
                    )

                    try:
                        # Get associated titles for this Event Family
                        titles_context = await self._get_titles_for_event_family(
                            event_family
                        )

                        if len(titles_context) < 2:
                            processing_warnings.append(
                                f"EF '{event_family.title}' has insufficient titles for narrative analysis"
                            )
                            continue

                        # Generate Framed Narratives
                        narratives = await self._generate_framed_narratives(
                            event_family, titles_context
                        )

                        for narrative in narratives:
                            if not dry_run:
                                if await self.db.save_framed_narrative(narrative):
                                    logger.debug(
                                        f"Saved Framed Narrative: {narrative.frame_type}"
                                    )
                                else:
                                    processing_errors.append(
                                        f"Failed to save narrative for EF: {event_family.title}"
                                    )

                            all_narratives.append(narrative)

                    except Exception as e:
                        logger.error(
                            f"Pass 2: Error generating narratives for EF {event_family.title}: {e}"
                        )
                        processing_errors.append(f"EF {event_family.title}: {e}")
                        continue

            # Calculate final stats
            processing_time = (datetime.now() - start_time).total_seconds()
            success_rate = (
                len(all_narratives) / max(len(event_families), 1)
                if all_narratives
                else 0.0
            )

            logger.info(
                f"Pass 2 completed: {len(merged_families)} merged EFs, {len(all_narratives)} Framed Narratives",
                processing_time=f"{processing_time:.1f}s",
                success_rate=f"{success_rate:.1%}",
            )

            return ProcessingResult(
                total_titles_processed=0,  # Pass 2 processes EFs, not titles
                event_families=merged_families,
                framed_narratives=all_narratives,
                success_rate=success_rate,
                processing_time_seconds=processing_time,
                errors=processing_errors,
                warnings=processing_warnings,
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Pass 2 failed: {e}")
            return ProcessingResult(
                total_titles_processed=0,
                event_families=[],
                framed_narratives=[],
                success_rate=0.0,
                processing_time_seconds=processing_time,
                errors=[f"Pass 2 failed: {e}"],
                warnings=[],
            )

    async def _analyze_merge_opportunities(
        self, event_families: List[EventFamily], dry_run: bool
    ) -> List[EventFamily]:
        """
        Analyze Event Families for potential merging opportunities using LLM intelligence

        Args:
            event_families: List of Event Families to analyze
            dry_run: Don't save changes to database

        Returns:
            List of merged Event Families (empty if no merging needed)
        """
        logger.info(
            f"Analyzing {len(event_families)} Event Families for merge opportunities"
        )

        try:
            # Build comprehensive context for merging analysis
            ef_context = []
            for i, ef in enumerate(event_families):
                ef_context.append(
                    {
                        "id": ef.id,
                        "index": i,
                        "title": ef.title,
                        "summary": ef.summary,
                        "key_actors": ef.key_actors,
                        "event_type": ef.event_type,
                        "geography": ef.geography,
                        "event_start": (
                            ef.event_start.strftime("%Y-%m-%d %H:%M")
                            if ef.event_start
                            else "Unknown"
                        ),
                        "event_end": (
                            ef.event_end.strftime("%Y-%m-%d %H:%M")
                            if ef.event_end
                            else "Unknown"
                        ),
                        "title_count": len(ef.source_title_ids),
                        "confidence": ef.confidence_score,
                    }
                )

            # Generate merging analysis using LLM
            merge_analysis = await self._generate_merge_analysis(ef_context)

            # Process merge recommendations
            merged_families = []
            if merge_analysis.get("merge_groups"):
                logger.info(f"Found {len(merge_analysis['merge_groups'])} merge groups")

                for group_info in merge_analysis["merge_groups"]:
                    # Get Event Families to merge
                    ef_indices = group_info.get("event_family_indices", [])
                    families_to_merge = [
                        event_families[i] for i in ef_indices if i < len(event_families)
                    ]

                    if len(families_to_merge) < 2:
                        continue

                    # Create merged Event Family
                    merged_ef = await self._merge_event_families(
                        families_to_merge, group_info, dry_run
                    )
                    if merged_ef:
                        merged_families.append(merged_ef)
                        logger.info(
                            f"Merged {len(families_to_merge)} EFs into: {merged_ef.title}"
                        )

            # Add non-merged Event Families
            merged_indices = set()
            for group_info in merge_analysis.get("merge_groups", []):
                merged_indices.update(group_info.get("event_family_indices", []))

            for i, ef in enumerate(event_families):
                if i not in merged_indices:
                    merged_families.append(ef)

            logger.info(
                f"Pass 2 merging: {len(event_families)} → {len(merged_families)} Event Families"
            )
            return merged_families

        except Exception as e:
            logger.error(f"EF merging analysis failed: {e}")
            # Return original Event Families if merging fails
            return event_families

    async def _get_titles_for_event_family(
        self, event_family: EventFamily
    ) -> List[Dict[str, Any]]:
        """
        Get title contexts for an Event Family for narrative analysis

        Args:
            event_family: Event Family to get titles for

        Returns:
            List of title context dictionaries
        """
        try:

            with get_db_session() as session:

                if not event_family.source_title_ids:
                    return []

                # Build query to get title details
                uuid_list = (
                    "ARRAY["
                    + ",".join(
                        [
                            f"'{title_id}'::uuid"
                            for title_id in event_family.source_title_ids
                        ]
                    )
                    + "]"
                )

                query = f"""
                SELECT 
                    id, title_display as text, url_gnews as url,
                    publisher_name as source, pubdate_utc,
                    detected_language as language
                FROM titles 
                WHERE id = ANY({uuid_list})
                ORDER BY pubdate_utc ASC
                """

                results = session.execute(text(query)).fetchall()

                titles_context = []
                for row in results:
                    titles_context.append(
                        {
                            "id": str(row.id),
                            "text": row.text,
                            "source": row.source,
                            "pubdate": (
                                row.pubdate_utc.strftime("%Y-%m-%d %H:%M")
                                if row.pubdate_utc
                                else "Unknown"
                            ),
                            "language": row.language,
                        }
                    )

                logger.debug(
                    f"Retrieved {len(titles_context)} titles for EF: {event_family.title}"
                )
                return titles_context

        except Exception as e:
            logger.error(
                f"Failed to get titles for Event Family {event_family.id}: {e}"
            )
            return []

    async def _generate_framed_narratives(
        self, event_family: EventFamily, titles_context: List[Dict[str, Any]]
    ) -> List[FramedNarrative]:
        """
        Generate Framed Narratives for an Event Family

        Args:
            event_family: Event Family to generate narratives for
            titles_context: List of title contexts

        Returns:
            List of FramedNarrative objects
        """
        try:
            # Create request for Framed Narrative generation
            framing_instructions = """
            Analyze how different outlets frame this Event Family and identify distinct perspectives.
            Focus on evaluative language, causal attributions, and stance differences.
            Generate 1-3 dominant framings with strong textual evidence.
            """

            request = LLMFramedNarrativeRequest(
                event_family=event_family,
                titles_context=titles_context,
                framing_instructions=framing_instructions,
                max_narratives=3,
            )

            # Generate narratives using LLM
            response = await self.llm_client.generate_framed_narratives(request)

            # Convert to FramedNarrative objects
            narratives = []
            for fn_data in response.framed_narratives:
                narrative = FramedNarrative(
                    event_family_id=event_family.id,
                    frame_type=fn_data.get("frame_type", "Unknown"),
                    frame_description=fn_data.get("frame_description", ""),
                    stance_summary=fn_data.get("stance_summary", ""),
                    supporting_headlines=fn_data.get("supporting_headlines", []),
                    supporting_title_ids=fn_data.get("supporting_title_ids", []),
                    key_language=fn_data.get("key_language", []),
                    prevalence_score=fn_data.get("prevalence_score", 0.5),
                    evidence_quality=fn_data.get("evidence_quality", 0.5),
                )
                narratives.append(narrative)

            logger.debug(
                f"Generated {len(narratives)} Framed Narratives for EF: {event_family.title}"
            )
            return narratives

        except Exception as e:
            logger.error(
                f"Failed to generate Framed Narratives for EF {event_family.id}: {e}"
            )
            return []

    async def _generate_merge_analysis(
        self, ef_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate LLM analysis for Event Family merging opportunities

        Args:
            ef_context: List of Event Family context dictionaries

        Returns:
            Dictionary with merge recommendations
        """
        # Build comprehensive prompt for merge analysis
        prompt = f"""You are analyzing {len(ef_context)} Event Families for potential merging opportunities.

ANTI-FRAGMENTATION OBJECTIVE: Consolidate Event Families that represent the same real-world strategic event or ongoing situation. Fight political information fragmentation by creating coherent, comprehensive Event Families.

EVENT FAMILIES TO ANALYZE:
"""

        for ef in ef_context:
            prompt += f"""
EF{ef['index']}: {ef['title']}
  Summary: {ef['summary']}
  Actors: {', '.join(ef['key_actors'])}
  Type: {ef['event_type']}
  Geography: {ef['geography']}
  Timeframe: {ef['event_start']} to {ef['event_end']}
  Title Count: {ef['title_count']} headlines
  Confidence: {ef['confidence']:.2f}
"""

        prompt += """
MERGE ANALYSIS CRITERIA:

1. **Same Strategic Event**: Multiple EFs describing the same real-world happening
   - Example: "Russia-Ukraine Conflict Escalation" + "Ukrainian Defense Operations" → Same conflict

2. **Shared Actor Set**: Overlapping key actors in similar contexts
   - Example: "Trump Immigration Policy" + "Trump Border Security" → Same administration policy

3. **Geographic/Temporal Coherence**: Same location and time period
   - Example: "Gaza Military Operations" + "Gaza Humanitarian Crisis" → Same theater/timeframe

4. **Thematic Unity**: Related aspects of the same strategic situation
   - Example: "Iran Nuclear Negotiations" + "Iran Sanctions Crisis" → Same policy area

MERGE QUALITY REQUIREMENTS:
- Only merge EFs with genuine strategic coherence (not just keyword overlap)
- Prioritize comprehensive, unified narratives over fragmented micro-events
- Maintain actor canonicalization (treat equivalent actors as unified)
- Preserve essential details from all constituent EFs

RESPONSE FORMAT (JSON):
{
    "merge_groups": [
        {
            "event_family_indices": [0, 3, 7],
            "merge_rationale": "Clear explanation of why these EFs should merge",
            "merged_title": "Comprehensive title for merged EF",
            "merged_summary": "Unified 3-4 sentence summary covering all constituent events",
            "unified_actors": ["Actor1", "Actor2"],
            "unified_geography": "Geographic scope",
            "confidence": 0.85
        }
    ],
    "standalone_event_families": [1, 2, 4, 5, 6, 8, 9],
    "analysis_reasoning": "Overall approach and methodology for merge decisions",
    "anti_fragmentation_impact": "How merging reduces information fragmentation"
}

Only recommend merges with high confidence (0.8+). Be conservative but strategic - fight fragmentation while maintaining semantic accuracy.
"""

        try:
            # Call LLM for merge analysis
            response_text = await self.llm_client._call_llm(
                system_prompt="You are an expert in strategic news analysis and information consolidation. Your goal is to fight political information fragmentation by identifying genuine merge opportunities between Event Families.",
                user_prompt=prompt,
                max_tokens=2000,
                temperature=0.1,
            )

            # Parse JSON response
            merge_analysis = self.llm_client._extract_json(response_text)
            logger.info(
                f"Merge analysis completed: {len(merge_analysis.get('merge_groups', []))} potential merges identified"
            )

            return merge_analysis

        except Exception as e:
            logger.error(f"Merge analysis LLM call failed: {e}")
            return {
                "merge_groups": [],
                "standalone_event_families": list(range(len(ef_context))),
            }

    async def _merge_event_families(
        self,
        families_to_merge: List[EventFamily],
        group_info: Dict[str, Any],
        dry_run: bool,
    ) -> Optional[EventFamily]:
        """
        Merge multiple Event Families into a single consolidated Event Family

        Args:
            families_to_merge: List of Event Families to merge
            group_info: Merge group information from LLM analysis
            dry_run: Don't save to database

        Returns:
            Merged EventFamily object or None if merge fails
        """
        try:
            # Aggregate data from all constituent Event Families
            all_title_ids = []
            all_actors = set()
            earliest_start = None
            latest_end = None
            total_confidence = 0

            for ef in families_to_merge:
                all_title_ids.extend(ef.source_title_ids)
                all_actors.update(ef.key_actors)

                if earliest_start is None or (
                    ef.event_start and ef.event_start < earliest_start
                ):
                    earliest_start = ef.event_start

                if latest_end is None or (ef.event_end and ef.event_end > latest_end):
                    latest_end = ef.event_end

                total_confidence += ef.confidence_score

            # Create merged Event Family
            merged_ef = EventFamily(
                title=group_info.get(
                    "merged_title", f"Merged: {families_to_merge[0].title}"
                ),
                summary=group_info.get(
                    "merged_summary", "Consolidated Event Family from multiple sources"
                ),
                key_actors=list(group_info.get("unified_actors", all_actors))[
                    :10
                ],  # Limit actors
                event_type=f"Consolidated: {families_to_merge[0].event_type}",
                geography=group_info.get(
                    "unified_geography", families_to_merge[0].geography
                ),
                event_start=earliest_start,
                event_end=latest_end,
                source_title_ids=list(set(all_title_ids)),  # Deduplicate title IDs
                confidence_score=min(
                    total_confidence / len(families_to_merge),
                    group_info.get("confidence", 0.8),
                ),
                coherence_reason=f"Pass 2 merge: {group_info.get('merge_rationale', 'Consolidated for anti-fragmentation')}",
                processing_notes=f"Pass 2 merge of {len(families_to_merge)} EFs: {[ef.id for ef in families_to_merge]}",
            )

            if not dry_run:
                # Save merged Event Family
                if await self.db.save_event_family(merged_ef):
                    # Update title assignments to point to merged EF
                    await self.db.assign_titles_to_event_family(
                        title_ids=merged_ef.source_title_ids,
                        event_family_id=merged_ef.id,
                        confidence=merged_ef.confidence_score,
                        reason=f"Pass 2 merge consolidation: {len(families_to_merge)} EFs combined",
                    )

                    # TODO: Archive/mark original Event Families as merged
                    logger.info(
                        f"Saved merged EF: {merged_ef.id} with {len(merged_ef.source_title_ids)} titles"
                    )
                else:
                    logger.error(
                        f"Failed to save merged Event Family: {merged_ef.title}"
                    )
                    return None

            return merged_ef

        except Exception as e:
            logger.error(f"Failed to merge Event Families: {e}")
            return None

    async def _llm_merge_decision(
        self, event_families: List[EventFamily], theater: str, event_type: str
    ) -> Dict[str, Any]:
        """
        Use LLM to decide if Event Families with same theater+event_type should be merged

        Args:
            event_families: List of Event Families to potentially merge
            theater: Primary theater they share
            event_type: Event type they share

        Returns:
            Dictionary with merge decision and reasoning
        """
        try:
            # Build context for merge decision
            efs_context = []
            for i, ef in enumerate(event_families):
                efs_context.append(
                    {
                        "index": i,
                        "title": ef.title,
                        "summary": ef.summary,
                        "key_actors": ef.key_actors,
                        "ef_key": ef.ef_key,
                        "title_count": len(ef.source_title_ids),
                        "confidence": ef.confidence_score,
                    }
                )

            prompt = f"""You are deciding whether to merge Event Families that share the same theater ({theater}) and event_type ({event_type}).

MERGE DECISION CRITERIA:
- Event Families should be merged if they represent different aspects of the SAME strategic situation
- Consider if the actor sets are complementary rather than conflicting
- Merge families that would benefit from unified strategic narrative
- Do NOT merge if they represent genuinely separate events or conflicting perspectives

EVENT FAMILIES TO ANALYZE:
"""

            for ef in efs_context:
                prompt += f"""
EF{ef['index']}: {ef['title']}
  Summary: {ef['summary']}
  Actors: {', '.join(ef['key_actors'])}
  EF_Key: {ef['ef_key']}
  Headlines: {ef['title_count']}
  Confidence: {ef['confidence']:.2f}
"""

            prompt += """
ANALYSIS REQUIRED:
1. Do these Event Families represent the same strategic situation from different angles?
2. Would merging create a more comprehensive, unified Event Family?
3. Are the actor sets compatible (not representing opposing sides)?
4. Would the merged family provide better strategic intelligence?

RESPOND IN THIS JSON FORMAT:
{{
    "should_merge": true/false,
    "merge_rationale": "Clear explanation of decision",
    "merged_title": "Title for merged EF (if merging)",
    "merged_summary": "Comprehensive summary (if merging)",
    "merged_actors": ["Actor1", "Actor2", "Actor3"],
    "confidence": 0.85,
    "strategic_benefit": "How merging improves strategic intelligence"
}}

Focus on creating comprehensive Event Families that provide unified strategic narratives rather than fragmented micro-events."""

            # Call LLM for merge decision
            response_text = await self.llm_client._call_llm(
                system_prompt="You are an expert in strategic intelligence consolidation. Your goal is to create comprehensive Event Families that provide unified strategic narratives while avoiding inappropriate mergers.",
                user_prompt=prompt,
                max_tokens=1500,
                temperature=0.1,
            )

            # Parse JSON response
            merge_decision = self.llm_client._extract_json(response_text)
            logger.info(
                f"Merge decision for {theater}/{event_type}: {merge_decision.get('should_merge', False)}"
            )

            return merge_decision

        except Exception as e:
            logger.error(f"LLM merge decision failed: {e}")
            # Default to no merge on error
            return {"should_merge": False, "merge_rationale": f"Error in analysis: {e}"}

    async def _execute_ef_merge(
        self,
        event_families: List[EventFamily],
        merge_decision: Dict[str, Any],
        dry_run: bool,
    ) -> Optional[EventFamily]:
        """
        Execute the merge of multiple Event Families based on LLM decision

        Args:
            event_families: List of Event Families to merge
            merge_decision: LLM decision with merge details
            dry_run: Don't save to database

        Returns:
            Merged EventFamily object or None if merge fails
        """
        try:
            if not event_families or len(event_families) < 2:
                return None

            # Aggregate data from all Event Families
            all_title_ids = []
            all_actors = set()
            earliest_start = None
            latest_end = None
            total_confidence = 0

            for ef in event_families:
                all_title_ids.extend(ef.source_title_ids)
                all_actors.update(ef.key_actors)

                if earliest_start is None or (
                    ef.event_start and ef.event_start < earliest_start
                ):
                    earliest_start = ef.event_start

                if latest_end is None or (ef.event_end and ef.event_end > latest_end):
                    latest_end = ef.event_end

                total_confidence += ef.confidence_score

            # Use LLM-provided details or defaults
            merged_actors = merge_decision.get(
                "merged_actors", list(all_actors)[:10]
            )  # Limit actors
            merged_title = merge_decision.get(
                "merged_title", f"Merged: {event_families[0].title}"
            )
            merged_summary = merge_decision.get(
                "merged_summary",
                f"Consolidated Event Family from {len(event_families)} sources",
            )

            # Generate new ef_key for merged family
            merged_ef_key = generate_ef_key_from_data(
                {
                    "key_actors": merged_actors,
                    "primary_theater": event_families[0].primary_theater,
                    "event_type": event_families[0].event_type,
                }
            )

            # Create merged Event Family
            merged_ef = EventFamily(
                title=merged_title,
                summary=merged_summary,
                key_actors=merged_actors,
                event_type=event_families[0].event_type,
                primary_theater=event_families[0].primary_theater,
                ef_key=merged_ef_key,
                event_start=earliest_start,
                event_end=latest_end,
                source_title_ids=list(set(all_title_ids)),  # Deduplicate
                confidence_score=min(
                    total_confidence / len(event_families),
                    merge_decision.get("confidence", 0.8),
                ),
                coherence_reason=f"Pass 2A merge: {merge_decision.get('merge_rationale', 'Strategic consolidation')}",
                processing_notes=f"Pass 2A merge of {len(event_families)} EFs: {[ef.id for ef in event_families]}",
            )

            if not dry_run:
                # Save merged Event Family
                success = await self.db.save_event_family(merged_ef)
                if success:
                    # Mark original EFs as merged
                    await self._mark_efs_as_merged(
                        event_families,
                        merged_ef.id,
                        merge_decision.get("merge_rationale", ""),
                    )

                    # Update title assignments to point to merged EF
                    await self.db.assign_titles_to_event_family(
                        title_ids=merged_ef.source_title_ids,
                        event_family_id=merged_ef.id,
                        confidence=merged_ef.confidence_score,
                        reason=f"Pass 2A merge consolidation: {len(event_families)} EFs combined",
                    )

                    logger.info(
                        f"Saved merged EF: {merged_ef.id} with {len(merged_ef.source_title_ids)} titles"
                    )
                else:
                    logger.error(
                        f"Failed to save merged Event Family: {merged_ef.title}"
                    )
                    return None

            return merged_ef

        except Exception as e:
            logger.error(f"Failed to execute EF merge: {e}")
            return None

    async def _mark_efs_as_merged(
        self, original_efs: List[EventFamily], merged_ef_id: str, rationale: str
    ) -> None:
        """Mark original Event Families as merged into the new EF"""
        try:
            with get_db_session() as session:
                for ef in original_efs:
                    update_query = """
                    UPDATE event_families 
                    SET status = 'merged',
                        merged_into = :merged_ef_id,
                        merge_rationale = :rationale,
                        updated_at = NOW()
                    WHERE id = :ef_id
                    """

                    session.execute(
                        text(update_query),
                        {
                            "merged_ef_id": merged_ef_id,
                            "rationale": rationale[:500],  # Truncate if too long
                            "ef_id": ef.id,
                        },
                    )

                logger.info(
                    f"Marked {len(original_efs)} EFs as merged into {merged_ef_id}"
                )

        except Exception as e:
            logger.error(f"Failed to mark EFs as merged: {e}")
            # Don't raise - this is cleanup, shouldn't fail the main operation


def get_multipass_processor() -> MultiPassProcessor:
    """Factory function to get multipass processor"""
    return MultiPassProcessor()


if __name__ == "__main__":
    # CLI usage for testing
    import asyncio
    import sys

    async def main():
        processor = get_multipass_processor()

        if len(sys.argv) > 1 and sys.argv[1] == "pass1":
            # Test Pass 1
            max_titles = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            result = await processor.run_pass1_entity_assembly(
                max_titles=max_titles,
                batch_size=max_titles
                or 100,  # Use max_titles as batch_size for testing
                dry_run="--dry-run" in sys.argv,
            )

            print("\nPass 1 Results:")
            print(f"  {result.total_titles_processed} titles processed")
            print(f"  {len(result.event_families)} Event Families created")
            print(f"  {len(result.errors)} errors")
            print(f"  Processing time: {result.processing_time_seconds:.1f}s")

        elif len(sys.argv) > 1 and sys.argv[1] == "pass2a":
            # Test Pass 2A (EF merging)
            max_efs = int(sys.argv[2]) if len(sys.argv) > 2 else None
            result = await processor.run_pass2a_ef_merging(
                max_event_families=max_efs, dry_run="--dry-run" in sys.argv
            )

            print("\nPass 2A Results:")
            print(f"  {len(result.event_families)} Event Families after merging")
            print(f"  {len(result.errors)} errors")
            print(f"  {len(result.warnings)} warnings")
            print(f"  Processing time: {result.processing_time_seconds:.1f}s")

        elif len(sys.argv) > 1 and sys.argv[1] == "pass2":
            # Test Pass 2 (original cross-merging + narratives)
            max_efs = int(sys.argv[2]) if len(sys.argv) > 2 else None
            result = await processor.run_pass2_cross_merging(
                max_event_families=max_efs,
                generate_narratives=True,
                dry_run="--dry-run" in sys.argv,
            )

            print("\nPass 2 Results:")
            print(f"  {len(result.event_families)} Event Families merged")
            print(f"  {len(result.framed_narratives)} Framed Narratives created")
            print(f"  {len(result.errors)} errors")
            print(f"  {len(result.warnings)} warnings")
            print(f"  Processing time: {result.processing_time_seconds:.1f}s")

        else:
            print(
                "Usage: python -m apps.generate.multipass_processor [pass1|pass2a|pass2] [max_items] [--dry-run]"
            )
            print("  pass1: Run Pass 1 (EF assembly from titles)")
            print("  pass2a: Run Pass 2A (EF merging by theater+type)")
            print("  pass2: Run Pass 2 (EF cross-merging and narrative generation)")
            print(
                "  max_items: Maximum titles (pass1) or Event Families (pass2a/pass2) to process"
            )

    asyncio.run(main())
