"""
GEN-1 Validation and Quality Control
Validation logic for Event Families and Framed Narratives
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from loguru import logger

from apps.gen1.models import EventFamily, FramedNarrative


class Gen1Validator:
    """
    Quality control and validation for GEN-1 processing results
    Ensures Event Families and Framed Narratives meet quality standards
    """

    def __init__(self):
        # Quality thresholds
        self.min_confidence_score = 0.3
        self.min_coherence_length = 20
        self.max_event_span_days = 30
        self.min_narrative_evidence = 1
        self.min_prevalence_score = 0.1

    def validate_event_family(self, event_family: EventFamily) -> Tuple[bool, List[str]]:
        """
        Validate an Event Family for quality and completeness
        
        Args:
            event_family: EventFamily to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Required fields validation
        if not event_family.title or len(event_family.title.strip()) < 5:
            issues.append("Title is too short or empty")

        if not event_family.summary or len(event_family.summary.strip()) < 20:
            issues.append("Summary is too short or empty")

        if not event_family.event_type or len(event_family.event_type.strip()) == 0:
            issues.append("Event type is missing")

        if not event_family.key_actors:
            issues.append("No key actors identified")

        # Confidence score validation
        if event_family.confidence_score < self.min_confidence_score:
            issues.append(f"Confidence score too low: {event_family.confidence_score:.2f}")

        # Coherence reason validation
        if len(event_family.coherence_reason.strip()) < self.min_coherence_length:
            issues.append("Coherence reason is too brief")

        # Time validation
        if event_family.event_end:
            if event_family.event_end < event_family.event_start:
                issues.append("Event end time is before start time")

            event_span = event_family.event_end - event_family.event_start
            if event_span.days > self.max_event_span_days:
                issues.append(f"Event span too long: {event_span.days} days")

        # Source data validation
        if not event_family.source_title_ids:
            issues.append("No source titles referenced")

        if not event_family.source_bucket_ids:
            issues.append("No source buckets referenced")

        # Actor validation
        if len(event_family.key_actors) > 10:
            issues.append("Too many key actors (>10) - may indicate poor focus")

        # Title uniqueness check (basic)
        if len(set(event_family.source_title_ids)) != len(event_family.source_title_ids):
            issues.append("Duplicate title IDs in source_title_ids")

        is_valid = len(issues) == 0

        if not is_valid:
            logger.debug(f"Event Family validation failed: {event_family.id}", issues=issues)

        return is_valid, issues

    def validate_framed_narrative(
        self, framed_narrative: FramedNarrative
    ) -> Tuple[bool, List[str]]:
        """
        Validate a Framed Narrative for quality and completeness
        
        Args:
            framed_narrative: FramedNarrative to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Required fields validation
        if not framed_narrative.frame_type or len(framed_narrative.frame_type.strip()) == 0:
            issues.append("Frame type is missing")

        if not framed_narrative.frame_description or len(framed_narrative.frame_description.strip()) < 10:
            issues.append("Frame description is too short or empty")

        if not framed_narrative.stance_summary or len(framed_narrative.stance_summary.strip()) < 10:
            issues.append("Stance summary is too short or empty")

        # Evidence validation
        if not framed_narrative.supporting_headlines and not framed_narrative.supporting_title_ids:
            issues.append("No supporting evidence provided")

        if (
            len(framed_narrative.supporting_headlines) < self.min_narrative_evidence
            and len(framed_narrative.supporting_title_ids) < self.min_narrative_evidence
        ):
            issues.append("Insufficient supporting evidence")

        # Score validation
        if framed_narrative.prevalence_score < self.min_prevalence_score:
            issues.append(f"Prevalence score too low: {framed_narrative.prevalence_score:.2f}")

        if framed_narrative.evidence_quality < 0.2:
            issues.append(f"Evidence quality too low: {framed_narrative.evidence_quality:.2f}")

        # Language validation
        if not framed_narrative.key_language:
            issues.append("No key language phrases identified")

        # Consistency checks
        if (
            framed_narrative.supporting_title_ids
            and framed_narrative.supporting_headlines
            and len(framed_narrative.supporting_title_ids) != len(framed_narrative.supporting_headlines)
        ):
            issues.append("Mismatch between supporting titles and headlines count")

        is_valid = len(issues) == 0

        if not is_valid:
            logger.debug(f"Framed Narrative validation failed: {framed_narrative.id}", issues=issues)

        return is_valid, issues

    def validate_processing_result(
        self, event_families: List[EventFamily], framed_narratives: List[FramedNarrative]
    ) -> Dict[str, Any]:
        """
        Validate complete processing result for quality metrics
        
        Args:
            event_families: List of Event Families to validate
            framed_narratives: List of Framed Narratives to validate
            
        Returns:
            Dictionary with validation summary and metrics
        """
        result = {
            "event_families": {
                "total": len(event_families),
                "valid": 0,
                "invalid": 0,
                "issues": [],
            },
            "framed_narratives": {
                "total": len(framed_narratives),
                "valid": 0,
                "invalid": 0,
                "issues": [],
            },
            "overall": {
                "quality_score": 0.0,
                "recommendations": [],
            },
        }

        # Validate Event Families
        for ef in event_families:
            is_valid, issues = self.validate_event_family(ef)
            if is_valid:
                result["event_families"]["valid"] += 1
            else:
                result["event_families"]["invalid"] += 1
                result["event_families"]["issues"].extend(issues)

        # Validate Framed Narratives
        for fn in framed_narratives:
            is_valid, issues = self.validate_framed_narrative(fn)
            if is_valid:
                result["framed_narratives"]["valid"] += 1
            else:
                result["framed_narratives"]["invalid"] += 1
                result["framed_narratives"]["issues"].extend(issues)

        # Calculate overall quality score
        total_items = len(event_families) + len(framed_narratives)
        valid_items = result["event_families"]["valid"] + result["framed_narratives"]["valid"]

        if total_items > 0:
            result["overall"]["quality_score"] = valid_items / total_items
        else:
            result["overall"]["quality_score"] = 1.0

        # Generate recommendations
        result["overall"]["recommendations"] = self._generate_recommendations(result)

        logger.info(
            f"Validation completed: {valid_items}/{total_items} items valid "
            f"(quality score: {result['overall']['quality_score']:.2f})"
        )

        return result

    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        ef_result = validation_result["event_families"]
        fn_result = validation_result["framed_narratives"]

        # Event Family recommendations
        if ef_result["invalid"] > ef_result["valid"]:
            recommendations.append("Consider raising confidence thresholds for Event Family assembly")

        if "Coherence reason is too brief" in ef_result["issues"]:
            recommendations.append("Improve LLM prompting for more detailed coherence explanations")

        # Framed Narrative recommendations
        if fn_result["invalid"] > fn_result["valid"]:
            recommendations.append("Consider improving evidence collection for Framed Narratives")

        if "No key language phrases identified" in fn_result["issues"]:
            recommendations.append("Enhance LLM prompting for key language extraction")

        # Overall recommendations
        quality_score = validation_result["overall"]["quality_score"]
        if quality_score < 0.5:
            recommendations.append("Overall quality is low - review LLM prompts and validation thresholds")
        elif quality_score < 0.8:
            recommendations.append("Quality is moderate - consider fine-tuning processing parameters")

        return recommendations

    def get_quality_metrics(
        self, event_families: List[EventFamily], framed_narratives: List[FramedNarrative]
    ) -> Dict[str, Any]:
        """
        Calculate detailed quality metrics for Event Families and Framed Narratives
        
        Args:
            event_families: List of Event Families
            framed_narratives: List of Framed Narratives
            
        Returns:
            Dictionary with detailed quality metrics
        """
        metrics = {}

        if event_families:
            confidence_scores = [ef.confidence_score for ef in event_families]
            metrics["event_families"] = {
                "count": len(event_families),
                "avg_confidence": sum(confidence_scores) / len(confidence_scores),
                "min_confidence": min(confidence_scores),
                "max_confidence": max(confidence_scores),
                "avg_actors": sum(len(ef.key_actors) for ef in event_families) / len(event_families),
                "avg_source_titles": sum(len(ef.source_title_ids) for ef in event_families) / len(event_families),
            }

        if framed_narratives:
            prevalence_scores = [fn.prevalence_score for fn in framed_narratives]
            evidence_scores = [fn.evidence_quality for fn in framed_narratives]
            
            metrics["framed_narratives"] = {
                "count": len(framed_narratives),
                "avg_prevalence": sum(prevalence_scores) / len(prevalence_scores),
                "avg_evidence_quality": sum(evidence_scores) / len(evidence_scores),
                "avg_supporting_headlines": sum(len(fn.supporting_headlines) for fn in framed_narratives) / len(framed_narratives),
                "unique_frame_types": len(set(fn.frame_type for fn in framed_narratives)),
            }

        return metrics


# Global validator instance
_gen1_validator = None


def get_gen1_validator() -> Gen1Validator:
    """Get global GEN-1 validator instance"""
    global _gen1_validator
    if _gen1_validator is None:
        _gen1_validator = Gen1Validator()
    return _gen1_validator