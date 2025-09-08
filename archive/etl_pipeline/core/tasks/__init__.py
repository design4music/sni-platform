"""
Tasks module for Strategic Narrative Intelligence ETL Pipeline

This module provides Celery task definitions and orchestration
for the distributed ETL pipeline processing.
"""

from .celery_app import (ETLTask, celery_app, check_celery_health,
                         get_active_tasks, get_worker_stats)
from .pipeline_tasks import (cleanup_old_data, data_quality_check,
                             generate_quality_report, health_check,
                             ingest_feed, ml_integration_pipeline,
                             process_content_batch, run_daily_pipeline,
                             trending_analysis)

__all__ = [
    "celery_app",
    "ETLTask",
    "run_daily_pipeline",
    "ingest_feed",
    "process_content_batch",
    "ml_integration_pipeline",
    "trending_analysis",
    "health_check",
    "data_quality_check",
    "cleanup_old_data",
    "generate_quality_report",
    "get_active_tasks",
    "get_worker_stats",
    "check_celery_health",
]
