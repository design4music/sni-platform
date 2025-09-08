# API Contract v1.0 - Combined Narrative Response

## 🎯 Contract Overview

**Version**: 1.0  
**Date**: 2025-08-01  
**Schema Compatibility**: NSF-1 v1.1 + Metrics v1.0  
**Status**: 🔒 **LOCKED FOR DEVELOPMENT**

This contract defines the **combined response model** that merges NSF-1 narrative content with operational metrics, providing a single comprehensive API interface.

---

## 📊 Combined Narrative Detail Response

### GET `/api/v1/narratives/{narrative_id}`

**Response Structure**: NSF-1 Content + Metrics + Computed Fields

```json
{
  // ========================================
  // INTERNAL IDENTIFIERS
  // ========================================
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "narrative_id": "EN-002-A",
  
  // ========================================
  // NSF-1 CORE CONTENT FIELDS
  // ========================================
  "title": "Energy Independence as Security Strategy",
  "summary": "Brief framing of narrative, 2-3 sentences.",
  "origin_language": "en",
  "dominant_source_languages": ["en", "de", "fr"],
  
  // NSF-1 Arrays
  "alignment": ["Western governments", "EU policy"],
  "actor_origin": ["EU Commission", "U.S. energy agencies"],
  "conflict_alignment": ["Europe vs Supplier Dependence"],
  "frame_logic": [
    "Reducing import reliance increases security",
    "Green transition framed as sovereignty defense"
  ],
  "nested_within": ["EN-CORE-001"],
  "conflicts_with": ["EN-004"],
  "logical_strain": [
    "Claim of independence vs rising LNG imports",
    "Security framing vs energy cost protests"
  ],
  
  // NSF-1 Structured Objects
  "narrative_tension": [
    {
      "type": "Internal",
      "description": "Green goals vs temporary fossil fuel expansion"
    },
    {
      "type": "External", 
      "description": "Critics argue U.S. LNG dependence contradicts autonomy narrative"
    }
  ],
  "activity_timeline": {
    "2025-Q3": "Narrative spike after EU energy summit"
  },
  "turning_points": [
    {
      "date": "2025-07-15",
      "description": "Framing shift: renewables as autonomy"
    }
  ],
  "media_spike_history": {
    "2025-07": 42
  },
  "source_stats": {
    "total_articles": 42,
    "sources": {
      "Reuters": 14,
      "Politico EU": 10,
      "Tagesschau": 7,
      "Bloomberg": 6,
      "Le Monde": 5
    }
  },
  "top_excerpts": [
    {
      "source": "Politico EU",
      "language": "en",
      "original": "Energy policy is now defense policy — Europe must act accordingly.",
      "translated": null
    }
  ],
  "update_status": {
    "last_updated": "2025-07-22",
    "update_trigger": "EU summit announcement and media spike"
  },
  "confidence_rating": "high",
  "data_quality_notes": "Based on 42 articles from 5 sources; alignment consistent.",
  "version_history": [
    {
      "version": "1.0",
      "date": "2025-07-22", 
      "change": "Initial narrative entry created"
    }
  ],
  "rai_analysis": {
    "adequacy_score": 0.74,
    "final_synthesis": "Overall, the narrative presents a coherent framing...",
    "key_conflicts": [
      "Narrative claims victory yet reports rising energy imports"
    ],
    "blind_spots": [
      "No acknowledgment of rare earth dependency in independence framing"
    ],
    "radical_shifts": [
      {
        "date": "2025-08-01",
        "description": "Pivot from renewables as climate policy to renewables as defense policy"
      }
    ],
    "last_analyzed": "2025-08-01"
  },
  
  // ========================================
  // METRICS & ANALYTICS FIELDS
  // ========================================
  "trending_score": 8.5,
  "credibility_score": 7.2,
  "engagement_score": 0.74,
  "sentiment_score": 0.15,
  "narrative_priority": 2,
  "narrative_status": "active",
  "geographic_scope": "europe",
  "keywords": ["energy", "independence", "security", "EU", "renewables", "autonomy"],
  
  // Temporal Fields
  "narrative_start_date": "2025-07-01T00:00:00Z", 
  "narrative_end_date": null,
  "last_spike": "2025-07-22T14:30:00Z",
  
  // ========================================
  // COMPUTED FIELDS (REAL-TIME)
  // ========================================
  "recent_activity_score": 15.2,
  "source_diversity": 0.85,
  "article_count_7d": 8,
  "composite_score": 7.89,
  
  // ========================================
  // METADATA
  // ========================================
  "created_at": "2025-07-01T10:00:00Z",
  "updated_at": "2025-07-22T14:30:00Z"
}
```

---

## 🔧 Response Model Implementation

### Pydantic Model Extension

```python
# Add to nsf1_pydantic_models.py

class NarrativeMetricsData(BaseModel):
    """Metrics data from narrative_metrics table"""
    trending_score: float = Field(0.0, ge=0, description="Current trending intensity")
    credibility_score: Optional[float] = Field(None, ge=0, le=10, description="Source credibility rating")
    engagement_score: Optional[float] = Field(None, ge=0, le=1, description="User engagement level")
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Overall sentiment")
    narrative_priority: int = Field(5, ge=1, le=10, description="Priority ranking (1=highest)")
    narrative_status: str = Field("active", description="Current status")
    geographic_scope: Optional[str] = Field(None, description="Geographic focus")
    keywords: List[str] = Field(default_factory=list, description="Core keywords")
    narrative_start_date: Optional[datetime] = Field(None, description="Narrative start date")
    narrative_end_date: Optional[datetime] = Field(None, description="Narrative end date") 
    last_spike: Optional[datetime] = Field(None, description="Last activity spike")

class ComputedMetrics(BaseModel):
    """Real-time computed metrics"""
    recent_activity_score: float = Field(0.0, description="Activity in last 7 days")
    source_diversity: float = Field(0.0, description="Source variety ratio")
    article_count_7d: int = Field(0, description="Articles in last 7 days")
    composite_score: float = Field(0.0, description="Weighted composite ranking")

class NarrativeDetailResponse(NarrativeNSF1Base):
    """Combined narrative detail response: NSF-1 + Metrics + Computed"""
    
    # Core identifiers 
    id: UUID = Field(..., description="Internal UUID")
    narrative_id: str = Field(..., description="Display ID (e.g., EN-002-A)")
    
    # Embed metrics directly in response
    trending_score: float = Field(0.0, ge=0)
    credibility_score: Optional[float] = Field(None, ge=0, le=10)
    engagement_score: Optional[float] = Field(None, ge=0, le=1) 
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    narrative_priority: int = Field(5, ge=1, le=10)
    narrative_status: str = Field("active")
    geographic_scope: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    narrative_start_date: Optional[datetime] = None
    narrative_end_date: Optional[datetime] = None
    last_spike: Optional[datetime] = None
    
    # Computed fields
    recent_activity_score: float = Field(0.0)
    source_diversity: float = Field(0.0) 
    article_count_7d: int = Field(0)
    composite_score: float = Field(0.0)
    
    # Metadata
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## 🔍 Dashboard List Response

### GET `/api/v1/narratives?status=active&limit=50`

**Lightweight response for dashboard/list views:**

```json
{
  "narratives": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "narrative_id": "EN-002-A", 
      "title": "Energy Independence as Security Strategy",
      "summary": "Brief framing of narrative, 2-3 sentences.",
      "trending_score": 8.5,
      "credibility_score": 7.2,
      "narrative_status": "active",
      "geographic_scope": "europe",
      "keywords": ["energy", "independence", "security"],
      "updated_at": "2025-07-22T14:30:00Z",
      "composite_score": 7.89
    }
  ],
  "total": 247,
  "page": 1,
  "pages": 5
}
```

---

## 🚀 Implementation Strategy

### Database Query Pattern
```sql
-- Single query for combined response
SELECT 
    -- NSF-1 fields from narratives
    n.id, n.narrative_id, n.title, n.summary, n.alignment, n.rai_analysis,
    -- Metrics fields from narrative_metrics  
    m.trending_score, m.credibility_score, m.narrative_status, m.keywords,
    -- Computed fields
    COALESCE(articles.count_7d, 0) as article_count_7d,
    COALESCE(sources.diversity, 0) as source_diversity
FROM narratives n
JOIN narrative_metrics m ON n.id = m.narrative_uuid
LEFT JOIN (
    SELECT narrative_id, COUNT(*) as count_7d
    FROM narrative_articles na
    JOIN raw_articles ra ON na.article_id = ra.article_id  
    WHERE ra.published_at >= NOW() - INTERVAL '7 days'
    GROUP BY narrative_id
) articles ON n.id = articles.narrative_id
LEFT JOIN (
    SELECT narrative_id, COUNT(DISTINCT ra.source_id)::float / COUNT(*)::float as diversity
    FROM narrative_articles na
    JOIN raw_articles ra ON na.article_id = ra.article_id
    GROUP BY narrative_id
) sources ON n.id = sources.narrative_id
WHERE n.narrative_id = $1;
```

### FastAPI Endpoint Implementation
```python
@router.get("/narratives/{narrative_id}", response_model=NarrativeDetailResponse)
async def get_narrative_detail(
    narrative_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get complete narrative with NSF-1 content + metrics + computed fields"""
    
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
```

---

## ✅ Contract Validation Checklist

- [x] **NSF-1 Compliance**: All specification fields included
- [x] **Metrics Integration**: Analytics fields properly merged
- [x] **Performance**: Single query for complete response
- [x] **Backward Compatibility**: UUID + narrative_id dual access
- [x] **Real-time Computed**: Activity scores and composite metrics
- [ ] **Integration Tests**: End-to-end API validation
- [ ] **Frontend Contract**: React component integration
- [ ] **Performance Benchmarks**: Response time targets

---

## 🎯 Next Phase: ETL Pipeline Integration

With API contract locked, ETL pipeline can now target:
1. **Narrative Generation**: Populate NSF-1 content fields
2. **Metrics Calculation**: Generate trending_score, credibility_score  
3. **Real-time Updates**: Maintain computed fields via triggers
4. **Dashboard Optimization**: Materialized views for list responses

**Contract Lock Authority**: Development Team  
**Ready for**: ETL Pipeline Development 🚀