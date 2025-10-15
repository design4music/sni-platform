"""
Enhanced P2 Strategic Filtering with Neo4j
Orchestrates mechanical gate, Neo4j enhancement, and LLM fallback
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.filter.strategic_gate import StrategicGate  # noqa: E402
from core.neo4j_enhancements import Neo4jEnhancements  # noqa: E402
from core.neo4j_sync import get_neo4j_sync  # noqa: E402


async def enhanced_p2_filter(title_data):
    """
    Enhanced P2 strategic filtering with three-stage logic:
    1. Mechanical filters (fast, deterministic)
    2. Neo4j enhancement (graph relationships for borderline cases)
    3. LLM fallback (expensive, for truly ambiguous cases)

    Args:
        title_data: Dict with:
            - id: title UUID
            - title_display: display text
            - title_norm: normalized text
            - pubdate_utc: publication datetime
            - entities: list of entity dicts with 'text' and 'type'

    Returns:
        Dict with gate_keep (bool) and gate_reason (str)
    """
    gate = StrategicGate()
    title_text = title_data.get("title_norm") or title_data.get("title_display", "")

    # Stage 1: Mechanical filters
    mechanical_result = gate.filter_title(title_text)

    # Strong mechanical signal - trust it
    if mechanical_result.keep:
        logger.debug(f"Mechanical KEEP: {mechanical_result.reason}")
        return {"gate_keep": True, "gate_reason": mechanical_result.reason}

    if mechanical_result.reason == "blocked_by_stop":
        logger.debug("Mechanical REJECT: blocked by stop list")
        return {"gate_keep": False, "gate_reason": "blocked_by_stop"}

    # Stage 2: Borderline case - try Neo4j enhancement
    # Only if we have entities to work with
    entities = title_data.get("entities", [])
    if entities and len(entities) >= 2:
        logger.debug(f"Borderline case with {len(entities)} entities - checking Neo4j")

        neo4j_sync = get_neo4j_sync()
        neo4j_enhancements = Neo4jEnhancements(neo4j_sync)

        try:
            neo4j_result = await neo4j_enhancements.enhance_p2_decision(title_data)
            if neo4j_result:
                logger.info(
                    f"Neo4j BOOST: {neo4j_result['gate_reason']} for title: {title_text[:60]}..."
                )
                return neo4j_result
        except Exception as e:
            logger.warning(f"Neo4j enhancement failed: {e}")

    # Stage 3: Fall back to treating as non-strategic
    # (In future, could add LLM classification here for very ambiguous cases)
    logger.debug("No mechanical or Neo4j signal - defaulting to non-strategic")
    return {"gate_keep": False, "gate_reason": "no_strategic_signal"}


def enhanced_p2_filter_sync(title_data):
    """Synchronous wrapper for enhanced P2 filter"""
    return asyncio.run(enhanced_p2_filter(title_data))
