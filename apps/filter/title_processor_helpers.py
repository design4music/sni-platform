"""
Shared helpers for title processing

Consolidates common database update and stats tracking logic
used by both entity_enrichment.py and run_enhanced_gate.py
"""

import json
from typing import Any, Dict

from sqlalchemy import text


def update_title_entities(
    session, title_id: str, entities: Dict[str, Any], is_strategic: bool
) -> None:
    """
    Update title with extracted entities and strategic gate decision

    Args:
        session: SQLAlchemy session
        title_id: Title UUID
        entities: Extracted entities dict
        is_strategic: Strategic gate decision

    This is the single source of truth for title entity updates
    """
    session.execute(
        text(
            """
            UPDATE titles
            SET gate_keep = :gate_keep,
                entities = :entities,
                processing_status = 'gated'
            WHERE id = :title_id
            """
        ),
        {
            "gate_keep": is_strategic,
            "entities": json.dumps(entities),
            "title_id": title_id,
        },
    )


def update_processing_stats(
    stats: Dict[str, int], entities: Dict[str, Any], is_strategic: bool
) -> None:
    """
    Update processing statistics based on entity extraction result

    Args:
        stats: Stats dict to update (modified in-place)
        entities: Extracted entities dict
        is_strategic: Strategic gate decision

    Common stats keys:
    - processed / titles_processed
    - strategic / strategic_titles
    - non_strategic / non_strategic_titles
    - entities_extracted
    - blocked_by_stop
    """
    # Increment processed count (handle both naming conventions)
    if "processed" in stats:
        stats["processed"] += 1
    if "titles_processed" in stats:
        stats["titles_processed"] += 1

    # Strategic classification
    if is_strategic:
        if "strategic" in stats:
            stats["strategic"] += 1
        if "strategic_titles" in stats:
            stats["strategic_titles"] += 1
    else:
        if "non_strategic" in stats:
            stats["non_strategic"] += 1
        if "non_strategic_titles" in stats:
            stats["non_strategic_titles"] += 1

    # Entity extraction tracking
    has_entities = entities.get("actors") or entities.get(
        "people", []
    )  # Handle both formats
    if has_entities:
        if "entities_extracted" in stats:
            stats["entities_extracted"] += 1

    # Blocked by stop culture (has entities but not strategic)
    if not is_strategic and has_entities:
        if "blocked_by_stop" in stats:
            stats["blocked_by_stop"] += 1
