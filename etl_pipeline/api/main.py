"""
FastAPI Application for Strategic Narrative Intelligence ETL Pipeline

This module provides REST API endpoints for pipeline management,
real-time data access, and monitoring integration.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from fastapi import (BackgroundTasks, Depends, FastAPI, HTTPException, Path,
                     Query)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..core.config import get_config
from ..core.database import get_db_session, initialize_database
from ..core.database.models import (Article, ContentCategory, EntityMention,
                                    NewsFeed, PipelineRun, ProcessingStatus,
                                    TrendingTopic)
from ..core.exceptions import APIError, ValidationError
from ..core.monitoring import AlertManager, MetricsCollector
from ..core.tasks import (celery_app, check_celery_health, get_active_tasks,
                          health_check, ingest_feed, run_daily_pipeline,
                          trending_analysis)

logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer(auto_error=False)


# Initialize FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    config = get_config()

    app = FastAPI(
        title="Strategic Narrative Intelligence ETL Pipeline API",
        description="REST API for managing and monitoring the ETL pipeline",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.allowed_origins,
        allow_credentials=True,
        allow_methods=config.api.allowed_methods + ["PUT", "DELETE"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Initialize components
    app.state.config = config
    app.state.metrics_collector = MetricsCollector(config.monitoring)
    app.state.alert_manager = AlertManager(config.alerting)

    return app


app = create_app()


# Pydantic models for API
class ArticleResponse(BaseModel):
    """Article response model"""

    id: str
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    url: str
    author: Optional[str] = None
    published_at: datetime
    language: str
    source_name: Optional[str] = None
    processing_status: str
    relevance_score: Optional[float] = None
    quality_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    primary_category: Optional[str] = None
    categories: Optional[Dict[str, float]] = None
    created_at: datetime


class FeedResponse(BaseModel):
    """Feed response model"""

    id: str
    name: str
    url: str
    feed_type: str
    language: str
    is_active: bool
    priority: int
    reliability_score: Optional[float] = None
    last_fetched_at: Optional[datetime] = None
    last_successful_fetch_at: Optional[datetime] = None


class PipelineRunResponse(BaseModel):
    """Pipeline run response model"""

    id: str
    pipeline_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    feeds_processed: int
    articles_ingested: int
    articles_filtered: int
    articles_processed: int
    errors_count: int
    processing_time_seconds: Optional[float] = None
    throughput_articles_per_second: Optional[float] = None


class TrendingTopicResponse(BaseModel):
    """Trending topic response model"""

    id: str
    topic_name: str
    topic_keywords: List[str]
    mention_count: int
    trending_score: float
    article_count: int
    detected_at: datetime
    window_start: datetime
    window_end: datetime


class EntityResponse(BaseModel):
    """Entity response model"""

    id: str
    entity_text: str
    entity_type: str
    entity_label: str
    confidence_score: float
    context_snippet: Optional[str] = None


class TaskExecutionRequest(BaseModel):
    """Task execution request model"""

    task_name: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    queue: Optional[str] = None
    priority: Optional[int] = None


class FeedIngestionRequest(BaseModel):
    """Feed ingestion request model"""

    feed_ids: Optional[List[str]] = None  # If None, ingest all active feeds
    force: bool = False  # Force ingestion even if recently fetched


# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Simple token-based authentication"""
    config = get_config()

    if not credentials:
        if config.environment.value == "development":
            return {"username": "dev_user", "permissions": ["read", "write", "admin"]}
        raise HTTPException(status_code=401, detail="Authentication required")

    # In production, validate the token properly
    # For now, accept any token in development
    if config.environment.value == "development":
        return {"username": "api_user", "permissions": ["read", "write"]}

    # TODO: Implement proper JWT token validation
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# Health and status endpoints
@app.get("/health")
async def health_check_endpoint():
    """Comprehensive health check endpoint"""
    try:
        # Perform health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {},
        }

        # Database health
        try:
            with get_db_session() as db:
                db.execute("SELECT 1")
            health_status["checks"]["database"] = "healthy"
        except Exception as exc:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = f"unhealthy: {str(exc)}"

        # Celery health
        celery_health = check_celery_health()
        health_status["checks"]["celery"] = celery_health["status"]

        # Overall status
        if any("unhealthy" in str(check) for check in health_status["checks"].values()):
            health_status["status"] = "unhealthy"
        elif any(
            "degraded" in str(check) for check in health_status["checks"].values()
        ):
            health_status["status"] = "degraded"

        status_code = 200 if health_status["status"] == "healthy" else 503
        return JSONResponse(content=health_status, status_code=status_code)

    except Exception as exc:
        logger.error("Health check failed", error=str(exc))
        return JSONResponse(
            content={"status": "unhealthy", "error": str(exc)}, status_code=503
        )


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    try:
        metrics_collector = app.state.metrics_collector
        metrics_text = metrics_collector.get_prometheus_metrics()
        return PlainTextResponse(content=metrics_text, media_type="text/plain")
    except Exception as exc:
        logger.error("Failed to generate metrics", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


@app.get("/status")
async def status_endpoint(user: dict = Depends(get_current_user)):
    """Get overall system status"""
    try:
        with get_db_session() as db:
            # Get latest pipeline run
            latest_run = (
                db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
            )

            # Get active feeds count
            active_feeds = db.query(NewsFeed).filter(NewsFeed.is_active == True).count()

            # Get recent articles count
            recent_articles = (
                db.query(Article)
                .filter(Article.created_at >= datetime.utcnow() - timedelta(hours=24))
                .count()
            )

            # Get active tasks
            active_tasks = get_active_tasks()

            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "latest_pipeline_run": {
                    "pipeline_id": latest_run.pipeline_id if latest_run else None,
                    "status": latest_run.status.value if latest_run else None,
                    "started_at": (
                        latest_run.started_at.isoformat() if latest_run else None
                    ),
                    "completed_at": (
                        latest_run.completed_at.isoformat()
                        if latest_run and latest_run.completed_at
                        else None
                    ),
                },
                "active_feeds": active_feeds,
                "articles_last_24h": recent_articles,
                "active_tasks": len(active_tasks),
                "system_health": "healthy",  # Could be more sophisticated
            }

            return status

    except Exception as exc:
        logger.error("Failed to get system status", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to get system status")


# Article endpoints
@app.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    limit: int = Query(
        100, le=1000, description="Maximum number of articles to return"
    ),
    offset: int = Query(0, ge=0, description="Number of articles to skip"),
    language: Optional[str] = Query(None, description="Filter by language"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_relevance: Optional[float] = Query(
        None, ge=0, le=1, description="Minimum relevance score"
    ),
    from_date: Optional[datetime] = Query(
        None, description="Filter articles from this date"
    ),
    to_date: Optional[datetime] = Query(
        None, description="Filter articles to this date"
    ),
    user: dict = Depends(get_current_user),
):
    """Get articles with filtering and pagination"""
    try:
        with get_db_session() as db:
            query = db.query(Article)

            # Apply filters
            if language:
                query = query.filter(Article.language == language)

            if category:
                try:
                    cat_enum = ContentCategory(category)
                    query = query.filter(Article.primary_category == cat_enum)
                except ValueError:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid category: {category}"
                    )

            if min_relevance is not None:
                query = query.filter(Article.relevance_score >= min_relevance)

            if from_date:
                query = query.filter(Article.published_at >= from_date)

            if to_date:
                query = query.filter(Article.published_at <= to_date)

            # Order by publication date (newest first)
            query = query.order_by(Article.published_at.desc())

            # Apply pagination
            articles = query.offset(offset).limit(limit).all()

            # Convert to response models
            return [
                ArticleResponse(
                    id=str(article.id),
                    title=article.title,
                    content=article.content,
                    summary=article.summary,
                    url=article.url,
                    author=article.author,
                    published_at=article.published_at,
                    language=article.language.value,
                    source_name=article.source_name,
                    processing_status=article.processing_status.value,
                    relevance_score=article.relevance_score,
                    quality_score=article.quality_score,
                    sentiment_score=article.sentiment_score,
                    primary_category=(
                        article.primary_category.value
                        if article.primary_category
                        else None
                    ),
                    categories=article.categories,
                    created_at=article.created_at,
                )
                for article in articles
            ]

    except Exception as exc:
        logger.error("Failed to get articles", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve articles")


@app.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str = Path(..., description="Article ID"),
    user: dict = Depends(get_current_user),
):
    """Get a specific article by ID"""
    try:
        with get_db_session() as db:
            article = db.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(status_code=404, detail="Article not found")

            return ArticleResponse(
                id=str(article.id),
                title=article.title,
                content=article.content,
                summary=article.summary,
                url=article.url,
                author=article.author,
                published_at=article.published_at,
                language=article.language.value,
                source_name=article.source_name,
                processing_status=article.processing_status.value,
                relevance_score=article.relevance_score,
                quality_score=article.quality_score,
                sentiment_score=article.sentiment_score,
                primary_category=(
                    article.primary_category.value if article.primary_category else None
                ),
                categories=article.categories,
                created_at=article.created_at,
            )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to get article", article_id=article_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve article")


@app.get("/articles/{article_id}/entities", response_model=List[EntityResponse])
async def get_article_entities(
    article_id: str = Path(..., description="Article ID"),
    user: dict = Depends(get_current_user),
):
    """Get entities extracted from a specific article"""
    try:
        with get_db_session() as db:
            # Check if article exists
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")

            # Get entities
            entities = (
                db.query(EntityMention)
                .filter(EntityMention.article_id == article_id)
                .order_by(EntityMention.confidence_score.desc())
                .all()
            )

            return [
                EntityResponse(
                    id=str(entity.id),
                    entity_text=entity.entity_text,
                    entity_type=entity.entity_type,
                    entity_label=entity.entity_label,
                    confidence_score=entity.confidence_score,
                    context_snippet=entity.context_snippet,
                )
                for entity in entities
            ]

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to get article entities", article_id=article_id, error=str(exc)
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve article entities"
        )


# Feed endpoints
@app.get("/feeds", response_model=List[FeedResponse])
async def get_feeds(
    active_only: bool = Query(True, description="Only return active feeds"),
    user: dict = Depends(get_current_user),
):
    """Get news feeds"""
    try:
        with get_db_session() as db:
            query = db.query(NewsFeed)

            if active_only:
                query = query.filter(NewsFeed.is_active == True)

            feeds = query.order_by(NewsFeed.priority, NewsFeed.name).all()

            return [
                FeedResponse(
                    id=str(feed.id),
                    name=feed.name,
                    url=feed.url,
                    feed_type=feed.feed_type.value,
                    language=feed.language.value,
                    is_active=feed.is_active,
                    priority=feed.priority,
                    reliability_score=feed.reliability_score,
                    last_fetched_at=feed.last_fetched_at,
                    last_successful_fetch_at=feed.last_successful_fetch_at,
                )
                for feed in feeds
            ]

    except Exception as exc:
        logger.error("Failed to get feeds", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve feeds")


@app.post("/feeds/{feed_id}/ingest")
async def trigger_feed_ingestion(
    feed_id: str = Path(..., description="Feed ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: dict = Depends(get_current_user),
):
    """Trigger manual ingestion for a specific feed"""
    try:
        with get_db_session() as db:
            feed = db.query(NewsFeed).filter(NewsFeed.id == feed_id).first()

            if not feed:
                raise HTTPException(status_code=404, detail="Feed not found")

            if not feed.is_active:
                raise HTTPException(status_code=400, detail="Feed is not active")

            # Create feed config for task
            feed_config = {
                "id": str(feed.id),
                "name": feed.name,
                "url": feed.url,
                "type": feed.feed_type.value,
                "language": feed.language.value,
                "api_headers": feed.api_headers,
                "api_params": feed.api_params,
                "api_key_required": feed.api_key_required,
            }

            # Trigger ingestion task
            task = ingest_feed.delay(feed_config)

            return {
                "task_id": task.id,
                "feed_id": feed_id,
                "status": "submitted",
                "message": f"Ingestion task submitted for feed {feed.name}",
            }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to trigger feed ingestion", feed_id=feed_id, error=str(exc)
        )
        raise HTTPException(status_code=500, detail="Failed to trigger feed ingestion")


# Pipeline endpoints
@app.get("/pipelines/runs", response_model=List[PipelineRunResponse])
async def get_pipeline_runs(
    limit: int = Query(50, le=200, description="Maximum number of runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    user: dict = Depends(get_current_user),
):
    """Get pipeline execution history"""
    try:
        with get_db_session() as db:
            runs = (
                db.query(PipelineRun)
                .order_by(PipelineRun.started_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [
                PipelineRunResponse(
                    id=str(run.id),
                    pipeline_id=run.pipeline_id,
                    status=run.status.value,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    feeds_processed=run.feeds_processed,
                    articles_ingested=run.articles_ingested,
                    articles_filtered=run.articles_filtered,
                    articles_processed=run.articles_processed,
                    errors_count=run.errors_count,
                    processing_time_seconds=run.processing_time_seconds,
                    throughput_articles_per_second=run.throughput_articles_per_second,
                )
                for run in runs
            ]

    except Exception as exc:
        logger.error("Failed to get pipeline runs", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve pipeline runs")


@app.post("/pipelines/trigger")
async def trigger_pipeline(user: dict = Depends(get_current_user)):
    """Trigger manual pipeline execution"""
    try:
        # Check user permissions
        if "admin" not in user.get("permissions", []):
            raise HTTPException(status_code=403, detail="Admin permissions required")

        # Trigger pipeline task
        task = run_daily_pipeline.delay()

        return {
            "task_id": task.id,
            "status": "submitted",
            "message": "Daily pipeline execution triggered manually",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to trigger pipeline", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to trigger pipeline")


# Trending topics endpoints
@app.get("/trending", response_model=List[TrendingTopicResponse])
async def get_trending_topics(
    limit: int = Query(20, le=100, description="Maximum number of topics to return"),
    hours_back: int = Query(
        24, ge=1, le=168, description="Hours to look back for trending topics"
    ),
    min_score: Optional[float] = Query(
        None, ge=0, description="Minimum trending score"
    ),
    user: dict = Depends(get_current_user),
):
    """Get current trending topics"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        with get_db_session() as db:
            query = db.query(TrendingTopic).filter(
                TrendingTopic.detected_at >= cutoff_time
            )

            if min_score is not None:
                query = query.filter(TrendingTopic.trending_score >= min_score)

            topics = (
                query.order_by(TrendingTopic.trending_score.desc()).limit(limit).all()
            )

            return [
                TrendingTopicResponse(
                    id=str(topic.id),
                    topic_name=topic.topic_name,
                    topic_keywords=topic.topic_keywords,
                    mention_count=topic.mention_count,
                    trending_score=topic.trending_score,
                    article_count=topic.article_count,
                    detected_at=topic.detected_at,
                    window_start=topic.window_start,
                    window_end=topic.window_end,
                )
                for topic in topics
            ]

    except Exception as exc:
        logger.error("Failed to get trending topics", error=str(exc))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve trending topics"
        )


@app.post("/trending/analyze")
async def trigger_trending_analysis(user: dict = Depends(get_current_user)):
    """Trigger manual trending analysis"""
    try:
        # Trigger trending analysis task
        task = trending_analysis.delay()

        return {
            "task_id": task.id,
            "status": "submitted",
            "message": "Trending analysis triggered manually",
        }

    except Exception as exc:
        logger.error("Failed to trigger trending analysis", error=str(exc))
        raise HTTPException(
            status_code=500, detail="Failed to trigger trending analysis"
        )


# Task management endpoints
@app.get("/tasks/active")
async def get_active_tasks(user: dict = Depends(get_current_user)):
    """Get currently active Celery tasks"""
    try:
        active_tasks = get_active_tasks()
        return {
            "active_tasks": active_tasks,
            "count": len(active_tasks),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error("Failed to get active tasks", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve active tasks")


@app.post("/tasks/execute")
async def execute_task(
    request: TaskExecutionRequest, user: dict = Depends(get_current_user)
):
    """Execute a specific task"""
    try:
        # Check user permissions
        if "admin" not in user.get("permissions", []):
            raise HTTPException(status_code=403, detail="Admin permissions required")

        # Get task by name
        task_func = getattr(
            celery_app.tasks.get(f"etl.{request.task_name}"), "delay", None
        )
        if not task_func:
            raise HTTPException(
                status_code=400, detail=f"Unknown task: {request.task_name}"
            )

        # Execute task
        task = task_func(*request.args, **request.kwargs)

        return {
            "task_id": task.id,
            "task_name": request.task_name,
            "status": "submitted",
            "queue": request.queue or "default",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to execute task", task_name=request.task_name, error=str(exc)
        )
        raise HTTPException(status_code=500, detail="Failed to execute task")


# Analytics endpoints
@app.get("/analytics/summary")
async def get_analytics_summary(
    days_back: int = Query(
        7, ge=1, le=30, description="Days to look back for analytics"
    ),
    user: dict = Depends(get_current_user),
):
    """Get analytics summary"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)

        with get_db_session() as db:
            # Basic counts
            total_articles = (
                db.query(Article).filter(Article.created_at >= cutoff_time).count()
            )

            processed_articles = (
                db.query(Article)
                .filter(
                    Article.created_at >= cutoff_time,
                    Article.processing_status == ProcessingStatus.COMPLETED,
                )
                .count()
            )

            # Language distribution
            language_results = db.execute(
                """
                SELECT language, COUNT(*) as count
                FROM articles 
                WHERE created_at >= %s
                GROUP BY language
                ORDER BY count DESC
            """,
                (cutoff_time,),
            ).fetchall()

            language_distribution = {row[0]: row[1] for row in language_results}

            # Category distribution
            category_results = db.execute(
                """
                SELECT primary_category, COUNT(*) as count
                FROM articles 
                WHERE created_at >= %s AND primary_category IS NOT NULL
                GROUP BY primary_category
                ORDER BY count DESC
            """,
                (cutoff_time,),
            ).fetchall()

            category_distribution = {row[0]: row[1] for row in category_results}

            # Average scores
            avg_scores = db.execute(
                """
                SELECT 
                    AVG(relevance_score) as avg_relevance,
                    AVG(quality_score) as avg_quality,
                    AVG(sentiment_score) as avg_sentiment
                FROM articles 
                WHERE created_at >= %s
                AND relevance_score IS NOT NULL
                AND quality_score IS NOT NULL
                AND sentiment_score IS NOT NULL
            """,
                (cutoff_time,),
            ).fetchone()

            return {
                "period": {
                    "days_back": days_back,
                    "start_date": cutoff_time.isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                },
                "article_counts": {
                    "total": total_articles,
                    "processed": processed_articles,
                    "processing_rate": processed_articles / max(total_articles, 1),
                },
                "language_distribution": language_distribution,
                "category_distribution": category_distribution,
                "average_scores": (
                    {
                        "relevance": float(avg_scores[0]) if avg_scores[0] else 0.0,
                        "quality": float(avg_scores[1]) if avg_scores[1] else 0.0,
                        "sentiment": float(avg_scores[2]) if avg_scores[2] else 0.0,
                    }
                    if avg_scores
                    else {"relevance": 0.0, "quality": 0.0, "sentiment": 0.0}
                ),
            }

    except Exception as exc:
        logger.error("Failed to get analytics summary", error=str(exc))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve analytics summary"
        )


# Error handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc: ValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "detail": exc.message,
            "context": exc.context,
        },
    )


@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    """Handle API errors"""
    status_code = exc.context.get("status_code", 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": "api_error", "detail": exc.message, "context": exc.context},
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        config = get_config()

        # Initialize database
        initialize_database(config.database)

        logger.info(
            "FastAPI application started successfully",
            environment=config.environment.value,
            debug=config.debug,
        )

    except Exception as exc:
        logger.error("Failed to start application", error=str(exc))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        # Close alert manager resources
        if hasattr(app.state, "alert_manager"):
            await app.state.alert_manager.close()

        logger.info("FastAPI application shutdown completed")

    except Exception as exc:
        logger.error("Error during application shutdown", error=str(exc))


if __name__ == "__main__":
    import uvicorn

    config = get_config()
    uvicorn.run(
        "api.main:app",
        host=config.api.host,
        port=config.api.port,
        workers=config.api.workers,
        reload=config.debug,
        log_level=config.monitoring.log_level.lower(),
    )
