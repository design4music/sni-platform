"""
REDUCE Assembler - Pass-1c
Parallel EF title/summary generation for classified title groups
"""

import asyncio
from typing import Dict, List

from loguru import logger

from apps.generate.llm_client import get_gen1_llm_client
from apps.generate.mapreduce_models import IncidentAnalysis, IncidentCluster
from apps.generate.mapreduce_prompts import build_incident_analysis_prompt
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

    async def analyze_incident_cluster(
        self, incident_cluster: IncidentCluster, all_titles: List[Dict[str, str]]
    ) -> IncidentAnalysis:
        """
        Analyze an incident cluster to create comprehensive Event Family

        Args:
            incident_cluster: Incident cluster with title IDs and metadata
            all_titles: All title data for lookup

        Returns:
            IncidentAnalysis with complete EF analysis and events timeline

        Raises:
            Exception: If LLM call fails or response parsing fails
        """
        logger.debug(
            f"REDUCE: Analyzing incident cluster '{incident_cluster.incident_name}' ({len(incident_cluster.title_ids)} titles)"
        )

        try:
            # Get titles for this incident cluster
            title_lookup = {title["id"]: title for title in all_titles}
            cluster_titles = []

            for title_id in incident_cluster.title_ids:
                if title_id in title_lookup:
                    cluster_titles.append(title_lookup[title_id])
                else:
                    logger.warning(
                        f"REDUCE: Title ID {title_id} not found in title data"
                    )

            if not cluster_titles:
                raise ValueError(
                    f"No valid titles found for incident cluster '{incident_cluster.incident_name}'"
                )

            # Build incident analysis prompt
            system_prompt, user_prompt = build_incident_analysis_prompt(
                incident_cluster.incident_name,
                incident_cluster.rationale,
                cluster_titles,
            )

            # Call LLM for incident analysis
            response_text = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.llm_max_tokens_generic,
                temperature=self.config.llm_temperature,
            )

            # Parse JSON response
            incident_analysis = self._parse_incident_analysis_response(response_text)

            logger.debug(
                f"REDUCE: Analyzed incident '{incident_cluster.incident_name}' -> {incident_analysis.primary_theater}/{incident_analysis.event_type} with {len(incident_analysis.events)} events"
            )
            return incident_analysis

        except Exception as e:
            logger.error(
                f"REDUCE: Incident analysis failed for '{incident_cluster.incident_name}': {e}"
            )
            raise

    def _parse_incident_analysis_response(self, response_text: str) -> IncidentAnalysis:
        """
        Parse JSON response from incident analysis into IncidentAnalysis object

        Args:
            response_text: LLM response text (should be JSON with IncidentAnalysis structure)

        Returns:
            IncidentAnalysis object with complete incident analysis

        Raises:
            ValueError: If parsing fails or response is invalid
        """
        try:
            # Try to extract JSON from response
            response_data = self.llm_client._extract_json(response_text)

            # Validate required fields
            required_fields = [
                "primary_theater",
                "event_type",
                "ef_title",
                "ef_summary",
                "events",
            ]
            for field in required_fields:
                if field not in response_data:
                    raise ValueError(
                        f"Missing required field '{field}' in response: {response_data}"
                    )

            # Validate ef_title and ef_summary
            ef_title = response_data["ef_title"].strip()
            ef_summary = response_data["ef_summary"].strip()

            if len(ef_title) > self.config.ef_title_max_length:
                logger.warning(
                    f"REDUCE: EF title too long ({len(ef_title)} chars), truncating"
                )
                ef_title = ef_title[: self.config.ef_title_max_length - 3] + "..."

            if len(ef_summary) > self.config.ef_summary_max_length:
                logger.warning(
                    f"REDUCE: EF summary too long ({len(ef_summary)} chars), truncating"
                )
                ef_summary = ef_summary[: self.config.ef_summary_max_length - 3] + "..."

            # Validate events
            events = response_data["events"]
            if not isinstance(events, list):
                raise ValueError(f"Events must be a list, got: {type(events)}")

            # Validate each event structure
            for i, event in enumerate(events):
                required_event_fields = [
                    "summary",
                    "date",
                    "source_title_ids",
                    "event_id",
                ]
                for field in required_event_fields:
                    if field not in event:
                        raise ValueError(
                            f"Event {i} missing required field '{field}': {event}"
                        )

            # Validate theater and event_type are from allowed lists
            # Note: We could add validation against THEATERS and EVENT_TYPES here if needed

            return IncidentAnalysis(
                primary_theater=response_data["primary_theater"],
                event_type=response_data["event_type"],
                ef_title=ef_title,
                ef_summary=ef_summary,
                events=events,
            )

        except Exception as e:
            logger.error(f"REDUCE: Incident analysis response parsing failed: {e}")
            logger.error(f"REDUCE: Response text: {response_text[:500]}...")
            raise ValueError(f"Failed to parse incident analysis response: {e}")

    async def process_incidents_parallel(
        self, incident_clusters: List[IncidentCluster], all_titles: List[Dict[str, str]]
    ) -> List[EventFamily]:
        """
        Process all incident clusters with parallel REDUCE calls

        Args:
            incident_clusters: All incident clusters to analyze
            all_titles: All title data for lookup

        Returns:
            List of EventFamily objects with generated content

        Raises:
            Exception: If too many clusters fail
        """
        if not incident_clusters:
            return []

        logger.info(
            f"REDUCE: Starting parallel incident analysis for {len(incident_clusters)} clusters"
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.reduce_concurrency)

        async def process_incident_with_semaphore(
            incident_cluster: IncidentCluster, cluster_num: int
        ) -> EventFamily:
            """Process single incident cluster with concurrency control"""
            async with semaphore:
                logger.debug(
                    f"REDUCE: Processing incident {cluster_num + 1}/{len(incident_clusters)}: {incident_cluster.incident_name}"
                )
                try:
                    # Analyze incident cluster
                    incident_analysis = await self.analyze_incident_cluster(
                        incident_cluster, all_titles
                    )

                    # Create EventFamily object from incident analysis
                    event_family = self._build_event_family_from_incident(
                        incident_cluster, incident_analysis, all_titles
                    )
                    return event_family

                except Exception as e:
                    logger.error(f"REDUCE: Incident {cluster_num + 1} failed: {e}")
                    # Create fallback EventFamily with generic content
                    return self._build_fallback_event_family_from_incident(
                        incident_cluster, all_titles
                    )

        # Process all incidents in parallel
        event_families = await asyncio.gather(
            *[
                process_incident_with_semaphore(cluster, i)
                for i, cluster in enumerate(incident_clusters)
            ],
            return_exceptions=True,
        )

        # Collect results (filter out exceptions)
        valid_event_families = []
        successful_clusters = 0

        for i, result in enumerate(event_families):
            if isinstance(result, Exception):
                logger.error(f"REDUCE: Incident {i + 1} exception: {result}")
                # Create fallback EF for exceptions
                fallback_ef = self._build_fallback_event_family_from_incident(
                    incident_clusters[i], all_titles
                )
                valid_event_families.append(fallback_ef)
            elif isinstance(result, EventFamily):
                valid_event_families.append(result)
                successful_clusters += 1
            else:
                logger.error(
                    f"REDUCE: Incident {i + 1} unexpected result type: {type(result)}"
                )

        # Log success rate
        success_rate = (
            successful_clusters / len(incident_clusters) if incident_clusters else 0
        )
        logger.info(
            f"REDUCE: Completed {successful_clusters}/{len(incident_clusters)} incidents successfully ({success_rate:.1%})"
        )

        logger.info(f"REDUCE: Total Event Families: {len(valid_event_families)}")
        return valid_event_families

    def _build_event_family_from_incident(
        self,
        incident_cluster: IncidentCluster,
        incident_analysis: IncidentAnalysis,
        all_titles: List[Dict[str, str]],
    ) -> EventFamily:
        """
        Build EventFamily object from incident cluster and analysis

        Args:
            incident_cluster: Original incident cluster
            incident_analysis: LLM analysis of the incident
            all_titles: All title data for extracting metadata

        Returns:
            EventFamily object ready for database insertion
        """
        from apps.generate.ef_key import generate_ef_key

        # Get title metadata for this incident
        title_lookup = {title["id"]: title for title in all_titles}
        cluster_titles = [
            title_lookup[title_id]
            for title_id in incident_cluster.title_ids
            if title_id in title_lookup
        ]

        # Extract key actors from all titles in the incident
        all_actors = set()
        dates = []

        for title in cluster_titles:
            # Extract actors
            title_entities = title.get("extracted_actors") or {}
            if isinstance(title_entities, dict):
                actors_list = title_entities.get("actors", [])
                if isinstance(actors_list, list):
                    all_actors.update(actors_list)

            # Extract dates
            pubdate = title.get("pubdate_utc")
            if pubdate:
                if isinstance(pubdate, str):
                    try:
                        from datetime import datetime

                        dates.append(
                            datetime.fromisoformat(pubdate.replace("Z", "+00:00"))
                        )
                    except ValueError:
                        pass
                elif hasattr(pubdate, "year"):  # datetime object
                    dates.append(pubdate)

        key_actors = sorted(list(all_actors))

        # Calculate temporal scope
        if dates:
            min(dates)
            max(dates)
        else:
            from datetime import datetime

            datetime.utcnow()

        # Generate ef_key using LLM-determined theater and event_type
        ef_key = generate_ef_key(
            actors=[],  # Actors ignored in current system
            primary_theater=incident_analysis.primary_theater,
            event_type=incident_analysis.event_type,
        )

        return EventFamily(
            title=incident_analysis.ef_title,
            summary=incident_analysis.ef_title,  # Use title as summary until P4 enrichment
            key_actors=key_actors,
            event_type=incident_analysis.event_type,
            primary_theater=incident_analysis.primary_theater,
            ef_key=ef_key,
            status="seed",  # Phase 1: Start as seed, promote to active later
            source_title_ids=incident_cluster.title_ids,
            confidence_score=0.90,  # Higher confidence for incident-based approach
            coherence_reason=f"{len(incident_cluster.title_ids)} titles - '{incident_cluster.incident_name}'",
            processing_notes=incident_cluster.rationale,
            events=incident_analysis.events,  # Include extracted events timeline
        )

    def _build_fallback_event_family_from_incident(
        self, incident_cluster: IncidentCluster, all_titles: List[Dict[str, str]]
    ) -> EventFamily:
        """
        Build fallback EventFamily for failed incident analysis

        Args:
            incident_cluster: Original incident cluster
            all_titles: All title data for extracting metadata

        Returns:
            EventFamily object with generic content
        """
        from datetime import datetime

        from apps.generate.ef_key import generate_ef_key

        # Get title metadata for this incident
        title_lookup = {title["id"]: title for title in all_titles}
        cluster_titles = [
            title_lookup[title_id]
            for title_id in incident_cluster.title_ids
            if title_id in title_lookup
        ]

        # Extract basic metadata
        all_actors = set()
        dates = []

        for title in cluster_titles:
            # Extract actors
            title_entities = title.get("extracted_actors") or {}
            if isinstance(title_entities, dict):
                actors_list = title_entities.get("actors", [])
                if isinstance(actors_list, list):
                    all_actors.update(actors_list)

            # Extract dates
            pubdate = title.get("pubdate_utc")
            if pubdate:
                if isinstance(pubdate, str):
                    try:
                        dates.append(
                            datetime.fromisoformat(pubdate.replace("Z", "+00:00"))
                        )
                    except ValueError:
                        pass
                elif hasattr(pubdate, "year"):  # datetime object
                    dates.append(pubdate)

        key_actors = sorted(list(all_actors))

        # Calculate temporal scope
        if dates:
            min(dates)
            max(dates)
        else:
            datetime.utcnow()

        # Use generic fallback classification
        primary_theater = "GLOBAL_SUMMIT"  # Fallback theater
        event_type = "Strategy/Tactics"  # Fallback event type

        # Generate ef_key using fallback classification
        ef_key = generate_ef_key(
            actors=[],
            primary_theater=primary_theater,
            event_type=event_type,
        )

        # Create generic title and summary
        title = (
            incident_cluster.incident_name[:117] + "..."
            if len(incident_cluster.incident_name) > 120
            else incident_cluster.incident_name
        )
        summary = (
            f"Incident analysis failed: {incident_cluster.rationale[:200]}..."
            if len(incident_cluster.rationale) > 200
            else incident_cluster.rationale
        )

        return EventFamily(
            title=title,
            summary=summary,
            key_actors=key_actors,
            event_type=event_type,
            primary_theater=primary_theater,
            ef_key=ef_key,
            status="seed",
            source_title_ids=incident_cluster.title_ids,
            confidence_score=0.3,  # Low confidence for fallback
            coherence_reason=f"Fallback EF for failed incident analysis: {incident_cluster.incident_name}",
            processing_notes=f"Fallback generated via MAP/REDUCE incident clustering pipeline: {incident_cluster.rationale}",
        )
