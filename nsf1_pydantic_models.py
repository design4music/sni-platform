"""
NSF-1 Pydantic Models - Exact match to finalized JSON specification
These models replace the existing narrative models in strategic_narrative_api.py
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# NSF-1 CORE MODELS - EXACT MATCH TO SPECIFICATION
# ============================================================================


class NarrativeTensionItem(BaseModel):
    """Individual narrative tension entry"""

    type: str = Field(..., description="Type of tension (Internal, External, etc.)")
    description: str = Field(..., description="Description of the tension")


class TurningPointItem(BaseModel):
    """Individual turning point entry"""

    date: str = Field(..., description="Date of turning point (YYYY-MM-DD)")
    description: str = Field(..., description="Description of what changed")


class TopExcerptItem(BaseModel):
    """Individual top excerpt entry"""

    source: str = Field(..., description="Source name (e.g., 'Reuters')")
    language: str = Field(..., description="Language code (e.g., 'en')")
    original: str = Field(..., description="Original text excerpt")
    translated: Optional[str] = Field(None, description="Translated text if applicable")


class SourceStats(BaseModel):
    """Source statistics breakdown"""

    total_articles: int = Field(..., description="Total number of articles")
    sources: Dict[str, int] = Field(
        ..., description="Source name to article count mapping"
    )


class UpdateStatus(BaseModel):
    """Narrative update status information"""

    last_updated: str = Field(..., description="Last update date (YYYY-MM-DD)")
    update_trigger: str = Field(..., description="What triggered the update")


class VersionHistoryItem(BaseModel):
    """Individual version history entry"""

    version: str = Field(..., description="Version number (e.g., '1.0')")
    date: str = Field(..., description="Version date (YYYY-MM-DD)")
    change: str = Field(..., description="Description of changes made")


class RadicalShiftItem(BaseModel):
    """Individual radical shift entry"""

    date: str = Field(..., description="Date of shift (YYYY-MM-DD)")
    description: str = Field(..., description="Description of the shift")


class RAIAnalysis(BaseModel):
    """Responsible AI analysis object"""

    adequacy_score: float = Field(..., description="Score from 0.0 to 1.0")
    final_synthesis: str = Field(..., description="Overall synthesis text")
    key_conflicts: List[str] = Field(
        ..., description="List of key conflicts identified"
    )
    blind_spots: List[str] = Field(..., description="List of blind spots identified")
    radical_shifts: List[RadicalShiftItem] = Field(
        ..., description="List of radical shifts"
    )
    last_analyzed: str = Field(..., description="Last analysis date (YYYY-MM-DD)")


# ============================================================================
# MAIN NSF-1 NARRATIVE MODEL
# ============================================================================


class NarrativeNSF1Base(BaseModel):
    """
    NSF-1 Narrative Base Model - Exact match to specification
    Contains all fields from the finalized NSF-1 JSON schema
    """

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}, validate_assignment=True
    )

    # Display ID (used by API and frontend)
    narrative_id: str = Field(..., description="Display ID like 'EN-002-A'")

    # CORE NSF-1 FIELDS
    title: str = Field(..., max_length=500, description="Narrative title")
    summary: str = Field(..., description="Brief framing of narrative, 2-3 sentences")
    origin_language: str = Field(
        ..., min_length=2, max_length=2, description="Origin language code"
    )

    # ARRAY FIELDS
    dominant_source_languages: List[str] = Field(
        default_factory=list, description="Array of dominant source language codes"
    )
    alignment: List[str] = Field(
        default_factory=list,
        description="Array of alignment strings (e.g., ['Western governments', 'EU policy'])",
    )
    actor_origin: List[str] = Field(
        default_factory=list,
        description="Array of actor origins (e.g., ['EU Commission', 'U.S. energy agencies'])",
    )
    conflict_alignment: List[str] = Field(
        default_factory=list, description="Array of conflict alignments"
    )
    frame_logic: List[str] = Field(
        default_factory=list, description="Array of logical framework strings"
    )
    nested_within: Optional[List[str]] = Field(
        default_factory=list, description="Array of parent narrative IDs"
    )
    conflicts_with: Optional[List[str]] = Field(
        default_factory=list, description="Array of conflicting narrative IDs"
    )
    logical_strain: Optional[List[str]] = Field(
        default_factory=list, description="Array of logical strain descriptions"
    )

    # STRUCTURED OBJECT FIELDS
    narrative_tension: Optional[List[NarrativeTensionItem]] = Field(
        default_factory=list,
        description="Array of tension objects with type and description",
    )
    activity_timeline: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Object with date keys and event descriptions"
    )
    turning_points: Optional[List[TurningPointItem]] = Field(
        default_factory=list,
        description="Array of turning point objects with date and description",
    )
    media_spike_history: Optional[Dict[str, int]] = Field(
        default_factory=dict, description="Object with date keys and count values"
    )
    source_stats: Optional[SourceStats] = Field(
        None, description="Source statistics object"
    )
    top_excerpts: Optional[List[TopExcerptItem]] = Field(
        default_factory=list, description="Array of excerpt objects"
    )

    # UPDATE STATUS
    update_status: Optional[UpdateStatus] = Field(
        None, description="Update status object"
    )

    # QUALITY AND CONFIDENCE
    confidence_rating: Optional[str] = Field(
        None, description="Confidence rating: low, medium, high, very_high"
    )
    data_quality_notes: Optional[str] = Field(
        None, description="Notes about data quality"
    )

    # VERSION HISTORY
    version_history: Optional[List[VersionHistoryItem]] = Field(
        default_factory=list, description="Array of version history objects"
    )

    # RAI ANALYSIS
    rai_analysis: Optional[RAIAnalysis] = Field(
        None, description="Responsible AI analysis object"
    )


class NarrativeNSF1Create(NarrativeNSF1Base):
    """NSF-1 Narrative creation model (for POST requests)"""

    pass


class NarrativeNSF1Response(NarrativeNSF1Base):
    """
    NSF-1 Narrative response model (for GET requests)
    Includes both UUID (internal) and narrative_id (display)
    """

    # Internal UUID primary key (returned but frontend mainly uses narrative_id)
    id: UUID = Field(..., description="Internal UUID primary key")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Optional performance fields
    search_vector: Optional[str] = Field(None, description="Full-text search vector")
    narrative_embedding: Optional[List[float]] = Field(
        None, description="Semantic embedding vector"
    )


class NarrativeNSF1Update(BaseModel):
    """NSF-1 Narrative update model (for PATCH requests)"""

    title: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    dominant_source_languages: Optional[List[str]] = None
    alignment: Optional[List[str]] = None
    actor_origin: Optional[List[str]] = None
    conflict_alignment: Optional[List[str]] = None
    frame_logic: Optional[List[str]] = None
    narrative_tension: Optional[List[NarrativeTensionItem]] = None
    activity_timeline: Optional[Dict[str, str]] = None
    turning_points: Optional[List[TurningPointItem]] = None
    logical_strain: Optional[List[str]] = None
    media_spike_history: Optional[Dict[str, int]] = None
    source_stats: Optional[SourceStats] = None
    top_excerpts: Optional[List[TopExcerptItem]] = None
    update_status: Optional[UpdateStatus] = None
    confidence_rating: Optional[str] = None
    data_quality_notes: Optional[str] = None
    rai_analysis: Optional[RAIAnalysis] = None


class NarrativeNSF1Summary(BaseModel):
    """NSF-1 Narrative summary model (for list views)"""

    id: UUID = Field(..., description="Internal UUID primary key")
    narrative_id: str = Field(..., description="Display ID like 'EN-002-A'")
    title: str = Field(..., description="Narrative title")
    summary: str = Field(..., description="Brief summary")
    origin_language: str = Field(..., description="Origin language code")
    alignment: List[str] = Field(..., description="Alignment array")
    confidence_rating: Optional[str] = Field(None, description="Confidence rating")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Computed fields for UI
    total_articles: Optional[int] = Field(
        None, description="Total article count from source_stats"
    )
    last_activity: Optional[str] = Field(
        None, description="Last activity date from update_status"
    )


# ============================================================================
# HELPER MODELS FOR API OPERATIONS
# ============================================================================


class NarrativeSearchFilters(BaseModel):
    """Search filters for NSF-1 narratives"""

    origin_language: Optional[str] = None
    alignment: Optional[List[str]] = None
    actor_origin: Optional[List[str]] = None
    confidence_rating: Optional[str] = None
    has_conflicts: Optional[bool] = None
    has_rai_analysis: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class NarrativeConflictMap(BaseModel):
    """Model for narrative conflict relationships"""

    narrative_id: str = Field(..., description="Source narrative ID")
    conflicts_with: List[str] = Field(
        ..., description="List of conflicting narrative IDs"
    )
    conflict_details: Optional[Dict[str, Any]] = Field(
        None, description="Additional conflict details"
    )


class NarrativeHierarchy(BaseModel):
    """Model for narrative hierarchy (nested_within relationships)"""

    narrative_id: str = Field(..., description="Child narrative ID")
    parent_narratives: List[str] = Field(
        ..., description="List of parent narrative IDs"
    )
    hierarchy_level: Optional[int] = Field(None, description="Nesting level")


# ============================================================================
# COMBINED API CONTRACT MODELS (NSF-1 + METRICS)
# ============================================================================


class NarrativeMetricsData(BaseModel):
    """Metrics data from narrative_metrics table"""

    trending_score: float = Field(0.0, ge=0, description="Current trending intensity")
    credibility_score: Optional[float] = Field(
        None, ge=0, le=10, description="Source credibility rating"
    )
    engagement_score: Optional[float] = Field(
        None, ge=0, le=1, description="User engagement level"
    )
    sentiment_score: Optional[float] = Field(
        None, ge=-1, le=1, description="Overall sentiment"
    )
    narrative_priority: int = Field(
        5, ge=1, le=10, description="Priority ranking (1=highest)"
    )
    narrative_status: str = Field("active", description="Current status")
    geographic_scope: Optional[str] = Field(None, description="Geographic focus")
    keywords: List[str] = Field(default_factory=list, description="Core keywords")
    narrative_start_date: Optional[datetime] = Field(
        None, description="Narrative start date"
    )
    narrative_end_date: Optional[datetime] = Field(
        None, description="Narrative end date"
    )
    last_spike: Optional[datetime] = Field(None, description="Last activity spike")


class ComputedMetrics(BaseModel):
    """Real-time computed metrics"""

    recent_activity_score: float = Field(0.0, description="Activity in last 7 days")
    source_diversity: float = Field(0.0, description="Source variety ratio")
    article_count_7d: int = Field(0, description="Articles in last 7 days")
    composite_score: float = Field(0.0, description="Weighted composite ranking")


class NarrativeDetailResponse(NarrativeNSF1Base):
    """Combined narrative detail response: NSF-1 + Metrics + Computed

    This is the primary API contract model that combines:
    - NSF-1 content fields (inherited from NarrativeNSF1Base)
    - Metrics fields (from narrative_metrics table)
    - Real-time computed fields
    """

    # Core identifiers
    id: UUID = Field(..., description="Internal UUID")
    narrative_id: str = Field(..., description="Display ID (e.g., EN-002-A)")

    # Embed metrics directly in response
    trending_score: float = Field(0.0, ge=0, description="Current trending intensity")
    credibility_score: Optional[float] = Field(
        None, ge=0, le=10, description="Source credibility rating"
    )
    engagement_score: Optional[float] = Field(
        None, ge=0, le=1, description="User engagement level"
    )
    sentiment_score: Optional[float] = Field(
        None, ge=-1, le=1, description="Overall sentiment"
    )
    narrative_priority: int = Field(
        5, ge=1, le=10, description="Priority ranking (1=highest)"
    )
    narrative_status: str = Field("active", description="Current status")
    geographic_scope: Optional[str] = Field(None, description="Geographic focus")
    keywords: List[str] = Field(default_factory=list, description="Core keywords")
    narrative_start_date: Optional[datetime] = Field(
        None, description="Narrative start date"
    )
    narrative_end_date: Optional[datetime] = Field(
        None, description="Narrative end date"
    )
    last_spike: Optional[datetime] = Field(None, description="Last activity spike")

    # Computed fields (calculated in real-time)
    recent_activity_score: float = Field(0.0, description="Activity in last 7 days")
    source_diversity: float = Field(0.0, description="Source variety ratio")
    article_count_7d: int = Field(0, description="Articles in last 7 days")
    composite_score: float = Field(0.0, description="Weighted composite ranking")

    # Metadata
    created_at: datetime = Field(..., description="Narrative creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class NarrativeListItem(BaseModel):
    """Lightweight narrative model for dashboard/list views"""

    id: UUID = Field(..., description="Internal UUID")
    narrative_id: str = Field(..., description="Display ID (e.g., EN-002-A)")
    title: str = Field(..., description="Narrative title")
    summary: str = Field(..., description="Brief narrative summary")
    trending_score: float = Field(0.0, ge=0, description="Current trending intensity")
    credibility_score: Optional[float] = Field(
        None, ge=0, le=10, description="Source credibility rating"
    )
    narrative_status: str = Field("active", description="Current status")
    geographic_scope: Optional[str] = Field(None, description="Geographic focus")
    keywords: List[str] = Field(default_factory=list, description="Core keywords")
    updated_at: datetime = Field(..., description="Last update timestamp")
    composite_score: float = Field(0.0, description="Weighted composite ranking")

    model_config = ConfigDict(from_attributes=True)


class NarrativeListResponse(BaseModel):
    """Paginated list response for dashboard queries"""

    narratives: List[NarrativeListItem] = Field(..., description="List of narratives")
    total: int = Field(..., description="Total number of narratives")
    page: int = Field(1, description="Current page number")
    pages: int = Field(1, description="Total number of pages")
    limit: int = Field(50, description="Items per page")


# ============================================================================
# EXAMPLE USAGE FOR COMBINED API CONTRACT
# ============================================================================

"""
# FastAPI endpoint using combined response model
@router.get("/narratives/{narrative_id}", response_model=NarrativeDetailResponse)
async def get_narrative_detail(
    narrative_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Single optimized query with all joins
    result = await db.execute(
        select(Narrative, NarrativeMetrics)
        .join(NarrativeMetrics)
        .where(Narrative.narrative_id == narrative_id)
    )
    
    narrative, metrics = result.one_or_none()
    if not narrative:
        raise HTTPException(404, "Narrative not found")
    
    # Compute real-time metrics
    computed = await compute_realtime_metrics(narrative.id, db)
    
    # Combine all data into response model
    return NarrativeDetailResponse(
        **narrative.__dict__,
        **metrics.__dict__,  
        **computed
    )

# Dashboard list endpoint
@router.get("/narratives", response_model=NarrativeListResponse)
async def list_narratives(
    status: str = "active",
    limit: int = 50,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    # Optimized query for list view
    query = (
        select(Narrative, NarrativeMetrics)
        .join(NarrativeMetrics)
        .where(NarrativeMetrics.narrative_status == status)
        .order_by(NarrativeMetrics.trending_score.desc())
        .limit(limit)
        .offset((page - 1) * limit)
    )
    
    results = await db.execute(query)
    narratives = []
    
    for narrative, metrics in results:
        narratives.append(NarrativeListItem(
            **narrative.__dict__,
            trending_score=metrics.trending_score,
            credibility_score=metrics.credibility_score,
            narrative_status=metrics.narrative_status,
            geographic_scope=metrics.geographic_scope,
            keywords=metrics.keywords,
            composite_score=calculate_composite_score(metrics)
        ))
    
    # Get total count
    total_query = select(func.count()).select_from(
        Narrative.__table__.join(NarrativeMetrics.__table__)
    ).where(NarrativeMetrics.narrative_status == status)
    
    total = await db.scalar(total_query)
    
    return NarrativeListResponse(
        narratives=narratives,
        total=total,
        page=page,
        pages=math.ceil(total / limit),
        limit=limit
    )
"""


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_confidence_rating(value: str) -> str:
    """Validate confidence rating values"""
    allowed = {"low", "medium", "high", "very_high"}
    if value and value not in allowed:
        raise ValueError(f"confidence_rating must be one of: {allowed}")
    return value


def validate_language_code(value: str) -> str:
    """Validate language code format (2 characters)"""
    if len(value) != 2:
        raise ValueError("Language code must be exactly 2 characters")
    return value.lower()


def validate_narrative_id_format(value: str) -> str:
    """Validate narrative_id format (e.g., EN-002-A)"""
    if not value or len(value) < 3:
        raise ValueError("narrative_id must be at least 3 characters")
    return value


# Apply validators to models
NarrativeNSF1Base.model_validate = lambda cls, v: cls(
    **{
        **v,
        "confidence_rating": (
            validate_confidence_rating(v.get("confidence_rating"))
            if v.get("confidence_rating")
            else None
        ),
        "origin_language": validate_language_code(v["origin_language"]),
        "narrative_id": validate_narrative_id_format(v["narrative_id"]),
    }
)
