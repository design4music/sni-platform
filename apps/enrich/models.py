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
    what: str = Field(description="What is being measured", max_length=50)


class EnrichmentPayload(BaseModel):
    """
    Lean 6-field enrichment payload for Event Families
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

    magnitude: List[Magnitude] = Field(
        default=[], description="Quantified impact metrics"
    )

    official_sources: List[str] = Field(
        default=[], max_items=2, description="Official URLs (max 2)"
    )

    why_strategic: Optional[str] = Field(
        default=None, max_length=150, description="Strategic significance (≤150 chars)"
    )


class EnrichmentRecord(BaseModel):
    """
    Complete enrichment record for database storage
    """

    ef_id: str = Field(description="Event Family UUID")
    enrichment_payload: EnrichmentPayload = Field(description="6-field enrichment data")

    # Metadata
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    enrichment_version: str = Field(default="v1.0")
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
