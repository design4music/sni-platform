#!/usr/bin/env python3
"""
Test Neo4j Intelligence Signals

Tests the three Neo4j intelligence signals on actual title data:
1. Entity Centrality - hot entities mentioned in strategic titles
2. Strategic Neighborhood - connection density to strategic clusters
3. Ongoing Event Detection - temporal story patterns

Usage:
    python test_neo4j_intelligence.py
    python test_neo4j_intelligence.py --title-id <uuid>
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402
from core.neo4j_sync import get_neo4j_sync  # noqa: E402


async def test_intelligence_signals(title_id: str = None):
    """Test Neo4j intelligence signals on title(s)"""

    neo4j = get_neo4j_sync()

    # Get test title IDs
    with get_db_session() as session:
        if title_id:
            # Test specific title
            query = """
            SELECT id, title_display, gate_keep, entities
            FROM titles
            WHERE id = :title_id
            """
            results = session.execute(text(query), {"title_id": title_id}).fetchall()
        else:
            # Test strategic titles with entities
            query = """
            SELECT id, title_display, gate_keep, entities
            FROM titles
            WHERE entities IS NOT NULL
              AND gate_keep = true
            ORDER BY created_at DESC
            LIMIT 5
            """
            results = session.execute(text(query)).fetchall()

    if not results:
        logger.error("No titles found to test")
        return

    logger.info(f"Testing Neo4j intelligence signals on {len(results)} titles\n")

    for row in results:
        title_id = str(row.id)
        title_text = row.title_display
        gate_keep = row.gate_keep
        entities = row.entities or []

        logger.info(f"Title: {title_text}")
        logger.info(f"  ID: {title_id}")
        logger.info(f"  Gate Keep: {gate_keep}")
        logger.info(f"  Entities: {entities}")

        # Test all three signals
        logger.info("  Testing Neo4j signals...")

        try:
            # Get combined signals (no time limit for testing on historical data)
            signals = await neo4j.analyze_strategic_signals(
                title_id,
                days_lookback_centrality=None,
                days_lookback_neighborhood=None,
                days_lookback_event=None,
            )

            # Calculate score
            strategic_score = 0
            reasons = []

            # Signal 1: Entity Centrality
            if signals.get("high_centrality_entities", 0) >= 1:
                strategic_score += 2
                centrality_details = signals.get("centrality_details", [])
                entity_names = [e["entity"] for e in centrality_details[:2]]
                reasons.append(f"Hot entities: {', '.join(entity_names)}")

            # Signal 2: Strategic Neighborhood
            if signals.get("strategic_neighbor_strength", 0) >= 0.3:
                strategic_score += 1
                neighbor_count = signals.get("strategic_neighbors", 0)
                reasons.append(f"{neighbor_count} strategic neighbors")

            # Signal 3: Ongoing Event
            if signals.get("ongoing_event", False):
                strategic_score += 1
                reasons.append("Ongoing event")

            # Show results
            logger.info(
                f"  Centrality: {signals['high_centrality_entities']} hot entities"
            )
            if signals.get("centrality_details"):
                for entity in signals["centrality_details"][:3]:
                    logger.info(
                        f"    - {entity['entity']} ({entity['type']}): "
                        f"{entity['strategic_mentions']} strategic mentions"
                    )

            logger.info(
                f"  Neighborhood: {signals['strategic_neighbors']} neighbors, "
                f"strength {signals['strategic_neighbor_strength']:.2f}"
            )
            logger.info(f"  Ongoing Event: {signals['ongoing_event']}")

            logger.info(f"\n  STRATEGIC SCORE: {strategic_score}/4")
            if reasons:
                logger.info(f"  Reasons: {'; '.join(reasons)}")

            if strategic_score >= 2:
                logger.success("  DECISION: Would OVERRIDE to strategic (score >= 2)\n")
            else:
                logger.info("  DECISION: No override (score < 2)\n")

        except Exception as e:
            logger.error(f"  Error testing signals: {e}\n")

    await neo4j.close()


async def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Neo4j Intelligence Signals")
    parser.add_argument("--title-id", type=str, help="Test specific title ID")

    args = parser.parse_args()

    await test_intelligence_signals(title_id=args.title_id)


if __name__ == "__main__":
    asyncio.run(main())
