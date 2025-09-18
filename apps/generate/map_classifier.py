"""
MAP Classifier - Pass-1a
Parallel title classification into (primary_theater, event_type) pairs
"""

import asyncio
import json
from typing import Dict, List

from loguru import logger

from apps.generate.llm_client import get_gen1_llm_client
from apps.generate.mapreduce_models import TitleClassification
from apps.generate.mapreduce_prompts import build_classification_prompt
from core.config import SNIConfig


class MapClassifier:
    """
    MAP phase processor: classify titles into theater + event_type

    Handles parallel batch processing with configurable concurrency and timeouts
    """

    def __init__(self, config: SNIConfig):
        self.config = config
        self.llm_client = get_gen1_llm_client()

    async def classify_titles_batch(
        self, titles: List[Dict[str, str]]
    ) -> List[TitleClassification]:
        """
        Classify a single batch of titles via LLM

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

    async def process_titles_parallel(
        self, all_titles: List[Dict[str, str]]
    ) -> List[TitleClassification]:
        """
        Process all titles with parallel MAP calls

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

        if success_rate < 0.5:  # Less than 50% success
            raise Exception(
                f"MAP phase failed: only {success_rate:.1%} of batches succeeded"
            )

        logger.info(f"MAP: Total classifications: {len(all_classifications)}")
        return all_classifications
