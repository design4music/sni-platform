"""
Strategic Narrative Intelligence Platform - FastAPI REST API
Complete API specification with all endpoints, models, and configurations
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import redis.asyncio as redis
from cachetools import TTLCache
# Import centralized config
from etl_pipeline.core.config import get_config
from fastapi import (BackgroundTasks, Body, Depends, FastAPI, HTTPException,
                     Path, Query, WebSocket, WebSocketDisconnect, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# ============================================================================
# CONFIGURATION AND SETUP
# ============================================================================


# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Cache setup (in-memory for demo, use Redis in production)
cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute TTL

# Redis connection (for real-time updates and caching)
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client
    config = get_config()
    redis_client = redis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        password=config.redis.password,
        decode_responses=True,
    )
    yield
    # Shutdown
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Strategic Narrative Intelligence API",
    description="Comprehensive API for narrative analysis, clustering, and real-time intelligence",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization",
        },
        {"name": "narratives", "description": "Narrative objects and analysis"},
        {"name": "articles", "description": "Source articles and content"},
        {"name": "clustering", "description": "Narrative clustering and embeddings"},
        {"name": "analytics", "description": "Temporal analytics and trending data"},
        {"name": "search", "description": "Search and filtering operations"},
        {"name": "real-time", "description": "WebSocket connections for live updates"},
        {
            "name": "pipeline",
            "description": "Background processing and pipeline triggers",
        },
        {"name": "admin", "description": "Administrative operations"},
    ],
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# Add middleware
config = get_config()
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.allowed_origins,
    allow_credentials=True,
    allow_methods=config.api.allowed_methods,
    allow_headers=["*"],
)

# Configure trusted hosts based on environment
trusted_hosts = ["localhost", "127.0.0.1"]
if config.environment.value == "production":
    # In production, use configured allowed origins as trusted hosts
    for origin in config.api.allowed_origins:
        if origin != "*":
            # Remove protocol from origin to get hostname
            hostname = (
                origin.replace("http://", "").replace("https://", "").split("/")[0]
            )
            if hostname not in trusted_hosts:
                trusted_hosts.append(hostname)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================


class AlignmentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class NarrativeStatus(str, Enum):
    ACTIVE = "active"
    EMERGING = "emerging"
    DECLINING = "declining"
    DORMANT = "dormant"


class TrendingPeriod(str, Enum):
    HOUR = "1h"
    SIX_HOURS = "6h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"


class SourceType(str, Enum):
    NEWS = "news"
    SOCIAL = "social"
    BLOG = "blog"
    ACADEMIC = "academic"
    GOVERNMENT = "government"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


# ============================================================================
# PYDANTIC MODELS - REQUEST/RESPONSE SCHEMAS
# ============================================================================


# Base Models
class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# Authentication Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase, TimestampMixin):
    id: UUID
    is_active: bool = True
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str


class LoginRequest(BaseModel):
    username: str
    password: str


# Article Models
class SourceInfo(BaseModel):
    name: str
    type: SourceType
    url: str
    credibility_score: float = Field(..., ge=0.0, le=1.0)
    bias_score: float = Field(..., ge=-1.0, le=1.0)


class ArticleBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    url: str = Field(..., regex=r"^https?://")
    author: Optional[str] = None
    published_at: datetime
    source: SourceInfo
    language: str = Field(default="en", max_length=5)
    tags: List[str] = Field(default_factory=list)


class ArticleCreate(ArticleBase):
    pass


class ArticleResponse(ArticleBase, TimestampMixin):
    id: UUID
    embedding_vector: Optional[List[float]] = None
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    narrative_ids: List[UUID] = Field(default_factory=list)


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


# Narrative Models
class TurningPoint(BaseModel):
    timestamp: datetime
    event_description: str
    impact_score: float = Field(..., ge=0.0, le=1.0)
    supporting_articles: List[UUID]


class NarrativeTension(BaseModel):
    opposing_narrative_id: UUID
    tension_score: float = Field(..., ge=0.0, le=1.0)
    key_differences: List[str]
    timeline_overlap: Dict[str, Any]


class SourceExcerpt(BaseModel):
    article_id: UUID
    excerpt: str = Field(..., max_length=1000)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime


class NarrativeBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    topic: str = Field(..., max_length=100)
    alignment: AlignmentType
    status: NarrativeStatus
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    impact_score: float = Field(..., ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)


class NarrativeCreate(NarrativeBase):
    pass


class NarrativeResponse(NarrativeBase, TimestampMixin):
    id: UUID
    timeline: List[TurningPoint]
    source_excerpts: List[SourceExcerpt]
    tensions: List[NarrativeTension]
    cluster_id: Optional[UUID] = None
    embedding_vector: Optional[List[float]] = None
    article_count: int = 0
    trend_momentum: float = Field(..., ge=-1.0, le=1.0)
    last_activity: datetime


class NarrativeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[NarrativeStatus] = None
    tags: Optional[List[str]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class NarrativeSummary(BaseModel):
    id: UUID
    title: str
    topic: str
    alignment: AlignmentType
    status: NarrativeStatus
    confidence_score: float
    impact_score: float
    article_count: int
    trend_momentum: float
    last_activity: datetime


# Clustering Models
class ClusterBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    centroid_vector: List[float]
    coherence_score: float = Field(..., ge=0.0, le=1.0)
    size: int = Field(..., ge=1)


class ClusterResponse(ClusterBase, TimestampMixin):
    id: UUID
    narrative_ids: List[UUID]
    representative_articles: List[UUID]
    topic_keywords: List[str]
    temporal_distribution: Dict[str, int]


# Analytics Models
class TrendingMetrics(BaseModel):
    narrative_id: UUID
    period: TrendingPeriod
    growth_rate: float
    velocity: float
    acceleration: float
    volume: int
    engagement_score: float = Field(..., ge=0.0, le=1.0)


class TemporalAnalytics(BaseModel):
    narrative_id: UUID
    time_series: Dict[str, float]  # timestamp -> metric value
    trend_direction: str = Field(..., regex=r"^(up|down|stable)$")
    seasonality_detected: bool
    anomalies: List[datetime]
    forecast_7d: List[float]


class GlobalMetrics(BaseModel):
    total_narratives: int
    active_narratives: int
    total_articles: int
    articles_last_24h: int
    top_topics: List[Dict[str, Union[str, int]]]
    sentiment_distribution: Dict[AlignmentType, int]
    processing_lag_minutes: float


# Search Models
class SearchFilters(BaseModel):
    topics: Optional[List[str]] = None
    alignments: Optional[List[AlignmentType]] = None
    statuses: Optional[List[NarrativeStatus]] = None
    source_types: Optional[List[SourceType]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_impact: Optional[float] = Field(None, ge=0.0, le=1.0)
    trending_period: Optional[TrendingPeriod] = None


class SearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Optional[SearchFilters] = None
    sort_by: str = Field(
        default="relevance", regex=r"^(relevance|date|impact|confidence|trending)$"
    )
    sort_order: str = Field(default="desc", regex=r"^(asc|desc)$")


class SearchResponse(BaseModel):
    narratives: List[NarrativeSummary]
    total: int
    query_time_ms: float
    suggestions: List[str]
    facets: Dict[str, Dict[str, int]]


# Pipeline Models
class PipelineTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: str = Field(..., regex=r"^(ingest|cluster|analyze|rai_analysis)$")
    status: TaskStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[int] = None


class PipelineTaskCreate(BaseModel):
    type: str = Field(..., regex=r"^(ingest|cluster|analyze|rai_analysis)$")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


# Real-time Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SubscriptionRequest(BaseModel):
    channels: List[str] = Field(..., min_items=1)
    filters: Optional[Dict[str, Any]] = None


# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    invalid_value: Any


class ValidationErrorResponse(ErrorResponse):
    validation_errors: List[ValidationErrorDetail]


# ============================================================================
# AUTHENTICATION AND AUTHORIZATION
# ============================================================================

security = HTTPBearer()

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )


def require_role(required_role: UserRole):
    def role_checker(token_data: dict = Depends(verify_token)):
        user_role = UserRole(token_data.get("role", "viewer"))
        role_hierarchy = {UserRole.VIEWER: 1, UserRole.ANALYST: 2, UserRole.ADMIN: 3}

        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 999):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token_data

    return role_checker


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail,
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message=str(exc),
            request_id=getattr(request.state, "request_id", None),
        ).dict(),
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================


# Authentication Endpoints
@app.post(
    "/api/v1/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
@limiter.limit("5/minute")
async def register_user(request, user_data: UserCreate):
    """Register a new user account."""
    # Implementation would hash password and store in database
    user_id = uuid4()
    return UserResponse(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
    )


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["authentication"])
@limiter.limit("10/minute")
async def login(request, login_data: LoginRequest):
    """Authenticate user and return access tokens."""
    # Implementation would verify credentials against database
    access_token = create_access_token(
        data={"sub": login_data.username, "role": "analyst"}
    )
    refresh_token = create_access_token(
        data={"sub": login_data.username, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
    )


@app.post("/api/v1/auth/refresh", response_model=TokenResponse, tags=["authentication"])
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        username = payload.get("sub")
        new_token = create_access_token(
            data={"sub": username, "role": payload.get("role")}
        )

        return TokenResponse(
            access_token=new_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@app.get("/api/v1/auth/me", response_model=UserResponse, tags=["authentication"])
async def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current user information."""
    # Implementation would fetch user details from database
    return UserResponse(
        id=uuid4(),
        username=token_data["sub"],
        email=f"{token_data['sub']}@example.com",
        role=UserRole(token_data.get("role", "viewer")),
    )


# Narrative Endpoints
@app.get("/api/v1/narratives", response_model=PaginatedResponse, tags=["narratives"])
@limiter.limit("100/minute")
async def list_narratives(
    request,
    pagination: PaginationParams = Depends(),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    alignment: Optional[AlignmentType] = Query(None, description="Filter by alignment"),
    status: Optional[NarrativeStatus] = Query(None, description="Filter by status"),
    trending: Optional[TrendingPeriod] = Query(
        None, description="Show trending narratives"
    ),
    token_data: dict = Depends(verify_token),
):
    """Get paginated list of narratives with optional filters."""
    # Implementation would query database with filters
    narratives = [
        NarrativeSummary(
            id=uuid4(),
            title="Sample Narrative",
            topic=topic or "Technology",
            alignment=alignment or AlignmentType.NEUTRAL,
            status=status or NarrativeStatus.ACTIVE,
            confidence_score=0.85,
            impact_score=0.72,
            article_count=156,
            trend_momentum=0.15,
            last_activity=datetime.utcnow(),
        )
    ]

    return PaginatedResponse(
        items=narratives,
        total=len(narratives),
        page=pagination.page,
        size=pagination.size,
        pages=1,
        has_next=False,
        has_prev=False,
    )


@app.get(
    "/api/v1/narratives/{narrative_id}",
    response_model=NarrativeResponse,
    tags=["narratives"],
)
@limiter.limit("200/minute")
async def get_narrative(
    narrative_id: UUID = Path(..., description="Narrative UUID"),
    include_timeline: bool = Query(True, description="Include timeline data"),
    include_excerpts: bool = Query(True, description="Include source excerpts"),
    include_tensions: bool = Query(False, description="Include narrative tensions"),
    token_data: dict = Depends(verify_token),
):
    """Get detailed narrative information by ID."""
    # Implementation would fetch from database
    return NarrativeResponse(
        id=narrative_id,
        title="Detailed Narrative",
        description="A comprehensive narrative description",
        topic="Technology",
        alignment=AlignmentType.POSITIVE,
        status=NarrativeStatus.ACTIVE,
        confidence_score=0.89,
        impact_score=0.76,
        timeline=(
            [
                TurningPoint(
                    timestamp=datetime.utcnow() - timedelta(days=5),
                    event_description="Major development announced",
                    impact_score=0.8,
                    supporting_articles=[uuid4()],
                )
            ]
            if include_timeline
            else []
        ),
        source_excerpts=(
            [
                SourceExcerpt(
                    article_id=uuid4(),
                    excerpt="Key excerpt from source material",
                    relevance_score=0.92,
                    timestamp=datetime.utcnow(),
                )
            ]
            if include_excerpts
            else []
        ),
        tensions=(
            [
                NarrativeTension(
                    opposing_narrative_id=uuid4(),
                    tension_score=0.65,
                    key_differences=["Different perspective on impact"],
                    timeline_overlap={"overlap_score": 0.3},
                )
            ]
            if include_tensions
            else []
        ),
        article_count=234,
        trend_momentum=0.23,
        last_activity=datetime.utcnow(),
    )


@app.post(
    "/api/v1/narratives",
    response_model=NarrativeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["narratives"],
)
@limiter.limit("20/minute")
async def create_narrative(
    narrative_data: NarrativeCreate,
    token_data: dict = Depends(require_role(UserRole.ANALYST)),
):
    """Create a new narrative."""
    narrative_id = uuid4()
    return NarrativeResponse(
        id=narrative_id,
        **narrative_data.dict(),
        timeline=[],
        source_excerpts=[],
        tensions=[],
        article_count=0,
        trend_momentum=0.0,
        last_activity=datetime.utcnow(),
    )


@app.put(
    "/api/v1/narratives/{narrative_id}",
    response_model=NarrativeResponse,
    tags=["narratives"],
)
@limiter.limit("50/minute")
async def update_narrative(
    narrative_id: UUID,
    update_data: NarrativeUpdate,
    token_data: dict = Depends(require_role(UserRole.ANALYST)),
):
    """Update an existing narrative."""
    # Implementation would update database record
    raise HTTPException(status_code=501, detail="Not implemented")


@app.delete(
    "/api/v1/narratives/{narrative_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["narratives"],
)
@limiter.limit("10/minute")
async def delete_narrative(
    narrative_id: UUID, token_data: dict = Depends(require_role(UserRole.ADMIN))
):
    """Delete a narrative."""
    # Implementation would soft delete from database
    pass


# Article Endpoints
@app.get("/api/v1/articles", response_model=PaginatedResponse, tags=["articles"])
@limiter.limit("100/minute")
async def list_articles(
    request,
    pagination: PaginationParams = Depends(),
    source_type: Optional[SourceType] = Query(None),
    language: Optional[str] = Query(None, max_length=5),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    token_data: dict = Depends(verify_token),
):
    """Get paginated list of articles with filters."""
    # Implementation would query database
    return PaginatedResponse(
        items=[],
        total=0,
        page=pagination.page,
        size=pagination.size,
        pages=0,
        has_next=False,
        has_prev=False,
    )


@app.get(
    "/api/v1/articles/{article_id}", response_model=ArticleResponse, tags=["articles"]
)
@limiter.limit("200/minute")
async def get_article(article_id: UUID, token_data: dict = Depends(verify_token)):
    """Get article by ID."""
    # Implementation would fetch from database
    raise HTTPException(status_code=404, detail="Article not found")


@app.post(
    "/api/v1/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["articles"],
)
@limiter.limit("50/minute")
async def create_article(
    article_data: ArticleCreate,
    token_data: dict = Depends(require_role(UserRole.ANALYST)),
):
    """Create a new article."""
    # Implementation would store in database and trigger processing
    article_id = uuid4()
    return ArticleResponse(
        id=article_id,
        **article_data.dict(),
        sentiment_score=0.0,
        relevance_score=0.0,
        narrative_ids=[],
    )


# Search Endpoints
@app.post("/api/v1/search", response_model=SearchResponse, tags=["search"])
@limiter.limit("100/minute")
async def search_narratives(
    request,
    search_request: SearchRequest,
    pagination: PaginationParams = Depends(),
    token_data: dict = Depends(verify_token),
):
    """Search narratives with advanced filtering and faceting."""
    # Implementation would use Elasticsearch or similar
    return SearchResponse(
        narratives=[], total=0, query_time_ms=25.5, suggestions=[], facets={}
    )


@app.get("/api/v1/search/suggestions", response_model=List[str], tags=["search"])
@limiter.limit("50/minute")
async def get_search_suggestions(
    request,
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    token_data: dict = Depends(verify_token),
):
    """Get search query suggestions."""
    # Implementation would use search index for autocomplete
    return [f"{query} suggestion {i}" for i in range(min(limit, 5))]


# Analytics Endpoints
@app.get(
    "/api/v1/analytics/trending",
    response_model=List[TrendingMetrics],
    tags=["analytics"],
)
@limiter.limit("50/minute")
async def get_trending_narratives(
    request,
    period: TrendingPeriod = Query(TrendingPeriod.DAY),
    limit: int = Query(20, ge=1, le=100),
    token_data: dict = Depends(verify_token),
):
    """Get trending narratives for specified period."""
    # Implementation would calculate trending metrics
    return [
        TrendingMetrics(
            narrative_id=uuid4(),
            period=period,
            growth_rate=1.5,
            velocity=0.8,
            acceleration=0.2,
            volume=150,
            engagement_score=0.75,
        )
    ]


@app.get(
    "/api/v1/analytics/temporal/{narrative_id}",
    response_model=TemporalAnalytics,
    tags=["analytics"],
)
@limiter.limit("100/minute")
async def get_temporal_analytics(
    request,
    narrative_id: UUID,
    period: TrendingPeriod = Query(TrendingPeriod.WEEK),
    token_data: dict = Depends(verify_token),
):
    """Get temporal analytics for a specific narrative."""
    return TemporalAnalytics(
        narrative_id=narrative_id,
        time_series={},
        trend_direction="up",
        seasonality_detected=False,
        anomalies=[],
        forecast_7d=[],
    )


@app.get("/api/v1/analytics/global", response_model=GlobalMetrics, tags=["analytics"])
@limiter.limit("20/minute")
async def get_global_metrics(request, token_data: dict = Depends(verify_token)):
    """Get global platform metrics."""
    return GlobalMetrics(
        total_narratives=1250,
        active_narratives=850,
        total_articles=45000,
        articles_last_24h=350,
        top_topics=[{"topic": "Technology", "count": 125}],
        sentiment_distribution={
            AlignmentType.POSITIVE: 400,
            AlignmentType.NEGATIVE: 250,
            AlignmentType.NEUTRAL: 350,
            AlignmentType.MIXED: 250,
        },
        processing_lag_minutes=2.5,
    )


# Clustering Endpoints
@app.get("/api/v1/clusters", response_model=List[ClusterResponse], tags=["clustering"])
@limiter.limit("50/minute")
async def list_clusters(
    request,
    min_size: int = Query(5, ge=1),
    min_coherence: float = Query(0.5, ge=0.0, le=1.0),
    token_data: dict = Depends(verify_token),
):
    """Get list of narrative clusters."""
    return []


@app.get(
    "/api/v1/clusters/{cluster_id}", response_model=ClusterResponse, tags=["clustering"]
)
@limiter.limit("100/minute")
async def get_cluster(
    request, cluster_id: UUID, token_data: dict = Depends(verify_token)
):
    """Get cluster details by ID."""
    raise HTTPException(status_code=404, detail="Cluster not found")


# Pipeline Endpoints
@app.post(
    "/api/v1/pipeline/tasks",
    response_model=PipelineTask,
    status_code=status.HTTP_201_CREATED,
    tags=["pipeline"],
)
@limiter.limit("20/minute")
async def create_pipeline_task(
    task_data: PipelineTaskCreate,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(require_role(UserRole.ANALYST)),
):
    """Create and queue a new pipeline task."""
    task = PipelineTask(
        type=task_data.type, status=TaskStatus.PENDING, parameters=task_data.parameters
    )

    # Add to background processing queue
    background_tasks.add_task(process_pipeline_task, task)

    return task


@app.get("/api/v1/pipeline/tasks", response_model=List[PipelineTask], tags=["pipeline"])
@limiter.limit("50/minute")
async def list_pipeline_tasks(
    request,
    status_filter: Optional[TaskStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    token_data: dict = Depends(require_role(UserRole.ANALYST)),
):
    """Get list of pipeline tasks with optional status filter."""
    return []


@app.get(
    "/api/v1/pipeline/tasks/{task_id}", response_model=PipelineTask, tags=["pipeline"]
)
@limiter.limit("100/minute")
async def get_pipeline_task(
    request, task_id: UUID, token_data: dict = Depends(require_role(UserRole.ANALYST))
):
    """Get pipeline task status and results."""
    raise HTTPException(status_code=404, detail="Task not found")


@app.post(
    "/api/v1/pipeline/rai-analysis/{narrative_id}",
    response_model=PipelineTask,
    tags=["pipeline"],
)
@limiter.limit("10/minute")
async def trigger_rai_analysis(
    narrative_id: UUID,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(require_role(UserRole.ANALYST)),
):
    """Trigger RAI (Responsible AI) analysis for a narrative."""
    task = PipelineTask(
        type="rai_analysis",
        status=TaskStatus.PENDING,
        parameters={"narrative_id": str(narrative_id)},
    )

    background_tasks.add_task(process_rai_analysis, narrative_id)

    return task


# Admin Endpoints
@app.get("/api/v1/admin/health", tags=["admin"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "uptime_seconds": 12345,
    }


@app.get("/api/v1/admin/metrics", tags=["admin"])
@limiter.limit("10/minute")
async def get_system_metrics(
    request, token_data: dict = Depends(require_role(UserRole.ADMIN))
):
    """Get detailed system metrics for monitoring."""
    return {
        "api": {
            "requests_per_minute": 450,
            "avg_response_time_ms": 125,
            "error_rate": 0.02,
        },
        "database": {
            "connection_pool_usage": 0.65,
            "query_avg_time_ms": 45,
            "active_connections": 12,
        },
        "pipeline": {
            "pending_tasks": 5,
            "processing_tasks": 2,
            "avg_task_duration_minutes": 8.5,
        },
    }


# ============================================================================
# WEBSOCKET ENDPOINTS FOR REAL-TIME UPDATES
# ============================================================================


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, List[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, channel: str = None):
        disconnected = []
        for connection in self.active_connections:
            try:
                # Check if connection is subscribed to channel
                if channel is None or channel in self.subscriptions.get(connection, []):
                    await connection.send_json(message)
            except:
                disconnected.append(connection)

        # Clean up disconnected websockets
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@app.websocket("/api/v1/ws/narratives")
async def websocket_narratives(websocket: WebSocket):
    """WebSocket endpoint for real-time narrative updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive subscription requests
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                channels = data.get("channels", [])
                manager.subscriptions[websocket] = channels
                await manager.send_personal_message(
                    {
                        "type": "subscription_confirmed",
                        "channels": channels,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    websocket,
                )

            elif data.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/api/v1/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe_trending":
                # Send initial trending data
                await manager.send_personal_message(
                    {
                        "type": "trending_update",
                        "data": {"period": "1h", "trending_narratives": []},
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# BACKGROUND TASKS
# ============================================================================


async def process_pipeline_task(task: PipelineTask):
    """Process a pipeline task in the background."""
    # Simulate task processing
    await asyncio.sleep(2)

    # Update task status
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.utcnow()

    # Simulate processing time
    await asyncio.sleep(5)

    # Complete task
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.progress = 100.0
    task.result = {"processed_items": 150, "insights_generated": 12}

    # Broadcast completion via WebSocket
    await manager.broadcast(
        {
            "type": "task_completed",
            "task_id": str(task.id),
            "task_type": task.type,
            "result": task.result,
        },
        "pipeline_updates",
    )


async def process_rai_analysis(narrative_id: UUID):
    """Process RAI analysis for a narrative."""
    # Simulate RAI analysis processing
    await asyncio.sleep(10)

    # Broadcast results
    await manager.broadcast(
        {
            "type": "rai_analysis_complete",
            "narrative_id": str(narrative_id),
            "analysis": {
                "bias_score": 0.25,
                "fairness_metrics": {"demographic_parity": 0.85},
                "transparency_score": 0.92,
                "recommendations": [
                    "Review source diversity",
                    "Validate fact-checking",
                ],
            },
        },
        "rai_updates",
    )


# ============================================================================
# STARTUP TASKS
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize services and background tasks on startup."""
    logging.info("Strategic Narrative Intelligence API starting up...")

    # Initialize background tasks for periodic updates
    asyncio.create_task(periodic_trending_updates())
    asyncio.create_task(periodic_metrics_broadcast())


async def periodic_trending_updates():
    """Send periodic trending updates via WebSocket."""
    while True:
        await asyncio.sleep(60)  # Update every minute

        await manager.broadcast(
            {
                "type": "trending_update",
                "data": {
                    "period": "1h",
                    "top_narratives": [
                        {
                            "id": str(uuid4()),
                            "title": "Sample Trending Narrative",
                            "growth_rate": 1.8,
                            "momentum": 0.65,
                        }
                    ],
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            "trending_updates",
        )


async def periodic_metrics_broadcast():
    """Send periodic system metrics via WebSocket."""
    while True:
        await asyncio.sleep(300)  # Update every 5 minutes

        await manager.broadcast(
            {
                "type": "system_metrics",
                "data": {
                    "active_narratives": 850,
                    "processing_lag": 2.3,
                    "api_requests_per_minute": 420,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            "system_metrics",
        )


if __name__ == "__main__":
    import uvicorn

    config = get_config()
    uvicorn.run(
        app, host=config.api.host, port=config.api.port, workers=config.api.workers
    )
