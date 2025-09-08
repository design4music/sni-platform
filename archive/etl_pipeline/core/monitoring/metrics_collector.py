"""
Metrics Collection System for Strategic Narrative Intelligence ETL Pipeline

This module provides comprehensive metrics collection, aggregation, and
export capabilities with Prometheus integration and custom business metrics.
"""

import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional, Union

import structlog
from prometheus_client import (CollectorRegistry, Counter,
                               Gauge, Histogram, Info, generate_latest)

from ..config import MonitoringConfig
from ..database import get_db_session
from ..database.models import (ProcessingStatus)
from ..exceptions import MetricsError

logger = structlog.get_logger(__name__)


@dataclass
class MetricValue:
    """Individual metric value with metadata"""

    name: str
    value: Union[float, int, str]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    help_text: str = ""


@dataclass
class PipelineMetrics:
    """Pipeline execution metrics container"""

    pipeline_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    feeds_processed: int = 0
    articles_ingested: int = 0
    articles_filtered: int = 0
    articles_processed: int = 0
    errors_count: int = 0
    processing_time_seconds: float = 0.0
    throughput_articles_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


class MetricsCollector:
    """
    Comprehensive metrics collection system with Prometheus integration,
    custom business metrics, and real-time monitoring capabilities.
    """

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Thread safety
        self._metrics_lock = Lock()

        # Prometheus registry and metrics
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()

        # Custom metrics storage
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metric_aggregates: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Performance tracking
        self.active_timers: Dict[str, float] = {}

        # Business metrics cache
        self.business_metrics_cache: Dict[str, Any] = {}
        self.cache_expiry = datetime.utcnow()

        logger.info(
            "Metrics collector initialized",
            enable_metrics=config.enable_metrics,
            metrics_port=config.metrics_port,
        )

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics definitions"""

        # Pipeline metrics
        self.pipeline_runs_total = Counter(
            "pipeline_runs_total",
            "Total number of pipeline runs",
            ["status", "pipeline_type"],
            registry=self.registry,
        )

        self.pipeline_duration_seconds = Histogram(
            "pipeline_duration_seconds",
            "Pipeline execution duration in seconds",
            ["pipeline_type", "status"],
            buckets=[30, 60, 300, 600, 1800, 3600, 7200, 14400],  # 30s to 4h
            registry=self.registry,
        )

        self.pipeline_articles_processed = Histogram(
            "pipeline_articles_processed",
            "Number of articles processed per pipeline run",
            ["pipeline_type"],
            buckets=[10, 50, 100, 500, 1000, 5000, 10000],
            registry=self.registry,
        )

        # Feed metrics
        self.feed_fetches_total = Counter(
            "feed_fetches_total",
            "Total number of feed fetch attempts",
            ["feed_id", "feed_type", "status"],
            registry=self.registry,
        )

        self.feed_articles_ingested = Counter(
            "feed_articles_ingested_total",
            "Total number of articles ingested from feeds",
            ["feed_id", "feed_type", "language"],
            registry=self.registry,
        )

        self.feed_fetch_duration_seconds = Histogram(
            "feed_fetch_duration_seconds",
            "Feed fetch duration in seconds",
            ["feed_id", "feed_type"],
            buckets=[1, 5, 10, 30, 60, 120, 300],
            registry=self.registry,
        )

        # Processing metrics
        self.articles_processed_total = Counter(
            "articles_processed_total",
            "Total number of articles processed",
            ["processing_stage", "status", "language"],
            registry=self.registry,
        )

        self.processing_duration_seconds = Histogram(
            "processing_duration_seconds",
            "Article processing duration in seconds",
            ["processing_stage", "language"],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry,
        )

        self.content_quality_score = Histogram(
            "content_quality_score",
            "Content quality scores",
            ["language", "category"],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry,
        )

        self.content_relevance_score = Histogram(
            "content_relevance_score",
            "Content relevance scores",
            ["language", "category"],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry,
        )

        # NER metrics
        self.entities_extracted_total = Counter(
            "entities_extracted_total",
            "Total number of entities extracted",
            ["entity_type", "language"],
            registry=self.registry,
        )

        self.entity_extraction_confidence = Histogram(
            "entity_extraction_confidence",
            "Entity extraction confidence scores",
            ["entity_type", "language"],
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
            registry=self.registry,
        )

        # Task execution metrics
        self.task_executions_total = Counter(
            "task_executions_total",
            "Total number of task executions",
            ["task_name", "status"],
            registry=self.registry,
        )

        self.task_duration_seconds = Histogram(
            "task_duration_seconds",
            "Task execution duration in seconds",
            ["task_name"],
            buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600],
            registry=self.registry,
        )

        self.task_retries_total = Counter(
            "task_retries_total",
            "Total number of task retries",
            ["task_name", "error_type"],
            registry=self.registry,
        )

        # System metrics
        self.active_feeds = Gauge(
            "active_feeds", "Number of active news feeds", registry=self.registry
        )

        self.database_connections = Gauge(
            "database_connections",
            "Number of active database connections",
            registry=self.registry,
        )

        self.redis_connections = Gauge(
            "redis_connections",
            "Number of active Redis connections",
            registry=self.registry,
        )

        # Business metrics
        self.trending_topics_detected = Counter(
            "trending_topics_detected_total",
            "Total number of trending topics detected",
            ["time_window"],
            registry=self.registry,
        )

        self.content_categories_distribution = Counter(
            "content_categories_total",
            "Distribution of content categories",
            ["category", "language"],
            registry=self.registry,
        )

        # Error metrics
        self.errors_total = Counter(
            "errors_total",
            "Total number of errors",
            ["error_type", "component", "severity"],
            registry=self.registry,
        )

        # System info
        self.system_info = Info(
            "etl_pipeline_info",
            "ETL pipeline system information",
            registry=self.registry,
        )

        # Set initial system info
        self.system_info.info(
            {
                "version": "1.0.0",
                "environment": self.config.log_level,
                "monitoring_enabled": str(self.config.enable_metrics),
            }
        )

    @contextmanager
    def timer(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        timer_id = f"{metric_name}_{id(start_time)}"
        self.active_timers[timer_id] = start_time

        try:
            yield
        finally:
            duration = time.time() - start_time
            self.active_timers.pop(timer_id, None)

            # Record timing metric
            self.record_timing(metric_name, duration, labels or {})

    def record_timing(self, metric_name: str, duration: float, labels: Dict[str, str]):
        """Record timing metric"""
        with self._metrics_lock:
            # Store in custom metrics
            metric_value = MetricValue(
                name=f"{metric_name}_duration",
                value=duration,
                labels=labels,
                help_text=f"Duration for {metric_name} operation",
            )
            self.custom_metrics[metric_name].append(metric_value)

            # Update aggregates
            if metric_name not in self.metric_aggregates:
                self.metric_aggregates[metric_name] = {
                    "count": 0,
                    "sum": 0.0,
                    "min": float("inf"),
                    "max": 0.0,
                    "avg": 0.0,
                }

            agg = self.metric_aggregates[metric_name]
            agg["count"] += 1
            agg["sum"] += duration
            agg["min"] = min(agg["min"], duration)
            agg["max"] = max(agg["max"], duration)
            agg["avg"] = agg["sum"] / agg["count"]

    def record_counter(
        self, metric_name: str, value: int = 1, labels: Dict[str, str] = None
    ):
        """Record counter metric"""
        with self._metrics_lock:
            metric_value = MetricValue(
                name=metric_name,
                value=value,
                labels=labels or {},
                help_text=f"Counter for {metric_name}",
            )
            self.custom_metrics[metric_name].append(metric_value)

    def record_gauge(
        self, metric_name: str, value: Union[float, int], labels: Dict[str, str] = None
    ):
        """Record gauge metric"""
        with self._metrics_lock:
            metric_value = MetricValue(
                name=metric_name,
                value=value,
                labels=labels or {},
                help_text=f"Gauge for {metric_name}",
            )
            self.custom_metrics[metric_name].append(metric_value)

    def record_pipeline_execution(self, metrics: PipelineMetrics):
        """Record comprehensive pipeline execution metrics"""
        labels = {"pipeline_id": metrics.pipeline_id}

        # Prometheus metrics
        if metrics.end_time:
            status = "success"
            duration = metrics.processing_time_seconds
        else:
            status = "running"
            duration = (datetime.utcnow() - metrics.start_time).total_seconds()

        self.pipeline_runs_total.labels(status=status, pipeline_type="daily").inc()

        if metrics.end_time:  # Only record duration for completed pipelines
            self.pipeline_duration_seconds.labels(
                pipeline_type="daily", status=status
            ).observe(duration)

            self.pipeline_articles_processed.labels(pipeline_type="daily").observe(
                metrics.articles_processed
            )

        # Custom metrics
        pipeline_metrics = [
            ("pipeline_feeds_processed", metrics.feeds_processed),
            ("pipeline_articles_ingested", metrics.articles_ingested),
            ("pipeline_articles_filtered", metrics.articles_filtered),
            ("pipeline_articles_processed", metrics.articles_processed),
            ("pipeline_errors_count", metrics.errors_count),
            ("pipeline_throughput_aps", metrics.throughput_articles_per_second),
            ("pipeline_memory_usage_mb", metrics.memory_usage_mb),
            ("pipeline_cpu_usage_percent", metrics.cpu_usage_percent),
        ]

        for metric_name, value in pipeline_metrics:
            self.record_gauge(metric_name, value, labels)

        logger.info(
            "Pipeline metrics recorded",
            pipeline_id=metrics.pipeline_id,
            duration=duration,
            articles_processed=metrics.articles_processed,
        )

    def record_feed_ingestion(
        self,
        feed_id: str,
        feed_type: str,
        language: str,
        articles_count: int,
        duration: float,
        success: bool,
    ):
        """Record feed ingestion metrics"""
        status = "success" if success else "failure"

        # Prometheus metrics
        self.feed_fetches_total.labels(
            feed_id=feed_id, feed_type=feed_type, status=status
        ).inc()

        if success:
            self.feed_articles_ingested.labels(
                feed_id=feed_id, feed_type=feed_type, language=language
            ).inc(articles_count)

        self.feed_fetch_duration_seconds.labels(
            feed_id=feed_id, feed_type=feed_type
        ).observe(duration)

        # Custom metrics
        labels = {
            "feed_id": feed_id,
            "feed_type": feed_type,
            "language": language,
            "status": status,
        }

        self.record_counter("feed_ingestion_attempts", 1, labels)
        self.record_gauge("feed_articles_ingested", articles_count, labels)
        self.record_timing("feed_ingestion", duration, labels)

    def record_content_processing(
        self,
        articles_processed: int,
        language: str,
        processing_stage: str,
        duration: float,
        success: bool,
        quality_scores: List[float] = None,
        relevance_scores: List[float] = None,
    ):
        """Record content processing metrics"""
        status = "success" if success else "failure"

        # Prometheus metrics
        self.articles_processed_total.labels(
            processing_stage=processing_stage, status=status, language=language
        ).inc(articles_processed)

        self.processing_duration_seconds.labels(
            processing_stage=processing_stage, language=language
        ).observe(duration)

        # Record quality and relevance scores
        if quality_scores:
            for score in quality_scores:
                self.content_quality_score.labels(
                    language=language, category="general"  # Could be more specific
                ).observe(score)

        if relevance_scores:
            for score in relevance_scores:
                self.content_relevance_score.labels(
                    language=language, category="general"
                ).observe(score)

        # Custom metrics
        labels = {
            "processing_stage": processing_stage,
            "language": language,
            "status": status,
        }

        self.record_counter("content_processing_attempts", 1, labels)
        self.record_gauge("content_articles_processed", articles_processed, labels)
        self.record_timing("content_processing", duration, labels)

    def record_entity_extraction(
        self,
        entities_by_type: Dict[str, int],
        language: str,
        confidence_scores: Dict[str, List[float]],
    ):
        """Record NER metrics"""

        # Prometheus metrics
        for entity_type, count in entities_by_type.items():
            self.entities_extracted_total.labels(
                entity_type=entity_type, language=language
            ).inc(count)

            # Record confidence scores for this entity type
            if entity_type in confidence_scores:
                for score in confidence_scores[entity_type]:
                    self.entity_extraction_confidence.labels(
                        entity_type=entity_type, language=language
                    ).observe(score)

        # Custom metrics
        labels = {"language": language}
        total_entities = sum(entities_by_type.values())

        self.record_gauge("entities_extracted_total", total_entities, labels)

        for entity_type, count in entities_by_type.items():
            type_labels = {**labels, "entity_type": entity_type}
            self.record_gauge("entities_by_type", count, type_labels)

    def record_task_execution(self, task_name: str, duration: float, success: bool):
        """Record task execution metrics"""
        status = "success" if success else "failure"

        # Prometheus metrics
        self.task_executions_total.labels(task_name=task_name, status=status).inc()

        self.task_duration_seconds.labels(task_name=task_name).observe(duration)

        # Custom metrics
        labels = {"task_name": task_name, "status": status}
        self.record_counter("task_executions", 1, labels)
        self.record_timing("task_execution", duration, labels)

    def record_task_retry(self, task_name: str, retry_count: int, error_type: str):
        """Record task retry metrics"""

        # Prometheus metrics
        self.task_retries_total.labels(task_name=task_name, error_type=error_type).inc()

        # Custom metrics
        labels = {
            "task_name": task_name,
            "error_type": error_type,
            "retry_count": str(retry_count),
        }
        self.record_counter("task_retries", 1, labels)

    def record_task_success(self, task_name: str, duration: float):
        """Record successful task completion"""
        self.record_task_execution(task_name, duration, success=True)

    def record_task_failure(self, task_name: str, error_type: str, retry_count: int):
        """Record task failure"""
        self.record_task_execution(task_name, 0.0, success=False)

        # Prometheus error metrics
        self.errors_total.labels(
            error_type=error_type, component="task_execution", severity="error"
        ).inc()

    def record_trending_topic(self, topic_count: int, time_window: str):
        """Record trending topic detection"""

        # Prometheus metrics
        self.trending_topics_detected.labels(time_window=time_window).inc(topic_count)

        # Custom metrics
        labels = {"time_window": time_window}
        self.record_gauge("trending_topics_count", topic_count, labels)

    def record_content_categories(self, categories: Dict[str, int], language: str):
        """Record content category distribution"""

        # Prometheus metrics
        for category, count in categories.items():
            self.content_categories_distribution.labels(
                category=category, language=language
            ).inc(count)

        # Custom metrics
        for category, count in categories.items():
            labels = {"category": category, "language": language}
            self.record_gauge("content_category_count", count, labels)

    def record_error(self, error_type: str, component: str, severity: str = "error"):
        """Record error occurrence"""

        # Prometheus metrics
        self.errors_total.labels(
            error_type=error_type, component=component, severity=severity
        ).inc()

        # Custom metrics
        labels = {
            "error_type": error_type,
            "component": component,
            "severity": severity,
        }
        self.record_counter("errors", 1, labels)

    def update_system_gauges(self):
        """Update system-level gauge metrics"""
        try:
            with get_db_session() as db:
                # Active feeds count
                active_feeds_count = db.execute(
                    "SELECT COUNT(*) FROM news_feeds WHERE is_active = true"
                ).scalar()
                self.active_feeds.set(active_feeds_count)

                # Database connection info would require specific queries
                # For now, we'll use placeholder values
                self.database_connections.set(10)  # Would be actual connection count
                self.redis_connections.set(5)  # Would be actual Redis connections

        except Exception as exc:
            logger.error("Failed to update system gauges", error=str(exc))

    def get_business_metrics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get business-level metrics with caching"""
        current_time = datetime.utcnow()

        # Check cache validity (refresh every 5 minutes)
        if not force_refresh and current_time < self.cache_expiry:
            return self.business_metrics_cache

        try:
            with get_db_session() as db:
                # Calculate business metrics
                cutoff_24h = current_time - timedelta(hours=24)
                cutoff_7d = current_time - timedelta(days=7)

                metrics = {
                    "timestamp": current_time.isoformat(),
                    # Article metrics
                    "articles_last_24h": db.execute(
                        "SELECT COUNT(*) FROM articles WHERE created_at >= %s",
                        (cutoff_24h,),
                    ).scalar(),
                    "articles_last_7d": db.execute(
                        "SELECT COUNT(*) FROM articles WHERE created_at >= %s",
                        (cutoff_7d,),
                    ).scalar(),
                    # Processing metrics
                    "processing_success_rate_24h": self._calculate_processing_success_rate(
                        cutoff_24h
                    ),
                    # Quality metrics
                    "avg_quality_score_24h": db.execute(
                        "SELECT AVG(quality_score) FROM articles WHERE created_at >= %s AND quality_score IS NOT NULL",
                        (cutoff_24h,),
                    ).scalar()
                    or 0.0,
                    "avg_relevance_score_24h": db.execute(
                        "SELECT AVG(relevance_score) FROM articles WHERE created_at >= %s AND relevance_score IS NOT NULL",
                        (cutoff_24h,),
                    ).scalar()
                    or 0.0,
                    # Language distribution
                    "language_distribution_24h": self._get_language_distribution(
                        cutoff_24h
                    ),
                    # Category distribution
                    "category_distribution_24h": self._get_category_distribution(
                        cutoff_24h
                    ),
                    # Feed performance
                    "active_feeds_count": db.execute(
                        "SELECT COUNT(*) FROM news_feeds WHERE is_active = true"
                    ).scalar(),
                    # Recent pipeline runs
                    "pipeline_runs_24h": db.execute(
                        "SELECT COUNT(*) FROM pipeline_runs WHERE started_at >= %s",
                        (cutoff_24h,),
                    ).scalar(),
                    # Trending topics
                    "trending_topics_24h": db.execute(
                        "SELECT COUNT(*) FROM trending_topics WHERE detected_at >= %s",
                        (cutoff_24h,),
                    ).scalar(),
                }

                # Cache results
                self.business_metrics_cache = metrics
                self.cache_expiry = current_time + timedelta(minutes=5)

                return metrics

        except Exception as exc:
            logger.error("Failed to calculate business metrics", error=str(exc))
            return self.business_metrics_cache or {}

    def _calculate_processing_success_rate(self, cutoff_time: datetime) -> float:
        """Calculate processing success rate"""
        try:
            with get_db_session() as db:
                total = db.execute(
                    "SELECT COUNT(*) FROM articles WHERE created_at >= %s",
                    (cutoff_time,),
                ).scalar()

                if total == 0:
                    return 0.0

                successful = db.execute(
                    "SELECT COUNT(*) FROM articles WHERE created_at >= %s AND processing_status = %s",
                    (cutoff_time, ProcessingStatus.COMPLETED.value),
                ).scalar()

                return successful / total

        except Exception:
            return 0.0

    def _get_language_distribution(self, cutoff_time: datetime) -> Dict[str, int]:
        """Get language distribution"""
        try:
            with get_db_session() as db:
                results = db.execute(
                    "SELECT language, COUNT(*) FROM articles WHERE created_at >= %s GROUP BY language",
                    (cutoff_time,),
                ).fetchall()

                return {row[0]: row[1] for row in results}

        except Exception:
            return {}

    def _get_category_distribution(self, cutoff_time: datetime) -> Dict[str, int]:
        """Get category distribution"""
        try:
            with get_db_session() as db:
                results = db.execute(
                    "SELECT primary_category, COUNT(*) FROM articles WHERE created_at >= %s AND primary_category IS NOT NULL GROUP BY primary_category",
                    (cutoff_time,),
                ).fetchall()

                return {row[0]: row[1] for row in results}

        except Exception:
            return {}

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        try:
            # Update system gauges before export
            self.update_system_gauges()
            return generate_latest(self.registry)
        except Exception as exc:
            logger.error("Failed to generate Prometheus metrics", error=str(exc))
            raise MetricsError(f"Failed to generate metrics: {str(exc)}") from exc

    def get_custom_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of custom metrics"""
        with self._metrics_lock:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics_count": len(self.custom_metrics),
                "total_data_points": sum(
                    len(deque_data) for deque_data in self.custom_metrics.values()
                ),
                "aggregates": dict(self.metric_aggregates),
                "active_timers": len(self.active_timers),
            }

            return summary

    def clear_expired_metrics(self, max_age_hours: int = 24):
        """Clear expired custom metrics to prevent memory leaks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        with self._metrics_lock:
            for metric_name, metric_deque in self.custom_metrics.items():
                # Filter out expired metrics
                while metric_deque and metric_deque[0].timestamp < cutoff_time:
                    metric_deque.popleft()

        logger.debug("Expired metrics cleared", cutoff_time=cutoff_time.isoformat())

    def export_metrics_json(self) -> Dict[str, Any]:
        """Export all metrics in JSON format"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "prometheus_metrics_available": True,
            "custom_metrics_summary": self.get_custom_metrics_summary(),
            "business_metrics": self.get_business_metrics(),
            "system_status": {
                "metrics_collection_enabled": self.config.enable_metrics,
                "active_timers": len(self.active_timers),
                "cache_expiry": self.cache_expiry.isoformat(),
            },
        }
