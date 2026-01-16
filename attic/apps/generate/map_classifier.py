"""
MAP Classifier - Pass-1a
Parallel title classification into (primary_theater, event_type) pairs
"""

import asyncio
import json
from typing import Dict, List

from loguru import logger

from apps.generate.mapreduce_models import (IncidentCluster,
                                            IncidentClustering,
                                            TitleClassification)
from core.config import SNIConfig
from core.llm_client import (build_classification_prompt,
                             build_incident_clustering_prompt, get_llm_client)


class MapClassifier:
    """
    MAP phase processor: classify titles into theater + event_type

    Handles parallel batch processing with configurable concurrency and timeouts
    """

    def __init__(self, config: SNIConfig):
        self.config = config
        self.llm_client = get_llm_client()

    async def cluster_incidents_batch(
        self, titles: List[Dict[str, str]]
    ) -> IncidentClustering:
        """
        Cluster a batch of titles into strategic incidents via LLM

        Args:
            titles: List of title dicts with 'id', 'title', and 'pubdate_utc' keys

        Returns:
            IncidentClustering object with clustered incidents

        Raises:
            Exception: If LLM call fails or response parsing fails
        """
        if not titles:
            return IncidentClustering(clusters=[])

        logger.debug(f"MAP: Clustering batch of {len(titles)} titles into incidents")

        try:
            # Build incident clustering prompt
            system_prompt, user_prompt = build_incident_clustering_prompt(titles)

            # Call LLM with MAP timeout and dedicated MAP token limit
            response_text = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.map_max_tokens,
                temperature=self.config.llm_temperature,
            )

            # Parse JSON response into incident clusters
            clustering = self._parse_clustering_response(response_text, titles)

            logger.debug(
                f"MAP: Successfully identified {len(clustering.clusters)} incident clusters"
            )
            return clustering

        except Exception as e:
            logger.error(f"MAP: Incident clustering failed: {e}")
            raise

    async def classify_titles_batch(
        self, titles: List[Dict[str, str]]
    ) -> List[TitleClassification]:
        """
        Classify a single batch of titles via LLM (LEGACY METHOD)

        Args:
            titles: List of title dicts with 'id' and 'title' keys

        Returns:
            List of TitleClassification objects

        Raises:
            Exception: If LLM call fails or response parsing fails
        """
        if not titles:
            return []

        logger.debug(f"MAP: Classifying batch of {len(titles)} titles")

        try:
            # Build prompt
            system_prompt, user_prompt = build_classification_prompt(titles)

            # Call LLM with MAP timeout and dedicated MAP token limit
            response_text = await self.llm_client._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=self.config.map_max_tokens,
                temperature=self.config.llm_temperature,
            )

            # Parse JSON Lines response
            classifications = self._parse_classification_response(response_text, titles)

            logger.debug(f"MAP: Successfully classified {len(classifications)} titles")
            return classifications

        except Exception as e:
            logger.error(f"MAP: Batch classification failed: {e}")
            raise

    def _parse_clustering_response(
        self, response_text: str, original_titles: List[Dict[str, str]]
    ) -> IncidentClustering:
        """
        Parse JSON response into IncidentClustering object

        Args:
            response_text: LLM response text (should be JSON array)
            original_titles: Original title data for validation

        Returns:
            IncidentClustering object with incident clusters

        Raises:
            ValueError: If parsing fails or response is invalid
        """
        try:
            # Clean response text - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]  # Remove ```
            cleaned_text = cleaned_text.strip()

            # Parse JSON response
            data = json.loads(cleaned_text)

            if not isinstance(data, list):
                raise ValueError("Response must be a JSON array of incident clusters")

            original_ids = {title["id"] for title in original_titles}
            clusters = []
            all_clustered_ids = set()

            for cluster_data in data:
                try:
                    # Validate required fields
                    if (
                        "incident_name" not in cluster_data
                        or "title_ids" not in cluster_data
                        or "rationale" not in cluster_data
                    ):
                        logger.warning(
                            f"MAP: Skipping malformed cluster: {cluster_data}"
                        )
                        continue

                    # Validate title IDs exist in original titles
                    cluster_title_ids = cluster_data["title_ids"]
                    if not isinstance(cluster_title_ids, list):
                        logger.warning(
                            f"MAP: title_ids must be a list in cluster: {cluster_data['incident_name']}"
                        )
                        continue

                    valid_title_ids = []
                    for title_id in cluster_title_ids:
                        if title_id in original_ids:
                            valid_title_ids.append(title_id)
                            all_clustered_ids.add(title_id)
                        else:
                            logger.warning(
                                f"MAP: Unknown title ID in cluster {cluster_data['incident_name']}: {title_id}"
                            )

                    if not valid_title_ids:
                        logger.warning(
                            f"MAP: No valid title IDs in cluster: {cluster_data['incident_name']}"
                        )
                        continue

                    cluster = IncidentCluster(
                        incident_name=cluster_data["incident_name"],
                        title_ids=valid_title_ids,
                        rationale=cluster_data["rationale"],
                    )
                    clusters.append(cluster)

                except Exception as e:
                    logger.warning(
                        f"MAP: Failed to parse cluster: {cluster_data} - {e}"
                    )
                    continue

            # Check for unclustered titles
            unclustered_ids = original_ids - all_clustered_ids
            if unclustered_ids:
                logger.warning(
                    f"MAP: {len(unclustered_ids)} titles not assigned to any cluster: {unclustered_ids}"
                )

            if len(clusters) == 0:
                raise ValueError("No valid incident clusters found in response")

            logger.debug(
                f"MAP: Parsed {len(clusters)} incident clusters covering {len(all_clustered_ids)} titles"
            )
            return IncidentClustering(clusters=clusters)

        except json.JSONDecodeError as e:
            logger.error(f"MAP: Failed to parse JSON response: {e}")
            logger.error(f"MAP: Response text: {response_text[:500]}...")
            raise ValueError(f"Failed to parse clustering response as JSON: {e}")
        except Exception as e:
            logger.error(f"MAP: Clustering response parsing failed: {e}")
            logger.error(f"MAP: Response text: {response_text[:500]}...")
            raise ValueError(f"Failed to parse clustering response: {e}")

    def _parse_classification_response(
        self, response_text: str, original_titles: List[Dict[str, str]]
    ) -> List[TitleClassification]:
        """
        Parse JSON Lines response into TitleClassification objects

        Args:
            response_text: LLM response text (should be JSON Lines)
            original_titles: Original title data for validation

        Returns:
            List of TitleClassification objects

        Raises:
            ValueError: If parsing fails or response is invalid
        """
        try:
            # Split into lines and parse each JSON object
            lines = response_text.strip().split("\n")
            classifications = []
            original_ids = {title["id"] for title in original_titles}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse individual JSON line
                    data = json.loads(line)

                    # Validate required fields
                    if (
                        "id" not in data
                        or "primary_theater" not in data
                        or "event_type" not in data
                    ):
                        logger.warning(
                            f"MAP: Skipping malformed classification: {line}"
                        )
                        continue

                    # Validate ID exists in original titles
                    if data["id"] not in original_ids:
                        logger.warning(
                            f"MAP: Unknown title ID in response: {data['id']}"
                        )
                        continue

                    classification = TitleClassification(**data)
                    classifications.append(classification)

                except json.JSONDecodeError as e:
                    logger.warning(f"MAP: Failed to parse JSON line: {line} - {e}")
                    continue

            # Validate we got classifications for all titles
            classified_ids = {c.id for c in classifications}
            missing_ids = original_ids - classified_ids

            if missing_ids:
                logger.warning(
                    f"MAP: Missing classifications for {len(missing_ids)} titles: {missing_ids}"
                )

            if len(classifications) == 0:
                raise ValueError("No valid classifications found in response")

            return classifications

        except Exception as e:
            logger.error(f"MAP: Response parsing failed: {e}")
            logger.error(f"MAP: Response text: {response_text[:500]}...")
            raise ValueError(f"Failed to parse classification response: {e}")

    async def process_incidents_parallel(
        self, all_titles: List[Dict[str, str]]
    ) -> List[IncidentCluster]:
        """
        Process all titles with parallel incident clustering

        Args:
            all_titles: All titles to cluster into incidents

        Returns:
            List of all IncidentCluster results

        Raises:
            Exception: If too many batches fail
        """
        if not all_titles:
            return []

        logger.info(
            f"MAP: Starting parallel incident clustering of {len(all_titles)} titles"
        )

        # Split into batches
        batch_size = self.config.map_batch_size
        batches = [
            all_titles[i : i + batch_size]
            for i in range(0, len(all_titles), batch_size)
        ]

        logger.info(f"MAP: Created {len(batches)} batches (batch_size={batch_size})")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.map_concurrency)

        async def process_batch_with_semaphore(
            batch_titles: List[Dict[str, str]], batch_num: int
        ) -> List[IncidentCluster]:
            """Process single batch with concurrency control"""
            async with semaphore:
                logger.debug(
                    f"MAP: Processing incident clustering batch {batch_num + 1}/{len(batches)}"
                )
                try:
                    clustering = await self.cluster_incidents_batch(batch_titles)
                    return clustering.clusters
                except Exception as e:
                    logger.error(
                        f"MAP: Batch {batch_num + 1} incident clustering failed: {e}"
                    )
                    return []  # Return empty list for failed batches

        # Process all batches in parallel
        batch_results = await asyncio.gather(
            *[
                process_batch_with_semaphore(batch, i)
                for i, batch in enumerate(batches)
            ],
            return_exceptions=True,
        )

        # Collect successful results
        all_clusters = []
        successful_batches = 0

        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"MAP: Batch {i + 1} exception: {result}")
            elif isinstance(result, list):
                all_clusters.extend(result)
                if result:  # Non-empty result
                    successful_batches += 1
            else:
                logger.error(
                    f"MAP: Batch {i + 1} unexpected result type: {type(result)}"
                )

        # Validate success rate
        success_rate = successful_batches / len(batches) if batches else 0
        logger.info(
            f"MAP: Completed {successful_batches}/{len(batches)} batches successfully ({success_rate:.1%})"
        )

        if success_rate < self.config.map_success_rate_threshold:
            raise Exception(
                f"MAP incident clustering failed: only {success_rate:.1%} of batches succeeded"
            )

        logger.info(f"MAP: Total incident clusters: {len(all_clusters)}")
        return all_clusters

    async def process_titles_parallel(
        self, all_titles: List[Dict[str, str]]
    ) -> List[TitleClassification]:
        """
        Process all titles with parallel MAP calls (LEGACY METHOD)

        Args:
            all_titles: All titles to classify

        Returns:
            List of all TitleClassification results

        Raises:
            Exception: If too many batches fail
        """
        if not all_titles:
            return []

        logger.info(
            f"MAP: Starting parallel classification of {len(all_titles)} titles"
        )

        # Split into batches
        batch_size = self.config.map_batch_size
        batches = [
            all_titles[i : i + batch_size]
            for i in range(0, len(all_titles), batch_size)
        ]

        logger.info(f"MAP: Created {len(batches)} batches (batch_size={batch_size})")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.map_concurrency)

        async def process_batch_with_semaphore(
            batch_titles: List[Dict[str, str]], batch_num: int
        ) -> List[TitleClassification]:
            """Process single batch with concurrency control"""
            async with semaphore:
                logger.debug(f"MAP: Processing batch {batch_num + 1}/{len(batches)}")
                try:
                    return await self.classify_titles_batch(batch_titles)
                except Exception as e:
                    logger.error(f"MAP: Batch {batch_num + 1} failed: {e}")
                    return []  # Return empty list for failed batches

        # Process all batches in parallel
        batch_results = await asyncio.gather(
            *[
                process_batch_with_semaphore(batch, i)
                for i, batch in enumerate(batches)
            ],
            return_exceptions=True,
        )

        # Collect successful results
        all_classifications = []
        successful_batches = 0

        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"MAP: Batch {i + 1} exception: {result}")
            elif isinstance(result, list):
                all_classifications.extend(result)
                if result:  # Non-empty result
                    successful_batches += 1
            else:
                logger.error(
                    f"MAP: Batch {i + 1} unexpected result type: {type(result)}"
                )

        # Validate success rate
        success_rate = successful_batches / len(batches) if batches else 0
        logger.info(
            f"MAP: Completed {successful_batches}/{len(batches)} batches successfully ({success_rate:.1%})"
        )

        if success_rate < self.config.map_success_rate_threshold:
            raise Exception(
                f"MAP phase failed: only {success_rate:.1%} of batches succeeded"
            )

        logger.info(f"MAP: Total classifications: {len(all_classifications)}")
        return all_classifications
