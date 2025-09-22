"""
Centroid Matching System
Fast mechanical matching for Event Families to narrative centroids
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session


@dataclass
class MatchResult:
    """Result of centroid matching"""

    centroid_id: Optional[str]
    confidence_score: float
    match_details: Dict[str, Any]
    requires_llm_verification: bool


class CentroidMatcher:
    """
    Mechanical centroid matching with confidence scoring

    Scoring: (Keywords 40%) + (Actors 30%) + (Theaters 20%) + (Event Type 10%)
    Thresholds: High ≥0.7, Medium 0.4-0.69, Low <0.4
    """

    def __init__(self):
        self.centroids: List[Dict[str, Any]] = []
        self.actor_variants = self._build_actor_variants()
        self.theater_hierarchy = self._build_theater_hierarchy()
        self.event_type_bonuses = self._build_event_type_bonuses()
        self._load_centroids()

    def _load_centroids(self) -> None:
        """Load centroid data from database"""
        try:
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                    SELECT id, label, keywords, actors, theaters
                    FROM centroids
                    ORDER BY id
                """
                    )
                ).fetchall()

                self.centroids = [
                    {
                        "id": row.id,
                        "label": row.label,
                        "keywords": [kw.lower().strip() for kw in row.keywords],
                        "actors": [actor.strip() for actor in row.actors],
                        "theaters": [theater.strip() for theater in row.theaters],
                    }
                    for row in result
                ]

                logger.info(f"Loaded {len(self.centroids)} centroids for matching")

        except Exception as e:
            logger.error(f"Failed to load centroids: {e}")
            self.centroids = []

    def _build_actor_variants(self) -> Dict[str, List[str]]:
        """Build actor name variations for fuzzy matching"""
        return {
            "united states": ["us", "usa", "america", "united states"],
            "china": ["china", "prc", "peoples republic of china"],
            "russia": ["russia", "russian federation", "rf"],
            "european union": ["eu", "european union"],
            "united kingdom": ["uk", "britain", "united kingdom", "great britain"],
            "north korea": [
                "north korea",
                "dprk",
                "democratic peoples republic of korea",
            ],
            "south korea": ["south korea", "rok", "republic of korea"],
        }

    def _build_theater_hierarchy(self) -> Dict[str, List[str]]:
        """Build geographic theater containment relationships"""
        return {
            "eastern europe": ["ukraine", "poland", "belarus", "baltic states"],
            "middle east": [
                "israel",
                "gaza",
                "west bank",
                "syria",
                "lebanon",
                "jordan",
            ],
            "persian gulf": ["iran", "iraq", "kuwait", "bahrain", "qatar", "uae"],
            "southeast asia": ["myanmar", "thailand", "vietnam", "laos", "cambodia"],
            "south asia": ["india", "pakistan", "bangladesh", "sri lanka"],
            "east china sea": ["taiwan strait"],
            "south china sea": ["spratly islands", "paracel islands"],
            "west africa": ["mali", "niger", "burkina faso", "ghana"],
            "horn of africa": ["ethiopia", "eritrea", "somalia", "djibouti"],
            "balkans": ["serbia", "kosovo", "bosnia", "montenegro", "albania"],
        }

    def _build_event_type_bonuses(self) -> Dict[str, Dict[str, float]]:
        """Event type compatibility bonuses for specific centroids"""
        return {
            "military_conflict": {
                "ARC-UKR": 0.2,
                "ARC-MIDEAST-ISR": 0.2,
                "ARC-CHN-TWN": 0.15,
                "ARC-KOREA": 0.15,
            },
            "political_violence": {
                "ARC-US-ELECT": 0.15,
                "ARC-MYANMAR": 0.1,
            },
            "cyber_attack": {
                "ARC-TECH": 0.2,
                "ARC-INFOOPS": 0.15,
            },
            "energy_crisis": {
                "ARC-ENERGY": 0.25,
                "ARC-CLIMATE": 0.1,
            },
            "trade_dispute": {
                "ARC-TRADE": 0.25,
                "ARC-TECH": 0.1,
            },
        }

    def _normalize_actor(self, actor: str) -> str:
        """Normalize actor name for matching"""
        actor_lower = actor.lower().strip()

        for canonical, variants in self.actor_variants.items():
            if actor_lower in variants:
                return canonical

        return actor_lower

    def _fuzzy_string_match(
        self, text1: str, text2: str, threshold: float = 0.8
    ) -> bool:
        """Check if two strings are similar enough"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() >= threshold

    def _score_keywords(self, ef_text: str, centroid_keywords: List[str]) -> float:
        """Score keyword matching between EF and centroid"""
        if not centroid_keywords:
            return 0.0

        ef_text_lower = ef_text.lower()
        matches = 0

        for keyword in centroid_keywords:
            # Exact match
            if keyword in ef_text_lower:
                matches += 1
            # Partial word match (e.g., "ukraine" matches "ukrainian")
            elif any(
                self._fuzzy_string_match(keyword, word)
                for word in ef_text_lower.split()
            ):
                matches += 0.7

        return min(matches / len(centroid_keywords), 1.0)

    def _score_actors(self, ef_actors: List[str], centroid_actors: List[str]) -> float:
        """Score actor matching between EF and centroid"""
        if not centroid_actors or not ef_actors:
            return 0.0

        normalized_ef_actors = {self._normalize_actor(actor) for actor in ef_actors}
        normalized_centroid_actors = {
            self._normalize_actor(actor) for actor in centroid_actors
        }

        matches = len(normalized_ef_actors.intersection(normalized_centroid_actors))
        return matches / len(normalized_centroid_actors)

    def _score_theaters(self, ef_theater: str, centroid_theaters: List[str]) -> float:
        """Score theater/geographic matching"""
        if not centroid_theaters or not ef_theater:
            return 0.0

        ef_theater_lower = ef_theater.lower().strip()

        # Direct match
        for theater in centroid_theaters:
            if theater.lower() == ef_theater_lower:
                return 1.0

        # Hierarchical containment check
        for parent, children in self.theater_hierarchy.items():
            if parent in [t.lower() for t in centroid_theaters]:
                if ef_theater_lower in children:
                    return 0.8

        # Fuzzy geographic match
        for theater in centroid_theaters:
            if self._fuzzy_string_match(ef_theater_lower, theater.lower(), 0.8):
                return 0.6

        return 0.0

    def _score_event_type(self, event_type: str, centroid_id: str) -> float:
        """Score event type compatibility"""
        if not event_type:
            return 0.0

        bonuses = self.event_type_bonuses.get(event_type, {})
        return bonuses.get(centroid_id, 0.0)

    def match_centroid(
        self,
        ef_title: str,
        ef_summary: str,
        ef_actors: List[str],
        primary_theater: str,
        event_type: str,
    ) -> MatchResult:
        """
        Find best matching centroid for an Event Family

        Args:
            ef_title: Event Family title
            ef_summary: Event Family summary
            ef_actors: List of canonical actors
            primary_theater: Primary geographic theater
            event_type: Event type classification

        Returns:
            MatchResult with best match and confidence
        """
        if not self.centroids:
            logger.warning("No centroids loaded, cannot perform matching")
            return MatchResult(
                centroid_id=None,
                confidence_score=0.0,
                match_details={},
                requires_llm_verification=True,
            )

        ef_text = f"{ef_title} {ef_summary}".strip()
        best_score = 0.0
        best_centroid = None
        all_scores = {}

        for centroid in self.centroids:
            # Calculate component scores
            keyword_score = self._score_keywords(ef_text, centroid["keywords"])
            actor_score = self._score_actors(ef_actors, centroid["actors"])
            theater_score = self._score_theaters(primary_theater, centroid["theaters"])
            event_type_score = self._score_event_type(event_type, centroid["id"])

            # Weighted composite score
            total_score = (
                keyword_score * 0.4
                + actor_score * 0.3
                + theater_score * 0.2
                + event_type_score * 0.1
            )

            all_scores[centroid["id"]] = {
                "total": total_score,
                "keyword": keyword_score,
                "actor": actor_score,
                "theater": theater_score,
                "event_type": event_type_score,
            }

            if total_score > best_score:
                best_score = total_score
                best_centroid = centroid["id"]

        # Determine confidence level and LLM verification need
        requires_llm = False
        if best_score >= 0.7:
            # High confidence - auto-assign
            confidence_level = "high"
        elif best_score >= 0.4:
            # Medium confidence - needs LLM verification
            confidence_level = "medium"
            requires_llm = True
        else:
            # Low confidence - no mechanical match
            confidence_level = "low"
            best_centroid = None
            requires_llm = True

        match_details = {
            "confidence_level": confidence_level,
            "all_scores": all_scores,
            "best_centroid_scores": (
                all_scores.get(best_centroid, {}) if best_centroid else {}
            ),
        }

        logger.debug(
            f"Centroid matching: {confidence_level} confidence, "
            f"score {best_score:.3f}, centroid {best_centroid}"
        )

        return MatchResult(
            centroid_id=best_centroid,
            confidence_score=best_score,
            match_details=match_details,
            requires_llm_verification=requires_llm,
        )

    def get_top_candidates(
        self,
        ef_title: str,
        ef_summary: str,
        ef_actors: List[str],
        primary_theater: str,
        event_type: str,
        top_n: int = 5,
    ) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Get top N centroid candidates with scores for LLM assessment

        Returns:
            List of (centroid_id, total_score, component_scores) tuples
        """
        match_result = self.match_centroid(
            ef_title, ef_summary, ef_actors, primary_theater, event_type
        )

        all_scores = match_result.match_details.get("all_scores", {})

        # Sort by total score
        sorted_scores = sorted(
            all_scores.items(), key=lambda x: x[1]["total"], reverse=True
        )

        return [
            (centroid_id, scores["total"], scores)
            for centroid_id, scores in sorted_scores[:top_n]
        ]
