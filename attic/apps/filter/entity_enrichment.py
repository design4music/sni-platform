#!/usr/bin/env python3
"""
Phase 2A: Entity Enrichment Service
Combines CLUST-1 strategic filtering and CLUST-2 actor extraction
to populate titles.entities jsonb column for bucketless processing.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy import text

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor
from apps.filter.title_processor_helpers import (update_processing_stats,
                                                 update_title_entities)
from apps.filter.vocab_loader_db import (load_actor_aliases,
                                         load_go_people_aliases)
from core.config import get_config
from core.database import get_db_session
from core.llm_client import LLMClient, build_aat_extraction_prompt
from core.neo4j_sync import get_neo4j_sync


class EntityEnrichmentService:
    """
    Service to enrich titles with extracted entities in Phase 2A.

    Combines strategic filtering (CLUST-1) + actor extraction (CLUST-2)
    to populate titles.entities column for direct GEN-1 processing.

    Logic:
    - actors + people = positive entities (store these)
    - stop_culture = negative filter (don't store, just blocks is_strategic)
    """

    def __init__(self):
        self.taxonomy_extractor = create_multi_vocab_taxonomy_extractor()
        self.llm_client = LLMClient()
        self.neo4j_sync = get_neo4j_sync()
        self.config = get_config()

        # Load entity vocabularies for matching LLM-extracted entities
        self._entity_vocab = None
        self._entity_lookup = None

    async def extract_entities_for_title(
        self, title_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract entities for a single title.

        Args:
            title_data: Title record with title_display, url, etc.

        Returns:
            entities dict with structure:
            {
                "actors": ["Germany", "NATO"],
                "people": ["Scholz", "Biden"],
                "is_strategic": false,  // blocked by stop_culture match
                "extraction_version": "2.0"
            }
        """
        title_text = title_data.get("title_display", "")
        if not title_text:
            return self._empty_entities()

        # Phase 1: Static taxonomy filtering
        strategic_hit = self.taxonomy_extractor.strategic_first_hit(title_text)
        is_strategic = strategic_hit is not None

        # Get all strategic actors if hit by static taxonomy
        all_entities = []
        neo4j_override = False
        neo4j_reason = None

        if is_strategic:
            # all_strategic_hits already includes country enrichment
            all_entities = self.taxonomy_extractor.all_strategic_hits(title_text)
        else:
            # Phase 2: LLM review for ambiguous titles (no positive hits)
            # Only call LLM if no static taxonomy match
            llm_result = await self._llm_strategic_review(title_text)
            is_strategic = llm_result["is_strategic"]

            # Match LLM-extracted entities against data_entities table
            llm_raw_entities = llm_result.get("entities", [])
            if llm_raw_entities:
                # Match raw LLM strings to canonical entity names (name_en)
                matched_entity_names = self._match_llm_entities(llm_raw_entities)
                if matched_entity_names:
                    # Auto-add countries for detected people (based on iso_code)
                    from apps.filter.country_enrichment import \
                        enrich_entities_with_countries

                    enriched_entity_names = enrich_entities_with_countries(
                        matched_entity_names
                    )
                    all_entities.extend(enriched_entity_names)
                    logger.debug(
                        f"LLM extracted and matched entities for '{title_text[:50]}': "
                        f"{llm_raw_entities} → {enriched_entity_names}"
                    )
                else:
                    logger.debug(
                        f"LLM extracted entities but no matches: {llm_raw_entities}"
                    )
            # If LLM flags as strategic but no entities found, keep empty array
            # gate_keep=true + entities=[] means strategic without specific actors

            # Phase 3: Neo4j network intelligence override
            # If LLM says non-strategic, check if Neo4j signals suggest otherwise
            if not is_strategic and title_data.get("id"):
                neo4j_decision = await self._neo4j_strategic_override(title_data["id"])
                if neo4j_decision.get("override"):
                    is_strategic = True
                    neo4j_override = True
                    neo4j_reason = neo4j_decision.get("reason")
                    logger.info(
                        f"Neo4j override for '{title_text[:50]}': {neo4j_reason}"
                    )

        # Store just the actors array (gate_keep column tracks strategic status)
        log_msg = (
            f"Extracted entities for '{title_text[:50]}': "
            f"entities={len(all_entities)}, strategic={is_strategic}"
        )
        if neo4j_override:
            log_msg += f" (Neo4j: {neo4j_reason})"
        logger.debug(log_msg)

        return {"actors": all_entities, "is_strategic": is_strategic}

    async def extract_aat_triple(self, title_text: str) -> Dict[str, str]:
        """
        Extract Actor-Action-Target triple from title.

        This extracts the core semantic structure of a title for graph-pattern clustering.
        Only called for strategic titles (gate_keep=true) to optimize performance.

        Args:
            title_text: Title text to analyze

        Returns:
            Dict with {"actor": str|None, "action": str|None, "target": str|None}
            All fields are None if extraction fails or no clear action pattern
        """
        if not self.config.phase_2_aat_enabled:
            return {"actor": None, "action": None, "target": None}

        system_prompt, user_prompt = build_aat_extraction_prompt(title_text)

        try:
            response = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.phase_2_aat_max_tokens,
                temperature=self.config.phase_2_aat_temperature,
            )

            answer = response.strip()

            # Parse ACTOR|ACTION|TARGET
            parts = answer.split("|")
            if len(parts) == 3:
                # Convert "null" string to None, or empty strings to None
                actor = parts[0].strip()
                actor = None if actor.lower() == "null" or not actor else actor

                action = parts[1].strip().lower()
                action = None if action == "null" or not action else action

                target = parts[2].strip()
                target = None if target.lower() == "null" or not target else target

                return {
                    "actor": actor,
                    "action": action,
                    "target": target,
                }
            else:
                logger.warning(f"Invalid AAT format (expected 3 parts): {answer}")
                return {"actor": None, "action": None, "target": None}

        except Exception as e:
            logger.error(f"AAT extraction failed for '{title_text[:50]}': {e}")
            return {"actor": None, "action": None, "target": None}

    async def _llm_strategic_review(self, title_text: str) -> Dict[str, Any]:
        """
        Use LLM to determine if ambiguous title is strategic and extract entities.
        Called only for titles that don't match static taxonomy.

        Returns:
            Dict with:
                - is_strategic (bool): True if strategic, False if not
                - entities (List[str]): Extracted entities/actors
                - reason (str): Brief explanation of decision
        """
        return await self.llm_client.strategic_review(title_text)

    async def _neo4j_strategic_override(self, title_id: str) -> Dict[str, Any]:
        """
        Use Neo4j network patterns to override LLM decisions for borderline cases.

        Multi-signal scoring approach for sparse entity scenarios:
        - Signal 1: Entity Centrality (contains hot entities) → +2 points
        - Signal 2: Strategic Neighborhood (connected to strategic cluster) → +1 point
        - Signal 3: Ongoing Event (part of temporal pattern) → +1 point

        If total score >= 2, override LLM decision to strategic.

        Args:
            title_id: Title UUID to analyze

        Returns:
            Dict with:
                - override: Boolean, whether to override to strategic
                - reason: String explanation of override decision
                - score: Integer strategic score
        """
        try:
            # Get all three Neo4j intelligence signals
            signals = await self.neo4j_sync.analyze_strategic_signals(title_id)

            strategic_score = 0
            reasons = []

            # Signal 1: Entity Centrality (how important are my entities?)
            if signals.get("high_centrality_entities", 0) >= 1:
                strategic_score += 2
                centrality_details = signals.get("centrality_details", [])
                entity_names = [e["entity"] for e in centrality_details[:2]]
                reasons.append(f"Hot entities: {', '.join(entity_names)}")

            # Signal 2: Strategic Neighborhood (am I near strategic content?)
            if signals.get("strategic_neighbor_strength", 0) >= 0.3:
                strategic_score += 1
                neighbor_count = signals.get("strategic_neighbors", 0)
                reasons.append(f"Connected to {neighbor_count} strategic titles")

            # Signal 3: Temporal Pattern (is this part of an ongoing story?)
            if signals.get("ongoing_event", False):
                strategic_score += 1
                reasons.append("Part of ongoing event")

            # Decision: override if score >= 2
            override = strategic_score >= 2

            return {
                "override": override,
                "reason": "; ".join(reasons) if reasons else "No strong signals",
                "score": strategic_score,
                "signals": signals,
            }

        except Exception as e:
            logger.error(f"Neo4j strategic override failed for {title_id}: {e}")
            return {"override": False, "reason": "Neo4j error", "score": 0}

    async def enrich_titles_batch(
        self, title_ids: List[str] = None, limit: int = 1000, since_hours: int = 24
    ) -> Dict[str, int]:
        """
        Enrich a batch of titles with entities.

        Args:
            title_ids: Specific title IDs to process (optional)
            limit: Max titles to process
            since_hours: Only process titles from last N hours (if title_ids not specified)

        Returns:
            stats dict with counts
        """
        stats = {
            "processed": 0,
            "strategic": 0,
            "non_strategic": 0,
            "blocked_by_stop": 0,
            "llm_calls": 0,
            "llm_strategic": 0,
            "errors": 0,
        }

        try:
            with get_db_session() as session:
                # Build query
                if title_ids:
                    # Build IN clause with UUID casting for PostgreSQL
                    placeholders = ",".join(
                        [f"'{uuid_str}'::uuid" for uuid_str in title_ids]
                    )
                    query = f"SELECT id, title_display, entities FROM titles WHERE id IN ({placeholders})"
                    params = {}
                else:
                    query = f"""
                    SELECT id, title_display, entities
                    FROM titles
                    WHERE created_at >= NOW() - INTERVAL '{since_hours} HOUR'
                    AND entities IS NULL
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                    params = {"limit": limit}

                # Get titles to process
                results = session.execute(text(query), params).fetchall()

                logger.info(f"Processing {len(results)} titles for entity extraction")

                # Process each title
                for row in results:
                    try:
                        title_data = {
                            "id": str(row.id),
                            "title_display": row.title_display,
                        }

                        # Extract entities (may involve LLM call)
                        entities = await self.extract_entities_for_title(title_data)

                        # Update database with simplified fields
                        is_strategic = entities["is_strategic"]

                        # Track LLM usage (strategic without specific entities = LLM decision)
                        if is_strategic and not entities.get("actors", []):
                            stats["llm_calls"] += 1
                            stats["llm_strategic"] += 1

                        # Use shared helper for DB update
                        update_title_entities(
                            session, title_data["id"], entities, is_strategic
                        )

                        # Use shared helper for stats tracking
                        update_processing_stats(stats, entities, is_strategic)

                    except Exception as e:
                        logger.error(f"Error processing title {row.id}: {e}")
                        stats["errors"] += 1
                        continue

                # Commit batch
                session.commit()

                logger.info(
                    f"Entity enrichment completed: {stats['processed']} processed, "
                    f"{stats['strategic']} strategic ({stats['llm_strategic']} via LLM), "
                    f"{stats['non_strategic']} non-strategic, LLM calls: {stats['llm_calls']}, "
                    f"{stats['errors']} errors"
                )

        except Exception as e:
            logger.error(f"Batch entity enrichment failed: {e}")
            stats["errors"] = len(title_ids) if title_ids else limit

        return stats

    def get_enrichment_status(self) -> Dict[str, int]:
        """Get status of entity enrichment across titles table."""
        try:
            with get_db_session() as session:
                status_query = """
                SELECT
                    COUNT(*) as total_titles,
                    COUNT(entities) as enriched_titles,
                    COUNT(CASE WHEN gate_keep = true THEN 1 END) as strategic_titles
                FROM titles
                WHERE created_at >= NOW() - INTERVAL '7 DAY'
                """

                result = session.execute(text(status_query)).fetchone()

                return {
                    "total_titles": result.total_titles or 0,
                    "enriched_titles": result.enriched_titles or 0,
                    "strategic_titles": result.strategic_titles or 0,
                    "enrichment_rate": (
                        result.enriched_titles / max(result.total_titles, 1)
                    )
                    * 100,
                }

        except Exception as e:
            logger.error(f"Failed to get enrichment status: {e}")
            return {"error": str(e)}

    def _empty_entities(self) -> Dict[str, Any]:
        """Return empty entities structure."""
        return {"actors": [], "is_strategic": False}

    def _load_entity_vocab(self) -> None:
        """
        Load entity vocabularies and build reverse lookup table.
        Lazy-loaded on first use to avoid database hits on initialization.
        """
        if self._entity_lookup is not None:
            return  # Already loaded

        logger.info("Loading entity vocabulary for LLM entity matching...")

        # Load actors and people from database
        actors = load_actor_aliases()
        people = load_go_people_aliases()

        # Combine into single vocabulary
        self._entity_vocab = {**actors, **people}

        # Build reverse lookup: alias (lowercase) -> entity_id
        self._entity_lookup = {}
        for entity_id, aliases in self._entity_vocab.items():
            for alias in aliases:
                alias_lower = alias.lower().strip()
                if alias_lower:
                    # Store best match (prefer shorter entity_ids for ambiguous aliases)
                    if alias_lower not in self._entity_lookup or len(entity_id) < len(
                        self._entity_lookup[alias_lower]
                    ):
                        self._entity_lookup[alias_lower] = entity_id

        logger.info(
            f"Entity vocabulary loaded: {len(self._entity_vocab)} entities, "
            f"{len(self._entity_lookup)} aliases"
        )

    def _match_llm_entities(self, llm_entities: List[str]) -> List[str]:
        """
        Match LLM-extracted entity strings against data_entities table.

        Args:
            llm_entities: Raw entity strings from LLM (e.g., ["United States", "Germany"])

        Returns:
            List of canonical entity names (name_en) (e.g., ["United States", "Germany"])
        """
        if not llm_entities:
            return []

        # Ensure vocabulary is loaded
        self._load_entity_vocab()

        matched_names = []
        seen_entity_ids = set()  # Track entity_ids to avoid duplicates

        for raw_entity in llm_entities:
            entity_lower = raw_entity.lower().strip()
            if not entity_lower:
                continue

            # Direct match
            if entity_lower in self._entity_lookup:
                entity_id = self._entity_lookup[entity_lower]
                if entity_id not in seen_entity_ids:
                    # Get canonical name_en (first alias in vocab)
                    name_en = self._entity_vocab[entity_id][0]
                    matched_names.append(name_en)
                    seen_entity_ids.add(entity_id)
                    logger.debug(
                        f"Matched '{raw_entity}' → '{name_en}' (entity_id: {entity_id})"
                    )
            else:
                # Partial match: check if raw_entity is contained in any alias
                found = False
                for alias, entity_id in self._entity_lookup.items():
                    if entity_lower in alias or alias in entity_lower:
                        if entity_id not in seen_entity_ids:
                            # Get canonical name_en (first alias in vocab)
                            name_en = self._entity_vocab[entity_id][0]
                            matched_names.append(name_en)
                            seen_entity_ids.add(entity_id)
                            logger.debug(
                                f"Partial matched '{raw_entity}' → '{name_en}' (entity_id: {entity_id}, via '{alias}')"
                            )
                            found = True
                            break

                if not found:
                    logger.debug(f"No match found for LLM entity: '{raw_entity}'")

        return matched_names


def get_entity_enrichment_service() -> EntityEnrichmentService:
    """Factory function to get entity enrichment service."""
    return EntityEnrichmentService()


if __name__ == "__main__":
    # CLI usage
    import sys

    service = get_entity_enrichment_service()

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        # Show enrichment status
        status = service.get_enrichment_status()
        print("Entity Enrichment Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        # Enrich recent titles
        stats = asyncio.run(service.enrich_titles_batch(since_hours=24, limit=100))
        print("Entity Enrichment Results:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
