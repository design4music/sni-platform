"""
MAP/REDUCE Data Models
Pydantic models for the new MAP/REDUCE Event Family processing approach
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class IncidentCluster(BaseModel):
    """Result of MAP phase: titles clustered by strategic incident"""

    incident_name: str = Field(
        description="Descriptive name for the strategic incident"
    )
    title_ids: List[str] = Field(description="List of title UUIDs in this incident")
    rationale: str = Field(description="Brief explanation of why these belong together")


class IncidentClustering(BaseModel):
    """Response from MAP phase: incident clusters for all titles"""

    clusters: List[IncidentCluster] = Field(
        description="List of incident clusters identified from titles"
    )


class IncidentAnalysis(BaseModel):
    """Response from REDUCE phase: complete Event Family for an incident"""

    primary_theater: str = Field(description="Primary theater for the whole incident")
    event_type: str = Field(description="Primary event type for the whole incident")
    ef_title: str = Field(description="Strategic Event Family title (≤120 chars)")
    ef_summary: str = Field(description="Brief strategic context (≤280 chars)")
    events: List[Dict[str, Any]] = Field(
        description="Timeline of discrete events within the incident",
        default_factory=list,
    )


# Legacy models - keeping for backward compatibility
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
    events: List[Dict[str, Any]] = Field(
        description="Events timeline array for EF seeds", default_factory=list
    )


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
