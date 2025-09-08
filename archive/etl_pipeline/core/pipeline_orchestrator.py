"""
Strategic Narrative Intelligence ETL Pipeline Orchestrator

This module coordinates the entire ETL pipeline for processing global news feeds
with multilingual support, content filtering, and ML integration.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from celery import Celery
from redis import Redis
from sqlalchemy.orm import Session

from .config import PipelineConfig
from .database import get_db_session
from .exceptions import IngestionError, PipelineError, ProcessingError
from .monitoring import AlertManager, MetricsCollector


class PipelineStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class PipelineMetrics:
    """Pipeline execution metrics"""

    start_time: datetime
    end_time: Optional[datetime] = None
    feeds_processed: int = 0
    articles_ingested: int = 0
    articles_filtered: int = 0
    articles_processed: int = 0
    errors_count: int = 0
    processing_time_seconds: float = 0.0
    throughput_articles_per_second: float = 0.0


class PipelineOrchestrator:
    """
    Main orchestrator for the Strategic Narrative Intelligence ETL pipeline.

    Coordinates daily ingestion, processing, and ML integration with comprehensive
    monitoring, error handling, and retry mechanisms.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.metrics_collector = MetricsCollector(config.monitoring)
        self.alert_manager = AlertManager(config.alerting)

        # Initialize external services
        self.celery_app = Celery(
            "narrative_intelligence_etl",
            broker=config.redis.url,
            backend=config.redis.url,
        )
        self.redis_client = Redis.from_url(config.redis.url)

        # Pipeline state
        self.status = PipelineStatus.IDLE
        self.current_metrics = None
        self.pipeline_id = None

        self._setup_celery_config()
        self._register_tasks()

    def _setup_celery_config(self):
        """Configure Celery for optimal task orchestration"""
        self.celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            task_time_limit=3600,  # 1 hour max per task
            task_soft_time_limit=3300,  # 55 minutes soft limit
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            worker_disable_rate_limits=False,
            task_compression="gzip",
            result_compression="gzip",
            task_routes={
                "etl.ingest_feed": {"queue": "ingestion"},
                "etl.process_content": {"queue": "processing"},
                "etl.ml_integration": {"queue": "ml_pipeline"},
                "etl.trending_analysis": {"queue": "realtime"},
            },
            beat_schedule={
                "daily-etl-pipeline": {
                    "task": "etl.run_daily_pipeline",
                    "schedule": self.config.pipeline.daily_schedule,
                },
                "trending-analysis": {
                    "task": "etl.run_trending_analysis",
                    "schedule": 300.0,  # Every 5 minutes
                },
                "health-check": {
                    "task": "etl.health_check",
                    "schedule": 60.0,  # Every minute
                },
            },
        )

    def _register_tasks(self):
        """Register Celery tasks for pipeline operations"""

        @self.celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
        def run_daily_pipeline(self, pipeline_config: Dict[str, Any]):
            """Execute the complete daily ETL pipeline"""
            try:
                return asyncio.run(self.execute_daily_pipeline())
            except Exception as exc:
                self.logger.error("Daily pipeline execution failed", error=str(exc))
                self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

        @self.celery_app.task(bind=True, max_retries=5, default_retry_delay=60)
        def ingest_feed(self, feed_config: Dict[str, Any]):
            """Ingest articles from a single news feed"""
            from .ingestion import FeedIngestor

            try:
                ingestor = FeedIngestor(self.config)
                return ingestor.ingest_feed(feed_config)
            except IngestionError as exc:
                self.logger.warning(
                    "Feed ingestion failed",
                    feed_id=feed_config.get("id"),
                    error=str(exc),
                )
                self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

        @self.celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
        def process_content(self, article_ids: List[str]):
            """Process content filtering and NER for articles"""
            from .processing import ContentProcessor

            try:
                processor = ContentProcessor(self.config)
                return processor.process_articles(article_ids)
            except ProcessingError as exc:
                self.logger.error(
                    "Content processing failed", article_ids=article_ids, error=str(exc)
                )
                self.retry(exc=exc, countdown=120 * (self.request.retries + 1))

        @self.celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
        def ml_integration(self, processed_article_ids: List[str]):
            """Integrate with ML pipeline for clustering and generation"""
            from .ml_integration import MLPipelineIntegrator

            try:
                integrator = MLPipelineIntegrator(self.config)
                return integrator.process_articles(processed_article_ids)
            except Exception as exc:
                self.logger.error(
                    "ML integration failed",
                    article_ids=processed_article_ids,
                    error=str(exc),
                )
                self.retry(exc=exc, countdown=300 * (self.request.retries + 1))

        @self.celery_app.task(bind=True)
        def run_trending_analysis(self):
            """Run real-time trending analysis"""
            from .trending import TrendingAnalyzer

            try:
                analyzer = TrendingAnalyzer(self.config)
                return analyzer.analyze_trends()
            except Exception as exc:
                self.logger.error("Trending analysis failed", error=str(exc))
                raise

        @self.celery_app.task
        def health_check():
            """Perform system health check"""
            return self.perform_health_check()

    async def execute_daily_pipeline(self) -> Dict[str, Any]:
        """
        Execute the complete daily ETL pipeline within the 4-hour window.

        Returns:
            Dict containing pipeline execution results and metrics
        """
        pipeline_start = datetime.utcnow()
        self.pipeline_id = f"pipeline_{pipeline_start.strftime('%Y%m%d_%H%M%S')}"

        self.logger.info("Starting daily ETL pipeline", pipeline_id=self.pipeline_id)
        self.status = PipelineStatus.RUNNING

        # Initialize metrics
        self.current_metrics = PipelineMetrics(start_time=pipeline_start)

        try:
            # Phase 1: Feed Ingestion (parallel processing)
            ingestion_results = await self._execute_ingestion_phase()

            # Phase 2: Content Processing (batch processing)
            processing_results = await self._execute_processing_phase(ingestion_results)

            # Phase 3: ML Integration (sequential processing)
            ml_results = await self._execute_ml_integration_phase(processing_results)

            # Phase 4: Finalization and cleanup
            await self._finalize_pipeline()

            # Update metrics
            self.current_metrics.end_time = datetime.utcnow()
            self.current_metrics.processing_time_seconds = (
                self.current_metrics.end_time - self.current_metrics.start_time
            ).total_seconds()

            if self.current_metrics.processing_time_seconds > 0:
                self.current_metrics.throughput_articles_per_second = (
                    self.current_metrics.articles_processed
                    / self.current_metrics.processing_time_seconds
                )

            self.status = PipelineStatus.COMPLETED

            # Send success metrics and alerts
            await self._send_completion_metrics()

            return {
                "pipeline_id": self.pipeline_id,
                "status": "completed",
                "metrics": self.current_metrics.__dict__,
                "ingestion_results": ingestion_results,
                "processing_results": processing_results,
                "ml_results": ml_results,
            }

        except Exception as exc:
            self.status = PipelineStatus.ERROR
            self.logger.error(
                "Pipeline execution failed",
                pipeline_id=self.pipeline_id,
                error=str(exc),
                exc_info=True,
            )

            # Send error alerts
            await self.alert_manager.send_alert(
                "pipeline_failure",
                f"Daily ETL pipeline {self.pipeline_id} failed: {str(exc)}",
                severity="critical",
            )

            raise PipelineError(f"Pipeline execution failed: {str(exc)}") from exc

    async def _execute_ingestion_phase(self) -> Dict[str, Any]:
        """Execute parallel feed ingestion"""
        self.logger.info("Starting ingestion phase", pipeline_id=self.pipeline_id)

        # Get active feeds from configuration
        active_feeds = await self._get_active_feeds()
        self.current_metrics.feeds_processed = len(active_feeds)

        # Create ingestion tasks
        ingestion_tasks = []
        for feed in active_feeds:
            task = self.celery_app.send_task(
                "etl.ingest_feed",
                args=[feed],
                queue="ingestion",
                routing_key="ingestion",
            )
            ingestion_tasks.append(task)

        # Wait for all ingestion tasks with timeout
        results = []
        failed_feeds = []

        for i, task in enumerate(ingestion_tasks):
            try:
                result = task.get(timeout=1800)  # 30 minute timeout per feed
                results.append(result)
                self.current_metrics.articles_ingested += result.get(
                    "articles_count", 0
                )
            except Exception as exc:
                self.logger.error(
                    "Feed ingestion failed",
                    feed_id=active_feeds[i].get("id"),
                    error=str(exc),
                )
                failed_feeds.append(active_feeds[i])
                self.current_metrics.errors_count += 1

        # Alert on failed feeds
        if failed_feeds:
            await self.alert_manager.send_alert(
                "ingestion_failures",
                f"Failed to ingest {len(failed_feeds)} feeds: {[f['id'] for f in failed_feeds]}",
                severity="warning",
            )

        return {
            "successful_feeds": len(results),
            "failed_feeds": len(failed_feeds),
            "total_articles": self.current_metrics.articles_ingested,
            "results": results,
        }

    async def _execute_processing_phase(
        self, ingestion_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute content processing in batches"""
        self.logger.info("Starting processing phase", pipeline_id=self.pipeline_id)

        # Get article IDs that need processing
        with get_db_session() as db:
            article_ids = await self._get_unprocessed_articles(db)

        if not article_ids:
            self.logger.info("No articles to process")
            return {"processed_articles": 0}

        # Process in batches to manage memory and performance
        batch_size = self.config.pipeline.processing_batch_size
        processing_tasks = []

        for i in range(0, len(article_ids), batch_size):
            batch = article_ids[i : i + batch_size]
            task = self.celery_app.send_task(
                "etl.process_content",
                args=[batch],
                queue="processing",
                routing_key="processing",
            )
            processing_tasks.append(task)

        # Wait for processing tasks
        processed_count = 0
        failed_batches = 0

        for task in processing_tasks:
            try:
                result = task.get(timeout=3600)  # 1 hour timeout per batch
                processed_count += result.get("processed_count", 0)
                self.current_metrics.articles_filtered += result.get(
                    "filtered_count", 0
                )
            except Exception as exc:
                self.logger.error("Content processing batch failed", error=str(exc))
                failed_batches += 1
                self.current_metrics.errors_count += 1

        self.current_metrics.articles_processed = processed_count

        return {
            "processed_articles": processed_count,
            "filtered_articles": self.current_metrics.articles_filtered,
            "failed_batches": failed_batches,
        }

    async def _execute_ml_integration_phase(
        self, processing_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute ML pipeline integration"""
        self.logger.info("Starting ML integration phase", pipeline_id=self.pipeline_id)

        # Get processed articles ready for ML
        with get_db_session() as db:
            processed_article_ids = await self._get_ml_ready_articles(db)

        if not processed_article_ids:
            self.logger.info("No articles ready for ML integration")
            return {"ml_processed_articles": 0}

        # Send to ML pipeline
        ml_task = self.celery_app.send_task(
            "etl.ml_integration",
            args=[processed_article_ids],
            queue="ml_pipeline",
            routing_key="ml_pipeline",
        )

        try:
            ml_result = ml_task.get(timeout=7200)  # 2 hour timeout for ML processing
            return ml_result
        except Exception as exc:
            self.logger.error("ML integration failed", error=str(exc))
            self.current_metrics.errors_count += 1

            # ML failure shouldn't stop the pipeline, but should alert
            await self.alert_manager.send_alert(
                "ml_integration_failure",
                f"ML integration failed for pipeline {self.pipeline_id}: {str(exc)}",
                severity="warning",
            )

            return {"ml_processed_articles": 0, "error": str(exc)}

    async def _finalize_pipeline(self):
        """Finalize pipeline execution and cleanup"""
        self.logger.info("Finalizing pipeline", pipeline_id=self.pipeline_id)

        # Update pipeline status in database
        with get_db_session() as db:
            await self._update_pipeline_status(db, "completed")

        # Cleanup temporary data
        await self._cleanup_temporary_data()

        # Update cache with latest processed data
        await self._update_cache()

    async def _get_active_feeds(self) -> List[Dict[str, Any]]:
        """Get list of active news feeds from configuration"""
        with get_db_session() as db:
            # This would fetch from database or config
            # For now, return configured feeds
            return self.config.feeds.active_feeds

    async def _get_unprocessed_articles(self, db: Session) -> List[str]:
        """Get article IDs that need processing"""
        # Implementation would query database for unprocessed articles
        pass

    async def _get_ml_ready_articles(self, db: Session) -> List[str]:
        """Get article IDs ready for ML processing"""
        # Implementation would query database for processed articles
        pass

    async def _update_pipeline_status(self, db: Session, status: str):
        """Update pipeline execution status in database"""
        # Implementation would update pipeline run record
        pass

    async def _cleanup_temporary_data(self):
        """Clean up temporary processing data"""
        # Implementation would clean up temp files, cache entries, etc.
        pass

    async def _update_cache(self):
        """Update Redis cache with latest processed data"""
        # Implementation would update cache with new articles, trends, etc.
        pass

    async def _send_completion_metrics(self):
        """Send pipeline completion metrics"""
        if self.current_metrics:
            await self.metrics_collector.record_pipeline_execution(self.current_metrics)

            # Send success alert if processing took too long
            if self.current_metrics.processing_time_seconds > 14400:  # 4 hours
                await self.alert_manager.send_alert(
                    "pipeline_slow",
                    f"Pipeline {self.pipeline_id} took {self.current_metrics.processing_time_seconds/3600:.1f} hours",
                    severity="warning",
                )

    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline_status": self.status.value,
            "services": {},
        }

        # Check Redis connectivity
        try:
            self.redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as exc:
            health_status["services"]["redis"] = f"unhealthy: {str(exc)}"

        # Check database connectivity
        try:
            with get_db_session() as db:
                db.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as exc:
            health_status["services"]["database"] = f"unhealthy: {str(exc)}"

        # Check Celery workers
        try:
            worker_stats = self.celery_app.control.inspect().stats()
            if worker_stats:
                health_status["services"]["celery_workers"] = "healthy"
                health_status["worker_count"] = len(worker_stats)
            else:
                health_status["services"]["celery_workers"] = "no_workers"
        except Exception as exc:
            health_status["services"]["celery_workers"] = f"unhealthy: {str(exc)}"

        # Overall health
        unhealthy_services = [
            k for k, v in health_status["services"].items() if "unhealthy" in v
        ]
        health_status["overall_health"] = (
            "healthy" if not unhealthy_services else "degraded"
        )

        return health_status

    async def pause_pipeline(self) -> bool:
        """Pause the running pipeline"""
        if self.status == PipelineStatus.RUNNING:
            self.status = PipelineStatus.PAUSED
            self.logger.info("Pipeline paused", pipeline_id=self.pipeline_id)
            return True
        return False

    async def resume_pipeline(self) -> bool:
        """Resume a paused pipeline"""
        if self.status == PipelineStatus.PAUSED:
            self.status = PipelineStatus.RUNNING
            self.logger.info("Pipeline resumed", pipeline_id=self.pipeline_id)
            return True
        return False

    def get_current_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics"""
        return {
            "status": self.status.value,
            "pipeline_id": self.pipeline_id,
            "metrics": self.current_metrics.__dict__ if self.current_metrics else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
