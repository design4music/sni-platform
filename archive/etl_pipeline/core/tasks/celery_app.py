"""
Celery application configuration for Strategic Narrative Intelligence ETL Pipeline

This module sets up Celery for distributed task processing with Redis backend,
comprehensive error handling, and monitoring integration.
"""

from datetime import datetime
from typing import Any, Dict, List

import structlog
from celery import Celery, Task
from celery.exceptions import Ignore
from celery.signals import (beat_init, task_failure, task_postrun, task_prerun,
                            task_retry, worker_ready, worker_shutdown)
from kombu import Exchange, Queue

from ..config import get_config
from ..database import initialize_database
from ..exceptions import (RetryableError, is_retryable_error)
from ..monitoring import MetricsCollector

logger = structlog.get_logger(__name__)


class ETLTask(Task):
    """
    Custom Celery task class with enhanced error handling, retry logic,
    and monitoring integration.
    """

    # Default task configuration
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max
    retry_jitter = True

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.metrics_collector = MetricsCollector(self.config.monitoring)

    def retry(
        self,
        args=None,
        kwargs=None,
        exc=None,
        throw=True,
        eta=None,
        countdown=None,
        max_retries=None,
        **options,
    ):
        """Enhanced retry method with intelligent backoff"""

        # Determine if error should be retried
        if exc and not is_retryable_error(exc):
            logger.error(
                "Non-retryable error encountered, failing task",
                task_name=self.name,
                task_id=self.request.id,
                error=str(exc),
            )
            raise Ignore()

        # Get retry parameters from exception if available
        if isinstance(exc, RetryableError):
            max_retries = max_retries or exc.max_retries
            if countdown is None and eta is None:
                countdown = exc.retry_delay * (2**self.request.retries)

        # Log retry attempt
        logger.warning(
            "Task retry scheduled",
            task_name=self.name,
            task_id=self.request.id,
            retry_count=self.request.retries + 1,
            max_retries=max_retries or self.max_retries,
            countdown=countdown,
            error=str(exc) if exc else None,
        )

        # Record retry metrics
        self.metrics_collector.record_task_retry(
            task_name=self.name,
            retry_count=self.request.retries + 1,
            error_type=type(exc).__name__ if exc else "Unknown",
        )

        return super().retry(
            args=args,
            kwargs=kwargs,
            exc=exc,
            throw=throw,
            eta=eta,
            countdown=countdown,
            max_retries=max_retries,
            **options,
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(
            "Task completed successfully",
            task_name=self.name,
            task_id=task_id,
            duration=getattr(self, "_task_duration", None),
        )

        self.metrics_collector.record_task_success(
            task_name=self.name, duration=getattr(self, "_task_duration", 0)
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails permanently"""
        logger.error(
            "Task failed permanently",
            task_name=self.name,
            task_id=task_id,
            error=str(exc),
            traceback=str(einfo),
        )

        self.metrics_collector.record_task_failure(
            task_name=self.name,
            error_type=type(exc).__name__,
            retry_count=self.request.retries,
        )

        # Send alert for critical task failures
        if self.name in ["etl.run_daily_pipeline", "etl.ingest_feed"]:
            # This would send an alert through the alerting system
            pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(
            "Task retry attempted",
            task_name=self.name,
            task_id=task_id,
            retry_count=self.request.retries,
            error=str(exc),
        )


def create_celery_app() -> Celery:
    """
    Create and configure Celery application with optimal settings
    for the ETL pipeline workload.
    """
    config = get_config()

    # Create Celery app
    app = Celery("narrative_intelligence_etl")

    # Configure broker and backend
    app.conf.update(
        # Broker settings
        broker_url=config.redis.url,
        result_backend=config.redis.url,
        # Task serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # Task execution settings
        task_track_started=True,
        task_time_limit=7200,  # 2 hours hard limit
        task_soft_time_limit=6900,  # 1h 55m soft limit
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Worker settings
        worker_prefetch_multiplier=1,  # Prevent memory issues with large tasks
        worker_max_tasks_per_child=1000,  # Restart workers periodically
        worker_disable_rate_limits=False,
        # Result settings
        result_expires=3600,  # 1 hour
        result_compression="gzip",
        task_compression="gzip",
        # Routing and queues
        task_routes={
            "etl.ingest_feed": {"queue": "ingestion"},
            "etl.process_content": {"queue": "processing"},
            "etl.ml_integration": {"queue": "ml_pipeline"},
            "etl.trending_analysis": {"queue": "realtime"},
            "etl.run_daily_pipeline": {"queue": "orchestration"},
            "etl.health_check": {"queue": "monitoring"},
            "etl.data_quality_check": {"queue": "monitoring"},
            "etl.cleanup_task": {"queue": "maintenance"},
        },
        # Queue definitions
        task_queues=(
            Queue(
                "ingestion",
                Exchange("ingestion"),
                routing_key="ingestion",
                queue_arguments={"x-max-priority": 5},
            ),
            Queue(
                "processing",
                Exchange("processing"),
                routing_key="processing",
                queue_arguments={"x-max-priority": 5},
            ),
            Queue(
                "ml_pipeline",
                Exchange("ml_pipeline"),
                routing_key="ml_pipeline",
                queue_arguments={"x-max-priority": 3},
            ),
            Queue(
                "realtime",
                Exchange("realtime"),
                routing_key="realtime",
                queue_arguments={"x-max-priority": 10},
            ),
            Queue(
                "orchestration",
                Exchange("orchestration"),
                routing_key="orchestration",
                queue_arguments={"x-max-priority": 10},
            ),
            Queue(
                "monitoring",
                Exchange("monitoring"),
                routing_key="monitoring",
                queue_arguments={"x-max-priority": 7},
            ),
            Queue(
                "maintenance",
                Exchange("maintenance"),
                routing_key="maintenance",
                queue_arguments={"x-max-priority": 1},
            ),
        ),
        # Beat schedule for periodic tasks
        beat_schedule={
            "daily-etl-pipeline": {
                "task": "etl.run_daily_pipeline",
                "schedule": config.pipeline.daily_schedule_cron,
                "options": {"queue": "orchestration", "priority": 10},
            },
            "trending-analysis": {
                "task": "etl.trending_analysis",
                "schedule": 300.0,  # Every 5 minutes
                "options": {"queue": "realtime", "priority": 8},
            },
            "health-check": {
                "task": "etl.health_check",
                "schedule": config.monitoring.health_check_interval_seconds,
                "options": {"queue": "monitoring", "priority": 5},
            },
            "data-quality-check": {
                "task": "etl.data_quality_check",
                "schedule": 3600.0,  # Every hour
                "options": {"queue": "monitoring", "priority": 6},
            },
            "cleanup-old-data": {
                "task": "etl.cleanup_old_data",
                "schedule": 86400.0,  # Daily
                "options": {"queue": "maintenance", "priority": 1},
            },
            "generate-quality-report": {
                "task": "etl.generate_quality_report",
                "schedule": 86400.0,  # Daily
                "options": {"queue": "monitoring", "priority": 4},
            },
            # RSS Feed Ingestion Tasks
            "ingest-all-feeds": {
                "task": "etl.ingest_all_feeds",
                "schedule": 3600.0,  # Every hour
                "options": {"queue": "ingestion", "priority": 7},
            },
            "test-feed-connectivity": {
                "task": "etl.test_feed_connectivity",
                "schedule": 7200.0,  # Every 2 hours
                "options": {"queue": "monitoring", "priority": 3},
            },
        },
        # Error handling
        task_annotations={
            "*": {"rate_limit": "100/m"},  # Global rate limit
            "etl.ingest_feed": {"rate_limit": "50/m", "time_limit": 1800},
            "etl.process_content": {"rate_limit": "30/m", "time_limit": 3600},
            "etl.ml_integration": {"rate_limit": "10/m", "time_limit": 7200},
            "etl.trending_analysis": {"rate_limit": "20/m", "time_limit": 600},
        },
        # Monitoring and logging
        worker_send_task_events=True,
        task_send_sent_event=True,
        # Security (if needed)
        # worker_hijack_root_logger=False,
        # security=SecurityConfig(),
    )

    # Set custom task base class
    app.Task = ETLTask

    return app


# Create global Celery app instance
celery_app = create_celery_app()


# Celery signal handlers for monitoring and logging
@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
):
    """Called before task execution starts"""
    logger.info(
        "Task starting",
        task_name=task.name,
        task_id=task_id,
        args_count=len(args) if args else 0,
        kwargs_keys=list(kwargs.keys()) if kwargs else [],
    )

    # Record task start time for duration calculation
    task._task_start_time = datetime.utcnow()


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **kwds,
):
    """Called after task execution completes"""
    if hasattr(task, "_task_start_time"):
        duration = (datetime.utcnow() - task._task_start_time).total_seconds()
        task._task_duration = duration

        logger.info(
            "Task completed",
            task_name=task.name,
            task_id=task_id,
            state=state,
            duration=duration,
        )


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds
):
    """Called when task fails"""
    logger.error(
        "Task failed",
        task_name=sender.name if sender else "Unknown",
        task_id=task_id,
        exception=str(exception),
        exc_info=True,
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Called when task is retried"""
    logger.warning(
        "Task retry scheduled",
        task_name=sender.name if sender else "Unknown",
        task_id=task_id,
        reason=str(reason),
    )


@worker_ready.connect
def worker_ready_handler(sender=None, **kwds):
    """Called when worker is ready to receive tasks"""
    logger.info("Celery worker ready", worker_name=sender.hostname)

    # Initialize database connection
    try:
        config = get_config()
        initialize_database(config.database)
        logger.info("Database initialized for worker")
    except Exception as exc:
        logger.error("Failed to initialize database for worker", error=str(exc))


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwds):
    """Called when worker is shutting down"""
    logger.info("Celery worker shutting down", worker_name=sender.hostname)


@beat_init.connect
def beat_init_handler(sender=None, **kwds):
    """Called when Celery Beat scheduler starts"""
    logger.info("Celery Beat scheduler initialized")


# Task monitoring utilities
def get_active_tasks() -> List[Dict[str, Any]]:
    """Get list of currently active tasks"""
    inspect = celery_app.control.inspect()
    active_tasks = inspect.active()

    if not active_tasks:
        return []

    tasks = []
    for worker, worker_tasks in active_tasks.items():
        for task in worker_tasks:
            tasks.append(
                {
                    "worker": worker,
                    "task_id": task["id"],
                    "task_name": task["name"],
                    "args": task["args"],
                    "kwargs": task["kwargs"],
                    "time_start": task["time_start"],
                }
            )

    return tasks


def get_scheduled_tasks() -> List[Dict[str, Any]]:
    """Get list of scheduled tasks"""
    inspect = celery_app.control.inspect()
    scheduled_tasks = inspect.scheduled()

    if not scheduled_tasks:
        return []

    tasks = []
    for worker, worker_tasks in scheduled_tasks.items():
        for task in worker_tasks:
            tasks.append(
                {
                    "worker": worker,
                    "task_id": task["request"]["id"],
                    "task_name": task["request"]["task"],
                    "eta": task["eta"],
                    "priority": task["request"].get("priority", 0),
                }
            )

    return tasks


def get_worker_stats() -> Dict[str, Any]:
    """Get worker statistics"""
    inspect = celery_app.control.inspect()
    stats = inspect.stats()

    if not stats:
        return {}

    return {
        "workers": stats,
        "total_workers": len(stats),
        "total_tasks_completed": sum(
            worker_stats.get("total", {}).values() for worker_stats in stats.values()
        ),
    }


def cancel_task(task_id: str, terminate: bool = False) -> bool:
    """Cancel a running task"""
    try:
        celery_app.control.revoke(task_id, terminate=terminate)
        logger.info("Task cancelled", task_id=task_id, terminate=terminate)
        return True
    except Exception as exc:
        logger.error("Failed to cancel task", task_id=task_id, error=str(exc))
        return False


def purge_queue(queue_name: str) -> int:
    """Purge all tasks from a queue"""
    try:
        purged_count = celery_app.control.purge()
        logger.info("Queue purged", queue=queue_name, purged_count=purged_count)
        return purged_count
    except Exception as exc:
        logger.error("Failed to purge queue", queue=queue_name, error=str(exc))
        return 0


# Health check utilities
def check_celery_health() -> Dict[str, Any]:
    """Perform comprehensive Celery health check"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "checks": {},
    }

    try:
        # Check if any workers are available
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if not stats:
            health_status["status"] = "unhealthy"
            health_status["checks"]["workers"] = "No workers available"
        else:
            health_status["checks"]["workers"] = f"{len(stats)} workers active"

        # Check broker connectivity
        try:
            # This will raise an exception if broker is not available
            celery_app.control.inspect().ping()
            health_status["checks"]["broker"] = "Connected"
        except Exception as exc:
            health_status["status"] = "degraded"
            health_status["checks"]["broker"] = f"Connection error: {str(exc)}"

        # Check active tasks
        active_tasks = get_active_tasks()
        health_status["checks"]["active_tasks"] = len(active_tasks)

        # Check for stuck tasks (running more than 2 hours)
        stuck_tasks = []
        current_time = datetime.utcnow()

        for task in active_tasks:
            if task.get("time_start"):
                start_time = datetime.fromisoformat(task["time_start"])
                if (current_time - start_time).total_seconds() > 7200:  # 2 hours
                    stuck_tasks.append(task["task_id"])

        if stuck_tasks:
            health_status["status"] = "degraded"
            health_status["checks"]["stuck_tasks"] = len(stuck_tasks)
        else:
            health_status["checks"]["stuck_tasks"] = 0

    except Exception as exc:
        health_status["status"] = "unhealthy"
        health_status["checks"]["error"] = str(exc)

    return health_status


# Export main app
__all__ = [
    "celery_app",
    "ETLTask",
    "get_active_tasks",
    "get_worker_stats",
    "check_celery_health",
]
