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


class EventFamily(BaseModel):
    """
    Event Family (EF): Coherent real-world news happening/episode

    An Event Family represents a single real-world news happening that may be
    covered across multiple headlines/outlets. It focuses on the concrete event
    with specific actors, time, and optionally geography.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Clear, descriptive title for the event family")
    summary: str = Field(description="Factual summary of what happened")
    key_actors: List[str] = Field(description="Primary actors/entities involved")
    event_type: str = Field(
        description="Type of event (e.g., 'diplomatic meeting', 'economic policy')"
    )
    geography: Optional[str] = Field(
        default=None, description="Geographic location if relevant"
    )

    # Time boundaries
    event_start: datetime = Field(description="When the event began")
    event_end: Optional[datetime] = Field(
        default=None, description="When the event concluded (if applicable)"
    )

    # Source metadata
    source_bucket_ids: List[str] = Field(
        description="CLUST-2 bucket IDs that contributed to this EF"
    )
    source_title_ids: List[str] = Field(
        description="Title IDs that are part of this event family"
    )

    # Quality indicators
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="LLM confidence in event coherence"
    )
    coherence_reason: str = Field(description="Why these titles form a coherent event")

    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_notes: Optional[str] = Field(default=None)


class FramedNarrative(BaseModel):
    """
    Framed Narrative (FN): Stanceful rendering of an Event Family

    Shows how outlets frame/position the same event. Must cite headline evidence
    and state evaluative/causal framing clearly.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_family_id: str = Field(description="Reference to parent Event Family")

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


class BucketContext(BaseModel):
    """
    Context information about CLUST-2 buckets for GEN-1 processing
    """

    bucket_id: str
    bucket_key: str  # Actor set key like "CN-US"
    actor_codes: List[str]
    title_count: int
    time_span_hours: float
    time_window_start: datetime
    time_window_end: datetime

    # Titles within this bucket
    titles: List[Dict[str, Any]] = Field(default_factory=list)


@dataclass
class ProcessingResult:
    """
    Result of GEN-1 processing operation
    """

    # Input context
    processed_buckets: List[str]
    total_titles_processed: int

    # Output artifacts
    event_families: List[EventFamily]
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
            f"Processed {len(self.processed_buckets)} buckets, "
            f"{self.total_titles_processed} titles -> "
            f"{len(self.event_families)} Event Families, "
            f"{len(self.framed_narratives)} Framed Narratives"
        )


class LLMEventFamilyRequest(BaseModel):
    """
    Request structure for LLM Event Family assembly
    """

    # Legacy bucket-based processing
    buckets: Optional[List[BucketContext]] = None
    cross_bucket_context: Optional[Dict[str, Any]] = None

    # Phase 2: Direct title processing
    title_context: Optional[List[Dict[str, Any]]] = None

    processing_instructions: str
    max_event_families: int = 10


class LLMEventFamilyResponse(BaseModel):
    """
    Response structure from LLM Event Family assembly
    """

    event_families: List[Dict[str, Any]]
    processing_reasoning: str
    confidence: float
    warnings: List[str] = Field(default_factory=list)


class LLMFramedNarrativeRequest(BaseModel):
    """
    Request structure for LLM Framed Narrative generation
    """

    event_family: EventFamily
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
