"""
CLUST-001: Strategic Gate Filtering
Simplified actor-based filtering with fast string matching

Logic:
- Keep if: actor alias match (geopolitical entities, strategic actors)
- No domain exclusions (all feeds are curated strategic sources)
- Fast word-boundary matching for Latin/Cyrillic, substring for CJK/Thai
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from apps.clust1.actor_extractor import create_actor_extractor
from core.config import get_config


@dataclass
class GateResult:
    """Result of strategic gate filtering with telemetry"""

    keep: bool
    score: float  # 0.99 for actor_hit, 0.0 for no match
    reason: str  # "actor_hit" | "no_actor"
    anchor_labels: List[str]  # empty (legacy field)
    anchor_scores: List[tuple[str, float]]  # empty (legacy field)
    actor_hit: Optional[str] = None  # canonical actor code (e.g., "US")


class StrategicGate:
    """Strategic Gate Filter - determines if headlines have strategic relevance"""

    def __init__(self):
        self.config = get_config()
        self._validate_config()

        # Load actor vocabulary only
        try:
            self._actor_extractor = create_actor_extractor()
        except Exception as e:
            raise RuntimeError(f"Failed to load actor vocabulary: {e}")

    def _validate_config(self):
        """Validate required config parameters exist"""
        required_attrs = ["actors_csv_path"]
        for attr in required_attrs:
            if not hasattr(self.config, attr):
                raise ValueError(f"Missing required config parameter: {attr}")

    def filter_title(self, title_text: str) -> GateResult:
        """
        Apply strategic gate filtering to a single title.

        Args:
            title_text: The title text to evaluate (will be normalized)

        Returns:
            GateResult with filtering decision and telemetry
        """
        if not title_text:
            return GateResult(False, 0.0, "no_actor", [], [])

        # Check for actor matches (fast path)
        actor_hit = self._actor_extractor.first_hit(title_text)
        if actor_hit:
            return GateResult(
                keep=True,
                score=0.99,  # Fixed score for actor hits
                reason="actor_hit",
                anchor_labels=[],  # No longer used
                anchor_scores=[],  # No longer used
                actor_hit=actor_hit,
            )

        # No actor found
        return GateResult(
            keep=False, score=0.0, reason="no_actor", anchor_labels=[], anchor_scores=[]
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
