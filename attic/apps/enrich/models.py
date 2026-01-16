"""
EF Enrichment Data Models
Lean 6-field enrichment payload for strategic context
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CanonicalActor(BaseModel):
    """Canonical actor with role in the event"""

    name: str = Field(description="Official/canonical name")
    role: Literal["initiator", "target", "beneficiary", "mediator"] = Field(
        description="Role in the event"
    )


class Magnitude(BaseModel):
    """Quantified magnitude of the event"""

    value: Optional[float] = Field(description="Numeric value")
    unit: str = Field(description="Unit: GW|bcm|$bn|%|troops|casualties")
    what: str = Field(description="What is being measured")


class ComparableEvent(BaseModel):
    """Strategically relevant comparable event for decision-making context"""

    event_description: str = Field(description="Brief description of comparable event")
    timeframe: str = Field(description="When it occurred (e.g., '2014', 'Spring 2020')")
    similarity_reason: str = Field(
        description="Why this event is strategically comparable (actors, context, implications)"
    )


class EFContext(BaseModel):
    """Strategic context for Event Family - stored in ef_context JSONB field"""

    macro_link: Optional[str] = Field(
        default=None, description="Centroid ID this EF belongs to (e.g., 'ARC-UKR')"
    )

    comparables: List[ComparableEvent] = Field(
        default=[],
        max_items=3,
        description="Up to 3 strategically relevant precedents (1-2 decades, similar actors/context)",
    )

    abnormality: Optional[str] = Field(
        default=None, description="What makes this event unusual or significant"
    )


class EnrichmentPayload(BaseModel):
    """
    Objectivity-first enrichment payload for Event Families
    All fields optional to handle incomplete data gracefully
    """

    canonical_actors: List[CanonicalActor] = Field(
        default=[], description="Key actors with roles"
    )

    policy_status: Optional[
        Literal[
            "proposed",
            "passed",
            "signed",
            "in_force",
            "enforced",
            "suspended",
            "cancelled",
            "null",
        ]
    ] = Field(default=None, description="Policy/legal status if applicable")

    time_span: Dict[str, Optional[str]] = Field(
        default={"start": None, "end": None},
        description="Event timeframe (YYYY-MM-DD format)",
    )

    temporal_pattern: Optional[str] = Field(
        default=None, description="Factual frequency/timing of similar events"
    )

    magnitude_baseline: Optional[str] = Field(
        default=None, description="Scale vs historical norm in region/domain"
    )

    systemic_context: Optional[str] = Field(
        default=None, description="Broader documented trend this fits within"
    )

    magnitude: List[Magnitude] = Field(
        default=[], description="Quantified impact metrics"
    )

    official_sources: List[str] = Field(
        default=[], max_items=2, description="Official URLs (max 2)"
    )

    why_strategic: Optional[str] = Field(
        default=None, description="Objective strategic significance"
    )

    tags: List[str] = Field(
        default=[], max_items=3, description="3 tags: 2 thematic + 1 geographic"
    )

    ef_context: EFContext = Field(
        default_factory=EFContext,
        description="Strategic context: macro-link, comparables, abnormality",
    )


class EnrichmentRecord(BaseModel):
    """
    Complete enrichment record for database storage
    """

    ef_id: str = Field(description="Event Family UUID")
    enrichment_payload: EnrichmentPayload = Field(description="6-field enrichment data")

    # Metadata
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    enrichment_version: str = Field(default="v2.0")
    sources_found: int = Field(
        default=0, description="Number of official sources found"
    )
    tokens_used: int = Field(default=0, description="LLM tokens consumed")
    processing_time_ms: int = Field(
        default=0, description="Processing time in milliseconds"
    )

    # Status tracking
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        default="pending"
    )
    error_message: Optional[str] = Field(default=None)


class EnrichmentQueueItem(BaseModel):
    """Queue item for enrichment processing"""

    ef_id: str = Field(description="Event Family UUID")
    priority_score: float = Field(
        description="Processing priority (size + recency + keywords)"
    )
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    attempts: int = Field(default=0, description="Processing attempts")
    max_attempts: int = Field(default=3, description="Max retry attempts")
