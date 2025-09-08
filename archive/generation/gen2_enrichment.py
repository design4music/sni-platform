#!/usr/bin/env python3
"""
GEN-2: Enrichment & Stance Analysis
Strategic Narrative Intelligence Platform

Enhances narrative cards with strategic context analysis:
- Alignment assessment (neutral/pro/anti stance)
- Actor origin identification (primary countries/actors)
- Frame logic analysis (cause→effect relationships)
- Turning points extraction from cluster timeline
- Narrative tension and logical strain scoring

Uses existing JSONB columns with no schema changes.
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import psycopg2
import psycopg2.extras

# Add project root to path for centralized config
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from etl_pipeline.core.config import get_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NarrativeEnricher:
    """Enhance narrative cards with strategic metadata and stance analysis."""

    def __init__(self, batch_size: int = 20, force: bool = False):
        self.batch_size = batch_size
        self.force = force
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0

        # Strategic keyword patterns for analysis
        self.stance_indicators = {
            "pro": [
                "supports",
                "endorses",
                "welcomes",
                "praises",
                "approves",
                "backs",
                "champions",
            ],
            "anti": [
                "opposes",
                "condemns",
                "rejects",
                "criticizes",
                "denounces",
                "protests",
                "disputes",
            ],
            "neutral": [
                "reports",
                "states",
                "announces",
                "confirms",
                "indicates",
                "reveals",
                "shows",
            ],
        }

        self.actor_patterns = {
            "countries": [
                "United States",
                "China",
                "Russia",
                "European Union",
                "Germany",
                "France",
                "UK",
                "Japan",
                "India",
            ],
            "organizations": ["NATO", "UN", "World Bank", "IMF", "WHO", "WTO", "OPEC"],
            "leaders": [
                "President",
                "Prime Minister",
                "Chancellor",
                "Secretary",
                "Minister",
                "Director",
            ],
        }

        self.causal_indicators = [
            "because of",
            "due to",
            "as a result",
            "leading to",
            "causing",
            "triggered by",
            "in response to",
            "following",
            "after",
            "prompted by",
            "resulting in",
        ]

    def get_pending_narratives(self, conn) -> List[Dict]:
        """Get narratives ready for GEN-2 enrichment."""
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Select narratives with GEN-1 complete but not GEN-2
        base_query = """
        SELECT 
            id, narrative_id, title, summary, top_excerpts, source_stats,
            activity_timeline, alignment, actor_origin, frame_logic, 
            turning_points, narrative_tension, logical_strain,
            update_status, version_history, created_at, updated_at
        FROM narratives 
        WHERE consolidation_stage = 'consolidated'
          AND archive_reason IS NULL
          AND (update_status->'gen'->>'gen1_done_at') IS NOT NULL
        """

        if self.force:
            # Force regeneration - process all GEN-1 complete narratives
            query = base_query + " ORDER BY updated_at DESC LIMIT %s"
            cursor.execute(query, (self.batch_size,))
        else:
            # Only process narratives without GEN-2 completion
            query = (
                base_query
                + """
              AND (update_status->'gen'->>'gen2_done_at') IS NULL
            ORDER BY updated_at DESC LIMIT %s
            """
            )
            cursor.execute(query, (self.batch_size,))

        narratives = cursor.fetchall()
        cursor.close()

        logger.info(f"Found {len(narratives)} narratives ready for GEN-2 processing")
        return [dict(n) for n in narratives]

    def analyze_alignment(self, narrative: Dict) -> Dict:
        """Analyze narrative stance and alignment toward main actors."""
        title = narrative.get("title", "").lower()
        summary = narrative.get("summary", "").lower()
        text = f"{title} {summary}"

        # Count stance indicators
        stance_scores = {"pro": 0, "anti": 0, "neutral": 0}
        main_actor = "unknown"

        # Identify main actor from known patterns
        for actor in (
            self.actor_patterns["countries"] + self.actor_patterns["organizations"]
        ):
            if actor.lower() in text:
                main_actor = actor
                break

        # Score stance indicators
        for stance, indicators in self.stance_indicators.items():
            stance_scores[stance] = sum(
                1 for indicator in indicators if indicator in text
            )

        # Determine primary stance
        total_indicators = sum(stance_scores.values())
        if total_indicators == 0:
            primary_stance = "neutral"
            confidence = 0.5
        else:
            primary_stance = max(stance_scores, key=stance_scores.get)
            confidence = stance_scores[primary_stance] / total_indicators

        return {
            "stance": primary_stance,
            "target": main_actor,
            "confidence": round(confidence, 2),
            "scores": stance_scores,
            "indicators_found": total_indicators,
        }

    def extract_actor_origin(self, narrative: Dict) -> List[str]:
        """Extract primary countries and organizational actors."""
        title = narrative.get("title", "")
        summary = narrative.get("summary", "")
        text = f"{title} {summary}"

        detected_actors = []

        # Extract country actors
        for country in self.actor_patterns["countries"]:
            if country.lower() in text.lower():
                detected_actors.append(country)

        # Extract organizational actors
        for org in self.actor_patterns["organizations"]:
            if org.lower() in text.lower():
                detected_actors.append(org)

        # Extract leader-based actors
        leader_pattern = (
            r"(President|Prime Minister|Chancellor|Secretary|Minister)\s+(\w+)"
        )
        leaders = re.findall(leader_pattern, text, re.IGNORECASE)
        for title_role, name in leaders:
            detected_actors.append(f"{title_role} {name}")

        # Remove duplicates and limit to top 5
        unique_actors = list(dict.fromkeys(detected_actors))[:5]

        # Ensure at least one actor
        if not unique_actors:
            unique_actors = ["Unknown Actor"]

        return unique_actors

    def analyze_frame_logic(self, narrative: Dict) -> Dict:
        """Extract cause-effect relationships and framing logic."""
        title = narrative.get("title", "")
        summary = narrative.get("summary", "")
        text = f"{title}. {summary}"

        # Find causal relationships
        causal_matches = []
        for indicator in self.causal_indicators:
            if indicator in text.lower():
                # Extract context around causal indicator
                pattern = rf"([^.]*{re.escape(indicator)}[^.]*)"
                matches = re.findall(pattern, text, re.IGNORECASE)
                causal_matches.extend(matches)

        # Analyze sentence structure for cause-effect
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        cause = "Multiple contributing factors"
        effect = "Strategic implications"

        if causal_matches:
            # Extract best causal relationship
            longest_match = max(causal_matches, key=len)
            parts = re.split(
                "|".join(self.causal_indicators), longest_match, flags=re.IGNORECASE
            )
            if len(parts) >= 2:
                cause = parts[0].strip()[:100]  # Limit length
                effect = parts[1].strip()[:100]
        elif sentences:
            # Use first and last sentences as proxy for cause-effect
            if len(sentences) >= 2:
                cause = sentences[0][:100]
                effect = sentences[-1][:100]

        return {
            "cause": cause,
            "effect": effect,
            "causal_indicators": len(causal_matches),
            "logic_strength": min(1.0, len(causal_matches) / 3.0),
        }

    def extract_turning_points(self, narrative: Dict) -> List[Dict]:
        """Extract key turning points from cluster timeline and content."""
        activity_timeline = narrative.get("activity_timeline")
        turning_points = []

        # Extract dates from activity timeline
        if activity_timeline:
            try:
                # Handle both list and dict timeline formats
                timeline_entries = []
                if isinstance(activity_timeline, list):
                    timeline_entries = activity_timeline
                elif (
                    isinstance(activity_timeline, dict)
                    and "cluster_evidence" in activity_timeline
                ):
                    timeline_entries = activity_timeline["cluster_evidence"]

                for entry in timeline_entries:
                    if isinstance(entry, dict) and "ts" in entry:
                        timestamp = entry["ts"]
                        # Convert to date
                        try:
                            if isinstance(timestamp, str):
                                dt = datetime.fromisoformat(
                                    timestamp.replace("Z", "+00:00")
                                )
                                date_str = dt.date().isoformat()
                                turning_points.append(
                                    {
                                        "date": date_str,
                                        "desc": f"Cluster formation with {entry.get('size', 1)} articles",
                                        "significance": min(
                                            1.0, entry.get("size", 1) / 10.0
                                        ),
                                    }
                                )
                        except ValueError:
                            continue
            except Exception as e:
                logger.warning(f"Error extracting timeline turning points: {e}")

        # Extract dates from text content
        title = narrative.get("title", "")
        summary = narrative.get("summary", "")
        text = f"{title} {summary}"

        # Look for date patterns and associated events
        date_patterns = [
            r"\b(\d{4}-\d{2}-\d{2})\b",  # YYYY-MM-DD
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:3]:  # Limit to 3 matches
                date_text = match if isinstance(match, str) else " ".join(match)
                turning_points.append(
                    {
                        "date": date_text,
                        "desc": "Key development mentioned in narrative",
                        "significance": 0.7,
                    }
                )

        # Ensure at least one turning point
        if not turning_points:
            turning_points.append(
                {
                    "date": datetime.now().date().isoformat(),
                    "desc": "Narrative consolidation point",
                    "significance": 0.5,
                }
            )

        # Sort by significance and limit to top 5
        turning_points.sort(key=lambda x: x["significance"], reverse=True)
        return turning_points[:5]

    def calculate_narrative_tension(self, narrative: Dict) -> float:
        """Calculate narrative tension score (0-1) based on conflict indicators."""
        title = narrative.get("title", "").lower()
        summary = narrative.get("summary", "").lower()
        text = f"{title} {summary}"

        # Tension indicators
        high_tension_words = [
            "crisis",
            "conflict",
            "war",
            "sanctions",
            "threatens",
            "escalates",
            "clash",
        ]
        medium_tension_words = [
            "tensions",
            "disputes",
            "concerns",
            "challenges",
            "pressure",
            "confronts",
        ]
        tension_words = [
            "disagree",
            "opposition",
            "criticism",
            "protests",
            "resistance",
        ]

        # Score tension indicators
        high_count = sum(1 for word in high_tension_words if word in text)
        medium_count = sum(1 for word in medium_tension_words if word in text)
        low_count = sum(1 for word in tension_words if word in text)

        # Calculate weighted tension score
        tension_score = high_count * 1.0 + medium_count * 0.6 + low_count * 0.3

        # Normalize to 0-1 scale
        max_possible = 5.0  # Reasonable maximum
        normalized_score = min(1.0, tension_score / max_possible)

        return round(normalized_score, 3)

    def calculate_logical_strain(self, narrative: Dict) -> float:
        """Calculate logical strain score (0-1) based on coherence indicators."""
        title = narrative.get("title", "")
        summary = narrative.get("summary", "")

        # Logical strain indicators
        strain_indicators = [
            "however",
            "but",
            "contradicts",
            "despite",
            "although",
            "while",
            "unclear",
            "disputed",
        ]
        coherence_indicators = [
            "therefore",
            "thus",
            "consequently",
            "as a result",
            "leading to",
            "because",
        ]

        text = f"{title} {summary}".lower()

        strain_count = sum(1 for indicator in strain_indicators if indicator in text)
        coherence_count = sum(
            1 for indicator in coherence_indicators if indicator in text
        )

        # Calculate logical strain (more strain = less coherence)
        total_indicators = strain_count + coherence_count
        if total_indicators == 0:
            return 0.3  # Moderate default strain

        strain_ratio = strain_count / total_indicators

        # Add complexity penalties
        sentences = [s.strip() for s in summary.split(".") if s.strip()]
        if len(sentences) > 5:  # Very long summaries may indicate strain
            strain_ratio += 0.1

        return round(min(1.0, strain_ratio), 3)

    def update_narrative_enrichment(
        self, conn, narrative_id: int, enrichment: Dict
    ) -> bool:
        """Update narrative with GEN-2 enrichment data."""
        cursor = conn.cursor()

        try:
            # Get current update_status and version_history
            cursor.execute(
                "SELECT update_status, version_history FROM narratives WHERE id = %s",
                (narrative_id,),
            )
            result = cursor.fetchone()
            if not result:
                logger.error(f"Narrative {narrative_id} not found")
                return False

            current_status, current_history = result

            # Update progress tracking
            now_iso = datetime.now(timezone.utc).isoformat()

            # Enhance update_status with GEN-2 completion
            new_status = current_status.copy() if current_status else {}
            new_status.update(
                {
                    "last_updated": now_iso,
                    "update_trigger": "gen2_enrichment",
                    "gen": {
                        **new_status.get("gen", {}),
                        "gen2_done_at": now_iso,
                        "gen2_version": "1.0",
                        "publication_ready": True,  # Ready for publication after GEN-2
                    },
                }
            )

            # Update version_history
            new_history = current_history.copy() if current_history else {}
            gen2_entry = {
                "timestamp": now_iso,
                "stage": "gen2_enrichment",
                "action": "stance_analysis_complete",
                "alignment": enrichment["alignment"],
                "actors_count": len(enrichment["actor_origin"]),
                "tension_score": enrichment["narrative_tension"],
                "strain_score": enrichment["logical_strain"],
                "turning_points": len(enrichment["turning_points"]),
            }

            if "gen2_history" not in new_history:
                new_history["gen2_history"] = []
            new_history["gen2_history"].append(gen2_entry)

            # Execute update with all enrichment fields
            update_query = """
            UPDATE narratives 
            SET alignment = %s,
                actor_origin = %s,
                frame_logic = %s,
                turning_points = %s,
                narrative_tension = %s,
                logical_strain = %s,
                update_status = %s,
                version_history = %s,
                updated_at = NOW()
            WHERE id = %s
            """

            cursor.execute(
                update_query,
                (
                    json.dumps(enrichment["alignment"]),
                    json.dumps(enrichment["actor_origin"]),
                    json.dumps(enrichment["frame_logic"]),
                    json.dumps(enrichment["turning_points"]),
                    enrichment["narrative_tension"],
                    enrichment["logical_strain"],
                    json.dumps(new_status),
                    json.dumps(new_history),
                    narrative_id,
                ),
            )

            conn.commit()
            logger.debug(f"Updated narrative {narrative_id} with GEN-2 enrichment")
            return True

        except Exception as e:
            logger.error(f"Error updating narrative {narrative_id}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()

    def process_narrative(self, conn, narrative: Dict) -> bool:
        """Process a single narrative through GEN-2 enrichment."""
        narrative_id = narrative["id"]

        try:
            logger.debug(f"Processing narrative {narrative_id} for enrichment")

            # Generate all enrichment components
            alignment = self.analyze_alignment(narrative)
            actor_origin = self.extract_actor_origin(narrative)
            frame_logic = self.analyze_frame_logic(narrative)
            turning_points = self.extract_turning_points(narrative)
            narrative_tension = self.calculate_narrative_tension(narrative)
            logical_strain = self.calculate_logical_strain(narrative)

            # Quality validation
            if len(actor_origin) == 0:
                logger.warning(f"No actors identified for narrative {narrative_id}")

            if alignment["indicators_found"] == 0:
                logger.warning(
                    f"No stance indicators found for narrative {narrative_id}"
                )

            # Package enrichment data
            enrichment = {
                "alignment": alignment,
                "actor_origin": actor_origin,
                "frame_logic": frame_logic,
                "turning_points": turning_points,
                "narrative_tension": narrative_tension,
                "logical_strain": logical_strain,
            }

            # Update database
            if self.update_narrative_enrichment(conn, narrative_id, enrichment):
                self.success_count += 1
                logger.info(
                    f"SUCCESS: Enriched narrative {narrative_id} (tension: {narrative_tension}, strain: {logical_strain})"
                )
                return True
            else:
                self.error_count += 1
                return False

        except Exception as e:
            logger.error(f"Error processing narrative {narrative_id}: {e}")
            self.error_count += 1
            return False

    def run_enrichment(self) -> Dict:
        """Run complete GEN-2 enrichment process."""
        start_time = time.time()
        logger.info("Starting GEN-2 narrative enrichment and stance analysis")

        try:
            conn = get_db_connection()

            # Get narratives ready for processing
            narratives = self.get_pending_narratives(conn)

            if not narratives:
                logger.info("No narratives ready for GEN-2 processing")
                return self.get_results_summary(start_time)

            # Process each narrative
            for narrative in narratives:
                self.processed_count += 1
                self.process_narrative(conn, narrative)

            conn.close()

        except Exception as e:
            logger.error(f"GEN-2 enrichment failed: {e}")
            if "conn" in locals():
                conn.close()

        return self.get_results_summary(start_time)

    def get_results_summary(self, start_time: float) -> Dict:
        """Generate processing results summary."""
        elapsed_time = time.time() - start_time
        success_rate = (
            (self.success_count / self.processed_count * 100)
            if self.processed_count > 0
            else 0
        )

        results = {
            "processed": self.processed_count,
            "successful": self.success_count,
            "errors": self.error_count,
            "success_rate": f"{success_rate:.1f}%",
            "elapsed_time": f"{elapsed_time:.1f}s",
            "rate_per_second": (
                f"{self.processed_count / elapsed_time:.2f}"
                if elapsed_time > 0
                else "0"
            ),
        }

        logger.info(f"GEN-2 SUMMARY: {results}")
        return results


def main():
    """Main entry point for GEN-2 enrichment."""
    parser = argparse.ArgumentParser(description="GEN-2: Enrichment & Stance Analysis")
    parser.add_argument(
        "--batch", type=int, default=20, help="Batch size for processing (default: 20)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force regeneration of all enrichments"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize and run enricher
    enricher = NarrativeEnricher(batch_size=args.batch, force=args.force)
    results = enricher.run_enrichment()

    # Display results
    print("\n" + "=" * 50)
    print("GEN-2 ENRICHMENT & STANCE ANALYSIS COMPLETE")
    print("=" * 50)
    print(f"Processed: {results['processed']} narratives")
    print(f"Successful: {results['successful']} enrichments")
    print(f"Errors: {results['errors']} failed")
    print(f"Success Rate: {results['success_rate']}")
    print(f"Processing Time: {results['elapsed_time']}")
    print(f"Rate: {results['rate_per_second']} narratives/second")

    # Exit with appropriate code
    exit_code = 0 if results["errors"] == 0 else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
