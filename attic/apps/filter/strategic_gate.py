"""
CLUST-001: Strategic Gate Filtering
Multi-vocabulary filtering with go/stop lists

Logic:
- STOP lists override GO lists (stop_culture.csv beats everything)
- GO lists: actors.csv, go_people.csv, go_taxonomy.csv (when ready) → strategic
- Fast word-boundary matching for Latin/Cyrillic, substring for CJK/Thai
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor


@dataclass
class GateResult:
    """Result of strategic gate filtering with telemetry"""

    keep: bool
    score: float  # 0.99 for strategic_hit, 0.0 for no match
    reason: str  # "strategic_hit" | "blocked_by_stop" | "no_strategic"
    anchor_labels: List[str]  # empty (legacy field)
    anchor_scores: List[tuple[str, float]]  # empty (legacy field)
    actor_hit: Optional[str] = None  # matching entity_id from any go list


class StrategicGate:
    """Strategic Gate Filter with multi-vocabulary go/stop list logic"""

    def __init__(self):
        # Load multi-vocabulary taxonomy extractor (now DB-backed)
        try:
            self._taxonomy_extractor = create_multi_vocab_taxonomy_extractor()
        except Exception as e:
            raise RuntimeError(f"Failed to load taxonomy vocabularies: {e}")

    def filter_title(self, title_text: str) -> GateResult:
        """
        Apply strategic gate filtering with go/stop list precedence.

        Args:
            title_text: The title text to evaluate (will be normalized)

        Returns:
            GateResult with filtering decision and telemetry

        Logic:
        1. If stop_culture.csv matches → NON-strategic (stop overrides all)
        2. If actors.csv OR go_people.csv OR go_taxonomy.csv match → STRATEGIC
        3. No matches → NON-strategic
        """
        if not title_text:
            return GateResult(False, 0.0, "no_strategic", [], [])

        # Use enhanced multi-vocabulary logic
        strategic_hit = self._taxonomy_extractor.strategic_first_hit(title_text)

        if strategic_hit:
            return GateResult(
                keep=True,
                score=0.99,
                reason="strategic_hit",
                anchor_labels=[],  # Legacy field
                anchor_scores=[],  # Legacy field
                actor_hit=strategic_hit,
            )

        # No strategic content found (either blocked by stop list or no matches)
        return GateResult(
            keep=False,
            score=0.0,
            reason="no_strategic",
            anchor_labels=[],
            anchor_scores=[],
        )


def filter_titles_batch(
    titles: List[Dict[str, Any]],
) -> List[tuple[Dict[str, Any], GateResult]]:
    """
    Batch filter titles through strategic gate with fast actor matching.

    Args:
        titles: List of title dictionaries with 'title_norm' or 'title_display' fields

    Returns:
        List of (title, gate_result) tuples
    """
    if not titles:
        return []

    gate = StrategicGate()
    results = []

    for title in titles:
        # Use title_norm if available, fallback to title_display
        title_text = title.get("title_norm") or title.get("title_display", "")

        # Apply simplified gate logic
        result = gate.filter_title(title_text)
        results.append((title, result))

    return results


def get_strategic_gate_service() -> StrategicGate:
    """Factory function to get strategic gate service."""
    return StrategicGate()
