#!/usr/bin/env python3
"""
Test enhanced P2 filtering with Neo4j
Demonstrates three-stage filtering: mechanical -> Neo4j -> fallback
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger  # noqa: E402

from apps.filter.enhanced_p2_filter import enhanced_p2_filter  # noqa: E402


async def test_enhanced_p2():
    """Test enhanced P2 filtering with various title types"""

    logger.info("=" * 60)
    logger.info("ENHANCED P2 FILTERING TEST")
    logger.info("=" * 60)

    test_cases = [
        {
            "name": "Clear strategic (mechanical pass)",
            "title_data": {
                "id": str(uuid.uuid4()),
                "title_display": "Biden announces new sanctions against Russia",
                "title_norm": "biden announces new sanctions against russia",
                "pubdate_utc": datetime.now(),
                "entities": [
                    {"text": "Biden", "type": "PERSON"},
                    {"text": "Russia", "type": "GPE"},
                ],
            },
        },
        {
            "name": "Borderline with entities (Neo4j may help)",
            "title_data": {
                "id": str(uuid.uuid4()),
                "title_display": "Trade negotiations continue in Asian markets",
                "title_norm": "trade negotiations continue in asian markets",
                "pubdate_utc": datetime.now(),
                "entities": [
                    {"text": "trade", "type": "EVENT"},
                    {"text": "Asian markets", "type": "ORG"},
                    {"text": "negotiations", "type": "EVENT"},
                ],
            },
        },
        {
            "name": "Clear non-strategic (celebrity news)",
            "title_data": {
                "id": str(uuid.uuid4()),
                "title_display": "Celebrity wedding breaks internet records",
                "title_norm": "celebrity wedding breaks internet records",
                "pubdate_utc": datetime.now(),
                "entities": [
                    {"text": "wedding", "type": "EVENT"},
                    {"text": "internet", "type": "PRODUCT"},
                ],
            },
        },
        {
            "name": "No entities (fallback to non-strategic)",
            "title_data": {
                "id": str(uuid.uuid4()),
                "title_display": "Local weather forecast for weekend",
                "title_norm": "local weather forecast for weekend",
                "pubdate_utc": datetime.now(),
                "entities": [],
            },
        },
    ]

    logger.info("\nTesting enhanced P2 filter on sample titles:\n")

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n[Test {i}] {test_case['name']}")
        logger.info(f"Title: {test_case['title_data']['title_display']}")
        logger.info(f"Entities: {len(test_case['title_data']['entities'])}")

        result = await enhanced_p2_filter(test_case["title_data"])

        status = "KEEP" if result["gate_keep"] else "REJECT"
        logger.info(f"Decision: [{status}] - {result['gate_reason']}")

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_enhanced_p2())
