"""
MAP/REDUCE Data Models
Pydantic models for the new MAP/REDUCE Event Family processing approach
"""

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class TitleClassification(BaseModel):
    """Result of MAP phase: title classified into theater + event_type"""

    id: str = Field(description="Title UUID")
    primary_theater: str = Field(description="Theater code (UKRAINE, GAZA, etc.)")
    event_type: str = Field(
        description="Event type (Strategy/Tactics, Diplomacy/Negotiations, etc.)"
    )


class MapRequest(BaseModel):
    """Request for MAP phase: batch of titles to classify"""

    titles: List[Dict[str, str]] = Field(
        description="List of title dicts with 'id' and 'title' keys"
    )


class MapResponse(BaseModel):
    """Response from MAP phase: classifications for all titles"""

    classifications: List[TitleClassification] = Field(
        description="One classification per input title"
    )


class EFGroup(BaseModel):
    """Grouped titles by (theater, event_type) for REDUCE phase"""

    primary_theater: str = Field(description="Theater code")
    event_type: str = Field(description="Event type")
    title_ids: List[str] = Field(description="Title UUIDs in this group")
    titles: List[Dict[str, str]] = Field(
        description="Title data (id, title, pubdate_utc)"
    )
    key_actors: List[str] = Field(
        description="Combined key actors from all titles in group", default_factory=list
    )
    temporal_scope_start: datetime = Field(
        description="Earliest publication date in group"
    )
    temporal_scope_end: datetime = Field(description="Latest publication date in group")


class ReduceRequest(BaseModel):
    """Request for REDUCE phase: EF context + sample titles"""

    ef_context: Dict[str, str] = Field(
        description="EF context with primary_theater and event_type"
    )
    titles: List[Dict[str, str]] = Field(
        description="Up to 12 representative titles from the group"
    )


class ReduceResponse(BaseModel):
    """Response from REDUCE phase: generated EF content"""

    ef_title: str = Field(description="Generated Event Family title (≤120 chars)")
    ef_summary: str = Field(description="Generated Event Family summary (≤280 chars)")


class MapReduceResult(BaseModel):
    """Final result of MAP/REDUCE processing"""

    # Input context
    total_titles_processed: int
    map_batches_processed: int
    ef_groups_created: int

    # Processing times
    map_phase_seconds: float
    group_phase_seconds: float
    reduce_phase_seconds: float
    total_seconds: float

    # Results
    event_families_created: int
    event_families_merged: int
    titles_assigned: int

    # Quality metrics
    classification_success_rate: float
    reduce_success_rate: float

    # Errors
    map_errors: List[str] = Field(default_factory=list)
    reduce_errors: List[str] = Field(default_factory=list)

    @property
    def summary(self) -> str:
        """Human-readable summary of MAP/REDUCE results"""
        return (
            f"MAP/REDUCE: {self.total_titles_processed} titles -> "
            f"{self.event_families_created} EFs created, "
            f"{self.event_families_merged} merged "
            f"({self.total_seconds:.1f}s total)"
        )
