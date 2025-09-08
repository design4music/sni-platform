"""
Pipeline tasks for Strategic Narrative Intelligence ETL Pipeline

This module defines all Celery tasks for the ETL pipeline including
ingestion, processing, ML integration, and monitoring tasks.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from celery import chain, chord, group

from ..config import get_config
from ..database import get_db_session
from ..database.models import (Article, DataQualityReport, NewsFeed,
                               PipelineRun, ProcessingStatus, TrendingTopic)
from ..exceptions import (IngestionError, PipelineError, ProcessingError,
                          TaskError, ValidationError)
from ..ingestion import FeedIngestor
from ..monitoring import MetricsCollector
from ..processing import ContentProcessor
from .celery_app import ETLTask, celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(base=ETLTask, bind=True, max_retries=3, default_retry_delay=300)
def run_daily_pipeline(self) -> Dict[str, Any]:
    """
    Execute the complete daily ETL pipeline.

    This is the main orchestration task that coordinates all pipeline phases.
    """
    pipeline_start = datetime.utcnow()
    pipeline_id = f"pipeline_{pipeline_start.strftime('%Y%m%d_%H%M%S')}"

    logger.info(
        "Starting daily ETL pipeline", pipeline_id=pipeline_id, task_id=self.request.id
    )

    try:
        config = get_config()

        # Create pipeline run record
        with get_db_session() as db:
            pipeline_run = PipelineRun(
                pipeline_id=pipeline_id,
                status=ProcessingStatus.IN_PROGRESS,
                started_at=pipeline_start,
                config_snapshot=config.to_dict(),
            )
            db.add(pipeline_run)
            db.commit()
            db.refresh(pipeline_run)
            run_id = pipeline_run.id

        # Phase 1: Feed Ingestion (parallel)
        logger.info("Starting ingestion phase", pipeline_id=pipeline_id)
        ingestion_job = create_ingestion_job()
        ingestion_results = ingestion_job.apply_async().get(
            timeout=3600
        )  # 1 hour timeout

        # Collect ingestion statistics
        total_articles = sum(
            result.get("articles_count", 0)
            for result in ingestion_results
            if result.get("success")
        )
        failed_feeds = sum(
            1 for result in ingestion_results if not result.get("success")
        )

        # Update pipeline run with ingestion results
        with get_db_session() as db:
            pipeline_run = (
                db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            )
            if pipeline_run:
                pipeline_run.articles_ingested = total_articles
                pipeline_run.feeds_processed = len(ingestion_results)
                db.commit()

        # Phase 2: Content Processing (batched)
        logger.info("Starting processing phase", pipeline_id=pipeline_id)
        processing_job = create_processing_job()
        processing_results = processing_job.apply_async().get(
            timeout=7200
        )  # 2 hour timeout

        # Aggregate processing results
        total_processed = sum(
            result.get("processed_count", 0) for result in processing_results
        )
        total_filtered = sum(
            result.get("filtered_count", 0) for result in processing_results
        )

        # Update pipeline run with processing results
        with get_db_session() as db:
            pipeline_run = (
                db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            )
            if pipeline_run:
                pipeline_run.articles_processed = total_processed
                pipeline_run.articles_filtered = total_filtered
                db.commit()

        # Phase 3: ML Integration
        logger.info("Starting ML integration phase", pipeline_id=pipeline_id)
        ml_result = ml_integration_pipeline.delay()
        ml_stats = ml_result.get(timeout=7200)  # 2 hour timeout

        # Phase 4: Trending Analysis
        logger.info("Starting trending analysis", pipeline_id=pipeline_id)
        trending_result = trending_analysis.delay()
        trending_stats = trending_result.get(timeout=600)  # 10 minute timeout

        # Complete pipeline
        pipeline_end = datetime.utcnow()
        processing_time = (pipeline_end - pipeline_start).total_seconds()

        # Update pipeline run as completed
        with get_db_session() as db:
            pipeline_run = (
                db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            )
            if pipeline_run:
                pipeline_run.status = ProcessingStatus.COMPLETED
                pipeline_run.completed_at = pipeline_end
                pipeline_run.processing_time_seconds = processing_time
                if total_articles > 0 and processing_time > 0:
                    pipeline_run.throughput_articles_per_second = (
                        total_articles / processing_time
                    )
                db.commit()

        # Final result
        result = {
            "pipeline_id": pipeline_id,
            "status": "completed",
            "processing_time_seconds": processing_time,
            "ingestion": {
                "total_articles": total_articles,
                "failed_feeds": failed_feeds,
                "results": ingestion_results,
            },
            "processing": {
                "processed_articles": total_processed,
                "filtered_articles": total_filtered,
                "results": processing_results,
            },
            "ml_integration": ml_stats,
            "trending_analysis": trending_stats,
        }

        logger.info(
            "Daily ETL pipeline completed successfully",
            pipeline_id=pipeline_id,
            processing_time=processing_time,
            total_articles=total_articles,
            processed_articles=total_processed,
        )

        return result

    except Exception as exc:
        # Handle pipeline failure
        logger.error(
            "Daily ETL pipeline failed",
            pipeline_id=pipeline_id,
            error=str(exc),
            exc_info=True,
        )

        # Update pipeline run as failed
        try:
            with get_db_session() as db:
                pipeline_run = (
                    db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
                )
                if pipeline_run:
                    pipeline_run.status = ProcessingStatus.FAILED
                    pipeline_run.completed_at = datetime.utcnow()
                    pipeline_run.error_message = str(exc)
                    pipeline_run.error_details = {"traceback": str(exc)}
                    db.commit()
        except Exception as db_exc:
            logger.error("Failed to update pipeline run status", error=str(db_exc))

        raise PipelineError(f"Daily pipeline failed: {str(exc)}") from exc


def create_ingestion_job():
    """Create parallel ingestion job for all active feeds"""

    # Get active feeds
    with get_db_session() as db:
        feeds = db.query(NewsFeed).filter(NewsFeed.is_active == True).all()
        feed_configs = []

        for feed in feeds:
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
            feed_configs.append(feed_config)

    # Create parallel ingestion tasks
    ingestion_tasks = group(ingest_feed.si(feed_config) for feed_config in feed_configs)

    return ingestion_tasks


def create_processing_job():
    """Create batched processing job for unprocessed articles"""

    # Get unprocessed articles
    with get_db_session() as db:
        articles = (
            db.query(Article)
            .filter(Article.processing_status == ProcessingStatus.PENDING)
            .all()
        )

        article_ids = [str(article.id) for article in articles]

    if not article_ids:
        logger.info("No articles to process")
        return group([])

    # Create batched processing tasks
    config = get_config()
    batch_size = config.processing.batch_size

    processing_tasks = group(
        process_content_batch.si(article_ids[i : i + batch_size])
        for i in range(0, len(article_ids), batch_size)
    )

    return processing_tasks


@celery_app.task(base=ETLTask, bind=True, max_retries=5, default_retry_delay=60)
def ingest_feed(self, feed_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingest articles from a single news feed.

    Args:
        feed_config: Feed configuration dictionary

    Returns:
        Dictionary with ingestion results
    """
    feed_id = feed_config.get("id")

    logger.info("Starting feed ingestion", feed_id=feed_id, task_id=self.request.id)

    try:
        config = get_config()
        ingestor = FeedIngestor(config.ingestion)

        # Run ingestion (this is async, so we need to handle it properly)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ingestor.ingest_feed(feed_config))
        finally:
            loop.close()

        logger.info(
            "Feed ingestion completed",
            feed_id=feed_id,
            articles_count=result.articles_count,
            new_articles=result.new_articles_count,
            processing_time=result.processing_time_seconds,
        )

        return {
            "success": result.success,
            "feed_id": result.feed_id,
            "articles_count": result.articles_count,
            "new_articles_count": result.new_articles_count,
            "duplicate_articles_count": result.duplicate_articles_count,
            "processing_time_seconds": result.processing_time_seconds,
        }

    except Exception as exc:
        logger.error(
            "Feed ingestion failed", feed_id=feed_id, error=str(exc), exc_info=True
        )

        # Determine if this should be retried
        if isinstance(exc, IngestionError):
            # Check if this is a retryable error based on the HTTP status or error type
            if "429" in str(exc) or "timeout" in str(exc).lower():
                # Rate limited or timeout - retry with exponential backoff
                raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
            elif "404" in str(exc) or "invalid" in str(exc).lower():
                # Permanent error - don't retry
                return {
                    "success": False,
                    "feed_id": feed_id,
                    "error": str(exc),
                    "retryable": False,
                }

        # Retry for other errors
        raise self.retry(exc=exc)


@celery_app.task(base=ETLTask, bind=True, max_retries=3, default_retry_delay=120)
def process_content_batch(self, article_ids: List[str]) -> Dict[str, Any]:
    """
    Process a batch of articles for content filtering and NER.

    Args:
        article_ids: List of article IDs to process

    Returns:
        Dictionary with processing results
    """
    logger.info(
        "Starting content processing batch",
        article_count=len(article_ids),
        task_id=self.request.id,
    )

    try:
        config = get_config()
        processor = ContentProcessor(config.processing)

        # Run processing (this is async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(processor.process_articles(article_ids))
        finally:
            loop.close()

        logger.info(
            "Content processing batch completed",
            processed_count=result.processed_count,
            filtered_count=result.filtered_count,
            entities_extracted=result.entities_extracted,
            processing_time=result.processing_time_seconds,
        )

        return {
            "success": True,
            "processed_count": result.processed_count,
            "filtered_count": result.filtered_count,
            "failed_count": result.failed_count,
            "entities_extracted": result.entities_extracted,
            "processing_time_seconds": result.processing_time_seconds,
            "categories_assigned": result.categories_assigned,
        }

    except Exception as exc:
        logger.error(
            "Content processing batch failed",
            article_count=len(article_ids),
            error=str(exc),
            exc_info=True,
        )

        raise self.retry(exc=exc)


@celery_app.task(base=ETLTask, bind=True, max_retries=2, default_retry_delay=300)
def ml_integration_pipeline(self) -> Dict[str, Any]:
    """
    Integrate processed articles with ML pipeline for clustering and generation.

    Returns:
        Dictionary with ML integration results
    """
    logger.info("Starting ML integration pipeline", task_id=self.request.id)

    try:
        # Get articles ready for ML processing
        with get_db_session() as db:
            articles = (
                db.query(Article)
                .filter(
                    Article.processing_status == ProcessingStatus.COMPLETED,
                    Article.ml_status == ProcessingStatus.PENDING,
                )
                .limit(1000)
                .all()
            )  # Process in chunks

            article_ids = [str(article.id) for article in articles]

        if not article_ids:
            logger.info("No articles ready for ML processing")
            return {"processed_articles": 0}

        # Here you would integrate with your ML pipeline
        # For now, we'll simulate the integration

        # Update articles as ML processed
        with get_db_session() as db:
            db.query(Article).filter(Article.id.in_(article_ids)).update(
                {Article.ml_status: ProcessingStatus.COMPLETED},
                synchronize_session=False,
            )
            db.commit()

        logger.info(
            "ML integration pipeline completed", processed_articles=len(article_ids)
        )

        return {
            "processed_articles": len(article_ids),
            "clustering_results": {"clusters_created": 50},  # Simulated
            "generation_results": {"summaries_generated": 25},  # Simulated
        }

    except Exception as exc:
        logger.error("ML integration pipeline failed", error=str(exc), exc_info=True)

        raise self.retry(exc=exc)


@celery_app.task(base=ETLTask, bind=True)
def trending_analysis(self) -> Dict[str, Any]:
    """
    Perform real-time trending analysis on recent articles.

    Returns:
        Dictionary with trending analysis results
    """
    logger.info("Starting trending analysis", task_id=self.request.id)

    try:
        # Get recent articles (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        with get_db_session() as db:
            recent_articles = (
                db.query(Article)
                .filter(
                    Article.published_at >= cutoff_time,
                    Article.processing_status == ProcessingStatus.COMPLETED,
                )
                .all()
            )

        # Simple trending analysis (in production, this would be more sophisticated)
        trending_topics = {}

        for article in recent_articles:
            # Extract keywords from title and categories
            if article.categories:
                for category, score in article.categories.items():
                    if score > 0.5:  # High confidence categories
                        if category not in trending_topics:
                            trending_topics[category] = {
                                "count": 0,
                                "articles": [],
                                "total_score": 0.0,
                            }
                        trending_topics[category]["count"] += 1
                        trending_topics[category]["articles"].append(str(article.id))
                        trending_topics[category]["total_score"] += score

        # Calculate trending scores and save top topics
        saved_topics = 0

        with get_db_session() as db:
            for topic, data in trending_topics.items():
                if data["count"] >= 3:  # Minimum articles for trending
                    trending_score = data["total_score"] / data["count"] * data["count"]

                    trending_topic = TrendingTopic(
                        topic_name=topic,
                        topic_keywords=[topic],
                        mention_count=data["count"],
                        trending_score=trending_score,
                        window_start=cutoff_time,
                        window_end=datetime.utcnow(),
                        article_count=data["count"],
                        sample_article_ids=data["articles"][:10],  # Store sample
                    )

                    db.add(trending_topic)
                    saved_topics += 1

            db.commit()

        logger.info(
            "Trending analysis completed",
            topics_analyzed=len(trending_topics),
            trending_topics_saved=saved_topics,
        )

        return {
            "topics_analyzed": len(trending_topics),
            "trending_topics_saved": saved_topics,
            "analysis_window_hours": 24,
        }

    except Exception as exc:
        logger.error("Trending analysis failed", error=str(exc), exc_info=True)

        raise TaskError(f"Trending analysis failed: {str(exc)}") from exc


@celery_app.task(base=ETLTask, bind=True)
def health_check(self) -> Dict[str, Any]:
    """
    Perform comprehensive system health check.

    Returns:
        Dictionary with health check results
    """
    logger.debug("Performing health check", task_id=self.request.id)

    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {},
    }

    try:
        # Check database connectivity
        with get_db_session() as db:
            db.execute("SELECT 1")
            health_status["checks"]["database"] = "connected"

        # Check recent pipeline runs
        with get_db_session() as db:
            recent_runs = (
                db.query(PipelineRun)
                .filter(
                    PipelineRun.started_at >= datetime.utcnow() - timedelta(hours=48)
                )
                .order_by(PipelineRun.started_at.desc())
                .limit(5)
                .all()
            )

            if recent_runs:
                latest_run = recent_runs[0]
                health_status["checks"]["latest_pipeline"] = {
                    "pipeline_id": latest_run.pipeline_id,
                    "status": latest_run.status.value,
                    "started_at": latest_run.started_at.isoformat(),
                    "completed_at": (
                        latest_run.completed_at.isoformat()
                        if latest_run.completed_at
                        else None
                    ),
                }

                # Check if latest run is stuck
                if (
                    latest_run.status == ProcessingStatus.IN_PROGRESS
                    and latest_run.started_at < datetime.utcnow() - timedelta(hours=6)
                ):
                    health_status["status"] = "degraded"
                    health_status["checks"]["pipeline_stuck"] = True
            else:
                health_status["checks"]["latest_pipeline"] = "no_recent_runs"

        # Check active feeds
        with get_db_session() as db:
            active_feeds_count = (
                db.query(NewsFeed).filter(NewsFeed.is_active == True).count()
            )
            health_status["checks"]["active_feeds"] = active_feeds_count

        # Check recent articles
        with get_db_session() as db:
            recent_articles_count = (
                db.query(Article)
                .filter(Article.created_at >= datetime.utcnow() - timedelta(hours=24))
                .count()
            )
            health_status["checks"]["recent_articles"] = recent_articles_count

            if recent_articles_count == 0:
                health_status["status"] = "degraded"
                health_status["checks"]["no_recent_articles"] = True

    except Exception as exc:
        health_status["status"] = "unhealthy"
        health_status["checks"]["error"] = str(exc)
        logger.error("Health check failed", error=str(exc))

    return health_status


@celery_app.task(base=ETLTask, bind=True)
def data_quality_check(self) -> Dict[str, Any]:
    """
    Perform data quality assessment and generate metrics.

    Returns:
        Dictionary with data quality results
    """
    logger.info("Starting data quality check", task_id=self.request.id)

    try:
        quality_metrics = {"timestamp": datetime.utcnow().isoformat(), "metrics": {}}

        with get_db_session() as db:
            # Check for duplicate articles
            duplicate_count = db.execute(
                """
                SELECT COUNT(*) FROM (
                    SELECT content_hash, COUNT(*) as cnt 
                    FROM articles 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY content_hash 
                    HAVING COUNT(*) > 1
                ) duplicates
            """
            ).scalar()

            quality_metrics["metrics"]["duplicate_articles_24h"] = duplicate_count

            # Check processing success rate
            total_articles = (
                db.query(Article)
                .filter(Article.created_at >= datetime.utcnow() - timedelta(hours=24))
                .count()
            )

            processed_articles = (
                db.query(Article)
                .filter(
                    Article.created_at >= datetime.utcnow() - timedelta(hours=24),
                    Article.processing_status == ProcessingStatus.COMPLETED,
                )
                .count()
            )

            processing_success_rate = (
                (processed_articles / total_articles) if total_articles > 0 else 0
            )
            quality_metrics["metrics"][
                "processing_success_rate"
            ] = processing_success_rate

            # Check average relevance score
            avg_relevance = db.execute(
                """
                SELECT AVG(relevance_score) 
                FROM articles 
                WHERE created_at >= NOW() - INTERVAL '24 hours' 
                AND relevance_score IS NOT NULL
            """
            ).scalar()

            quality_metrics["metrics"]["avg_relevance_score"] = float(
                avg_relevance or 0
            )

            # Check language distribution
            language_dist = db.execute(
                """
                SELECT language, COUNT(*) as count
                FROM articles 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY language
            """
            ).fetchall()

            quality_metrics["metrics"]["language_distribution"] = {
                row[0]: row[1] for row in language_dist
            }

        logger.info(
            "Data quality check completed",
            duplicate_articles=duplicate_count,
            processing_success_rate=processing_success_rate,
        )

        return quality_metrics

    except Exception as exc:
        logger.error("Data quality check failed", error=str(exc), exc_info=True)

        raise TaskError(f"Data quality check failed: {str(exc)}") from exc


@celery_app.task(base=ETLTask, bind=True)
def cleanup_old_data(self) -> Dict[str, Any]:
    """
    Clean up old data based on retention policies.

    Returns:
        Dictionary with cleanup results
    """
    logger.info("Starting data cleanup", task_id=self.request.id)

    try:
        config = get_config()
        cleanup_results = {}

        with get_db_session() as db:
            # Clean up old articles
            article_cutoff = datetime.utcnow() - timedelta(
                days=config.pipeline.article_retention_days
            )
            deleted_articles = db.execute(
                """
                DELETE FROM articles 
                WHERE created_at < :cutoff
            """,
                {"cutoff": article_cutoff},
            ).rowcount

            cleanup_results["deleted_articles"] = deleted_articles

            # Clean up old metrics
            metrics_cutoff = datetime.utcnow() - timedelta(
                days=config.pipeline.metrics_retention_days
            )
            deleted_metrics = db.execute(
                """
                DELETE FROM feed_metrics 
                WHERE date < :cutoff
            """,
                {"cutoff": metrics_cutoff.date()},
            ).rowcount

            cleanup_results["deleted_metrics"] = deleted_metrics

            # Clean up old pipeline runs
            runs_cutoff = datetime.utcnow() - timedelta(
                days=90
            )  # Keep pipeline runs for 3 months
            deleted_runs = db.execute(
                """
                DELETE FROM pipeline_runs 
                WHERE started_at < :cutoff
            """,
                {"cutoff": runs_cutoff},
            ).rowcount

            cleanup_results["deleted_pipeline_runs"] = deleted_runs

            # Clean up old trending topics
            trending_cutoff = datetime.utcnow() - timedelta(
                days=30
            )  # Keep trending topics for 1 month
            deleted_trending = db.execute(
                """
                DELETE FROM trending_topics 
                WHERE detected_at < :cutoff
            """,
                {"cutoff": trending_cutoff},
            ).rowcount

            cleanup_results["deleted_trending_topics"] = deleted_trending

            db.commit()

        logger.info(
            "Data cleanup completed",
            deleted_articles=deleted_articles,
            deleted_metrics=deleted_metrics,
            deleted_runs=deleted_runs,
            deleted_trending=deleted_trending,
        )

        return cleanup_results

    except Exception as exc:
        logger.error("Data cleanup failed", error=str(exc), exc_info=True)

        raise TaskError(f"Data cleanup failed: {str(exc)}") from exc


@celery_app.task(base=ETLTask, bind=True)
def generate_quality_report(self) -> Dict[str, Any]:
    """
    Generate comprehensive data quality report.

    Returns:
        Dictionary with quality report results
    """
    logger.info("Generating data quality report", task_id=self.request.id)

    try:
        report_date = datetime.utcnow()

        with get_db_session() as db:
            # Collect comprehensive quality metrics
            report_data = {
                "report_date": report_date,
                "report_type": "daily",
                "total_articles": 0,
                "duplicate_articles": 0,
                "low_quality_articles": 0,
                "irrelevant_articles": 0,
                "language_distribution": {},
                "category_distribution": {},
                "active_feeds": 0,
                "failing_feeds": 0,
                "avg_feed_reliability": 0.0,
                "avg_processing_time": 0.0,
                "processing_error_rate": 0.0,
                "avg_article_age_hours": 0.0,
                "stale_articles_count": 0,
                "quality_issues": [],
                "recommendations": [],
            }

            # Calculate metrics (simplified version)
            cutoff_24h = report_date - timedelta(hours=24)

            # Total articles
            report_data["total_articles"] = (
                db.query(Article).filter(Article.created_at >= cutoff_24h).count()
            )

            # Low quality articles
            report_data["low_quality_articles"] = (
                db.query(Article)
                .filter(Article.created_at >= cutoff_24h, Article.quality_score < 0.4)
                .count()
            )

            # Irrelevant articles
            report_data["irrelevant_articles"] = (
                db.query(Article)
                .filter(
                    Article.created_at >= cutoff_24h,
                    Article.filtering_status == ProcessingStatus.FILTERED_OUT,
                )
                .count()
            )

            # Active feeds
            report_data["active_feeds"] = (
                db.query(NewsFeed).filter(NewsFeed.is_active == True).count()
            )

            # Create quality report record
            quality_report = DataQualityReport(**report_data)
            db.add(quality_report)
            db.commit()

        logger.info(
            "Data quality report generated",
            total_articles=report_data["total_articles"],
            low_quality_articles=report_data["low_quality_articles"],
        )

        return {
            "report_generated": True,
            "report_date": report_date.isoformat(),
            "total_articles": report_data["total_articles"],
            "quality_score": 1.0
            - (
                report_data["low_quality_articles"]
                / max(report_data["total_articles"], 1)
            ),
        }

    except Exception as exc:
        logger.error("Quality report generation failed", error=str(exc), exc_info=True)

        raise TaskError(f"Quality report generation failed: {str(exc)}") from exc
