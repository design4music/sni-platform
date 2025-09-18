"""
REDUCE Assembler - Pass-1c
Parallel EF title/summary generation for classified title groups
"""

import asyncio
from typing import Dict, List

from loguru import logger

from apps.generate.llm_client import get_gen1_llm_client
from apps.generate.mapreduce_models import EFGroup, ReduceResponse
from apps.generate.mapreduce_prompts import build_ef_generation_prompt
from apps.generate.models import EventFamily
from core.config import SNIConfig


class ReduceAssembler:
    """
    REDUCE phase processor: generate EF title/summary for title groups

    Handles parallel EF generation with configurable concurrency and timeouts
    """

    def __init__(self, config: SNIConfig):
        self.config = config
        self.llm_client = get_gen1_llm_client()

    async def generate_ef_content(self, ef_group: EFGroup) -> ReduceResponse:
        """
        Generate EF title and summary for a single EF group

        Args:
            ef_group: Grouped titles by (theater, event_type)

        Returns:
            ReduceResponse with generated EF title and summary

        Raises:
            Exception: If LLM call fails or response parsing fails
        """
        logger.debug(
            f"REDUCE: Generating EF for {ef_group.primary_theater}/{ef_group.event_type} ({len(ef_group.titles)} titles)"
        )

        try:
            # Sample titles if group is too large
            sample_titles = self._sample_titles_for_ef_generation(ef_group.titles)

            # Build prompt
            system_prompt, user_prompt = build_ef_generation_prompt(
                ef_group.primary_theater, ef_group.event_type, sample_titles
            )

            # Call LLM with REDUCE timeout
            response_text = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.llm_max_tokens_generic,
                temperature=self.config.llm_temperature,
            )

            # Parse JSON response
            ef_content = self._parse_ef_generation_response(response_text)

            logger.debug(
                f"REDUCE: Generated EF '{ef_content.ef_title}' for {ef_group.primary_theater}/{ef_group.event_type}"
            )
            return ef_content

        except Exception as e:
            logger.error(
                f"REDUCE: EF generation failed for {ef_group.primary_theater}/{ef_group.event_type}: {e}"
            )
            raise

    def _sample_titles_for_ef_generation(
        self, titles: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Sample up to N titles for EF generation (to stay within prompt limits)

        Args:
            titles: All titles in the group

        Returns:
            Sampled titles (up to reduce_max_titles)
        """
        max_titles = self.config.reduce_max_titles

        if len(titles) <= max_titles:
            return titles

        # Sample evenly across the time range
        # For now, just take first N titles (could be improved with temporal sampling)
        sampled = titles[:max_titles]
        logger.debug(
            f"REDUCE: Sampled {len(sampled)}/{len(titles)} titles for EF generation"
        )
        return sampled

    def _parse_ef_generation_response(self, response_text: str) -> ReduceResponse:
        """
        Parse JSON response into ReduceResponse object

        Args:
            response_text: LLM response text (should be JSON)

        Returns:
            ReduceResponse object

        Raises:
            ValueError: If parsing fails or response is invalid
        """
        try:
            # Try to extract JSON from response
            response_data = self.llm_client._extract_json(response_text)

            # Validate required fields
            if "ef_title" not in response_data or "ef_summary" not in response_data:
                raise ValueError(
                    f"Missing required fields in response: {response_data}"
                )

            # Validate field lengths
            ef_title = response_data["ef_title"].strip()
            ef_summary = response_data["ef_summary"].strip()

            if len(ef_title) > 120:
                logger.warning(
                    f"REDUCE: EF title too long ({len(ef_title)} chars), truncating"
                )
                ef_title = ef_title[:117] + "..."

            if len(ef_summary) > 280:
                logger.warning(
                    f"REDUCE: EF summary too long ({len(ef_summary)} chars), truncating"
                )
                ef_summary = ef_summary[:277] + "..."

            return ReduceResponse(ef_title=ef_title, ef_summary=ef_summary)

        except Exception as e:
            logger.error(f"REDUCE: Response parsing failed: {e}")
            logger.error(f"REDUCE: Response text: {response_text[:500]}...")
            raise ValueError(f"Failed to parse EF generation response: {e}")

    async def process_groups_parallel(
        self, ef_groups: List[EFGroup]
    ) -> List[EventFamily]:
        """
        Process all EF groups with parallel REDUCE calls

        Args:
            ef_groups: All EF groups to process

        Returns:
            List of EventFamily objects with generated content

        Raises:
            Exception: If too many groups fail
        """
        if not ef_groups:
            return []

        logger.info(
            f"REDUCE: Starting parallel EF generation for {len(ef_groups)} groups"
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.reduce_concurrency)

        async def process_group_with_semaphore(
            ef_group: EFGroup, group_num: int
        ) -> EventFamily:
            """Process single EF group with concurrency control"""
            async with semaphore:
                logger.debug(
                    f"REDUCE: Processing group {group_num + 1}/{len(ef_groups)}"
                )
                try:
                    # Generate EF content
                    ef_content = await self.generate_ef_content(ef_group)

                    # Create EventFamily object
                    event_family = self._build_event_family(ef_group, ef_content)
                    return event_family

                except Exception as e:
                    logger.error(f"REDUCE: Group {group_num + 1} failed: {e}")
                    # Create fallback EventFamily with generic content
                    return self._build_fallback_event_family(ef_group)

        # Process all groups in parallel
        event_families = await asyncio.gather(
            *[
                process_group_with_semaphore(group, i)
                for i, group in enumerate(ef_groups)
            ],
            return_exceptions=True,
        )

        # Collect results (filter out exceptions)
        valid_event_families = []
        successful_groups = 0

        for i, result in enumerate(event_families):
            if isinstance(result, Exception):
                logger.error(f"REDUCE: Group {i + 1} exception: {result}")
                # Create fallback EF for exceptions
                fallback_ef = self._build_fallback_event_family(ef_groups[i])
                valid_event_families.append(fallback_ef)
            elif isinstance(result, EventFamily):
                valid_event_families.append(result)
                successful_groups += 1
            else:
                logger.error(
                    f"REDUCE: Group {i + 1} unexpected result type: {type(result)}"
                )

        # Log success rate
        success_rate = successful_groups / len(ef_groups) if ef_groups else 0
        logger.info(
            f"REDUCE: Completed {successful_groups}/{len(ef_groups)} groups successfully ({success_rate:.1%})"
        )

        logger.info(f"REDUCE: Total Event Families: {len(valid_event_families)}")
        return valid_event_families

    def _build_event_family(
        self, ef_group: EFGroup, ef_content: ReduceResponse
    ) -> EventFamily:
        """
        Build EventFamily object from EF group and generated content

        Args:
            ef_group: Original EF group data
            ef_content: Generated EF title/summary

        Returns:
            EventFamily object ready for database insertion
        """
        from apps.generate.ef_key import generate_ef_key

        # Generate ef_key using existing logic
        ef_key = generate_ef_key(
            actors=[],  # Actors ignored in current system
            primary_theater=ef_group.primary_theater,
            event_type=ef_group.event_type,
        )

        return EventFamily(
            title=ef_content.ef_title,
            summary=ef_content.ef_summary,
            key_actors=ef_group.key_actors,  # Use extracted key actors from all source titles
            event_type=ef_group.event_type,
            primary_theater=ef_group.primary_theater,
            ef_key=ef_key,
            status="active",
            event_start=ef_group.temporal_scope_start,
            event_end=ef_group.temporal_scope_end,
            source_title_ids=ef_group.title_ids,
            confidence_score=0.85,  # Default confidence for MAP/REDUCE approach
            coherence_reason=f"MAP/REDUCE generated EF for {len(ef_group.title_ids)} titles in {ef_group.primary_theater}/{ef_group.event_type}",
            processing_notes="Generated via MAP/REDUCE pipeline",
        )

    def _build_fallback_event_family(self, ef_group: EFGroup) -> EventFamily:
        """
        Build fallback EventFamily for failed EF generation

        Args:
            ef_group: Original EF group data

        Returns:
            EventFamily object with generic content
        """
        from apps.generate.ef_key import generate_ef_key

        # Generate ef_key using existing logic
        ef_key = generate_ef_key(
            actors=[],
            primary_theater=ef_group.primary_theater,
            event_type=ef_group.event_type,
        )

        # Create generic title and summary
        title = f"{ef_group.primary_theater} {ef_group.event_type} Events"
        summary = f"Collection of {len(ef_group.title_ids)} {ef_group.event_type.lower()} events in {ef_group.primary_theater} theater"

        return EventFamily(
            title=title,
            summary=summary,
            key_actors=ef_group.key_actors,  # Use extracted key actors even for fallback
            event_type=ef_group.event_type,
            primary_theater=ef_group.primary_theater,
            ef_key=ef_key,
            status="active",
            event_start=ef_group.temporal_scope_start,
            event_end=ef_group.temporal_scope_end,
            source_title_ids=ef_group.title_ids,
            confidence_score=0.5,  # Lower confidence for fallback
            coherence_reason=f"Fallback EF for failed generation: {ef_group.primary_theater}/{ef_group.event_type}",
            processing_notes="Generated via MAP/REDUCE pipeline (fallback)",
        )
