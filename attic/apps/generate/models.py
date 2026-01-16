"""
GEN-1 Data Models
Event Family and Framed Narrative data structures
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Event(BaseModel):
    """
    Event: Strategic event as primary entity

    Represents an individual strategic event. Events can later be assembled into families
    rather than starting with families as the primary unit.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Neutral, descriptive title for the strategic event")
    summary: str = Field(
        description="Neutral, factual summary of the event"
    )
    strategic_purpose: Optional[str] = Field(
        default=None,
        description="One-sentence core narrative that serves as semantic anchor for thematic validation",
    )
    key_actors: List[str] = Field(description="Primary actors/entities involved")
    event_type: str = Field(
        description="Event type from standardized taxonomy (Strategy/Tactics, Diplomacy/Negotiations, etc.)"
    )
    primary_theater: Optional[str] = Field(
        default=None,
        description="Theater code from standardized list (UKRAINE, GAZA, EUROPE_SECURITY, etc.)",
    )

    # Event Key system for continuous merging
    ef_key: Optional[str] = Field(
        default=None,
        description="Deterministic key for event merging (16-char hash)",
    )
    status: str = Field(
        default="seed", description="Event status (seed/active/merged)"
    )
    merged_into: Optional[str] = Field(
        default=None, description="UUID of event this was merged into"
    )
    merge_rationale: Optional[str] = Field(
        default=None, description="Explanation of why this event was merged"
    )
    parent_ef_id: Optional[str] = Field(
        default=None,
        description="UUID of parent event if this was created by splitting. Siblings share same parent_ef_id and should not be merged together.",
    )

    # Source metadata
    source_title_ids: List[str] = Field(
        description="Title IDs that are part of this event"
    )

    # Quality indicators
    coherence_reason: str = Field(description="Why these titles form a coherent event")

    # Events timeline for event evolution
    events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Timeline of discrete sub-events within this event. Each: {summary, date, source_title_ids, event_id}",
    )

    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_notes: Optional[str] = Field(default=None)


# Backward compatibility alias
EventFamily = Event


class FramedNarrative(BaseModel):
    """
    Framed Narrative (FN): Stanceful rendering of an Event

    Shows how outlets frame/position the same event. Must cite headline evidence
    and state evaluative/causal framing clearly.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = Field(description="Reference to parent Event")

    # Core narrative content
    frame_type: str = Field(
        description="Type of framing (e.g., 'supportive', 'critical', 'neutral')"
    )
    frame_description: str = Field(description="How this narrative frames the event")
    stance_summary: str = Field(
        description="Clear statement of the evaluative/causal framing"
    )

    # Evidence and support
    supporting_headlines: List[str] = Field(
        description="Headlines that exemplify this framing"
    )
    supporting_title_ids: List[str] = Field(
        description="Title IDs that support this narrative"
    )
    key_language: List[str] = Field(
        description="Key words/phrases that signal this framing"
    )

    # Narrative strength
    prevalence_score: float = Field(
        ge=0.0, le=1.0, description="How dominant this framing is"
    )
    evidence_quality: float = Field(
        ge=0.0, le=1.0, description="Quality of supporting evidence"
    )

    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class ProcessingResult:
    """
    Result of GEN-1 processing operation
    """

    # Input context
    total_titles_processed: int

    # Output artifacts
    events: List[Event]
    framed_narratives: List[FramedNarrative]

    # Quality metrics
    success_rate: float
    processing_time_seconds: float

    # Errors and warnings
    errors: List[str]
    warnings: List[str]

    @property
    def summary(self) -> str:
        """Human-readable summary of processing results"""
        return (
            f"Processed {self.total_titles_processed} titles -> "
            f"{len(self.events)} Events, "
            f"{len(self.framed_narratives)} Framed Narratives"
        )


class LLMEventRequest(BaseModel):
    """
    Request structure for LLM Event assembly
    """

    # Direct title processing
    title_context: Optional[List[Dict[str, Any]]] = None

    processing_instructions: str
    max_events: int = 10


class LLMEventResponse(BaseModel):
    """
    Response structure from LLM Event assembly
    """

    events: List[Dict[str, Any]]
    processing_reasoning: str
    confidence: float
    warnings: List[str] = Field(default_factory=list)


class LLMFramedNarrativeRequest(BaseModel):
    """
    Request structure for LLM Framed Narrative generation
    """

    event: Event
    titles_context: List[Dict[str, Any]]
    framing_instructions: str
    max_narratives: int = 3


class LLMFramedNarrativeResponse(BaseModel):
    """
    Response structure from LLM Framed Narrative generation
    """

    framed_narratives: List[Dict[str, Any]]
    processing_reasoning: str
    confidence: float
    dominant_frames: List[str]
