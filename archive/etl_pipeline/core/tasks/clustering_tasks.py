"""
Clustering Tasks for Strategic Narrative Intelligence ETL Pipeline

Celery tasks for running the clustering workflow:
- CLUST-1 thematic grouping
- Narrative matching
- Complete clustering workflow

These tasks are designed to run on a schedule or be triggered manually.
"""

from datetime import datetime
from typing import Any, Dict

import structlog

from ...clustering import (run_clust1_clustering,
                           run_clustering_workflow)
from .celery_app import ETLTask, celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, base=ETLTask)
def run_complete_clustering_workflow(self, article_limit: int = 1000) -> Dict[str, Any]:
    """
    Run the complete clustering workflow:
    1. CLUST-1 thematic grouping
    2. Narrative matching

    Args:
        article_limit: Maximum number of articles to process

    Returns:
        Workflow results summary
    """
    task_start = datetime.utcnow()

    try:
        logger.info(
            "Starting complete clustering workflow task",
            task_id=self.request.id,
            article_limit=article_limit,
        )

        # Run the workflow
        import asyncio

        result = asyncio.run(run_clustering_workflow(article_limit))

        # Prepare return data
        return_data = {
            "task_id": self.request.id,
            "status": "completed",
            "clusters_created": result.clusters_created,
            "narratives_attached": result.narratives_attached,
            "narratives_created": result.narratives_created,
            "articles_processed": result.articles_processed,
            "processing_duration_seconds": result.processing_duration_seconds,
            "started_at": task_start.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Complete clustering workflow task completed",
            task_id=self.request.id,
            **return_data
        )

        return return_data

    except Exception as exc:
        duration = (datetime.utcnow() - task_start).total_seconds()

        logger.error(
            "Complete clustering workflow task failed",
            task_id=self.request.id,
            duration_seconds=duration,
            error=str(exc),
            exc_info=True,
        )

        # Re-raise for Celery retry mechanism
        raise


@celery_app.task(bind=True, base=ETLTask)
def run_clust1_only(self, article_limit: int = 1000) -> Dict[str, Any]:
    """
    Run only CLUST-1 thematic grouping without narrative matching

    Args:
        article_limit: Maximum number of articles to process

    Returns:
        CLUST-1 results summary
    """
    task_start = datetime.utcnow()

    try:
        logger.info(
            "Starting CLUST-1 only task",
            task_id=self.request.id,
            article_limit=article_limit,
        )

        # Run CLUST-1
        import asyncio

        clusters = asyncio.run(run_clust1_clustering(article_limit))

        # Calculate summary stats
        total_articles = sum(len(cluster.articles) for cluster in clusters)
        avg_cluster_size = total_articles / len(clusters) if clusters else 0

        return_data = {
            "task_id": self.request.id,
            "status": "completed",
            "clusters_created": len(clusters),
            "articles_processed": total_articles,
            "average_cluster_size": round(avg_cluster_size, 2),
            "cluster_details": [
                {
                    "cluster_id": cluster.cluster_id,
                    "label": cluster.label,
                    "size": cluster.size,
                    "confidence": cluster.confidence_score,
                    "keywords": cluster.keywords[:5],  # Top 5 keywords
                }
                for cluster in clusters
            ],
            "started_at": task_start.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": (datetime.utcnow() - task_start).total_seconds(),
        }

        logger.info(
            "CLUST-1 only task completed",
            task_id=self.request.id,
            clusters_created=len(clusters),
            articles_processed=total_articles,
        )

        return return_data

    except Exception as exc:
        duration = (datetime.utcnow() - task_start).total_seconds()

        logger.error(
            "CLUST-1 only task failed",
            task_id=self.request.id,
            duration_seconds=duration,
            error=str(exc),
            exc_info=True,
        )

        raise


@celery_app.task(bind=True, base=ETLTask)
def get_clustering_status(self) -> Dict[str, Any]:
    """
    Get current clustering system status and metrics

    Returns:
        System status information
    """
    try:
        logger.info("Getting clustering status", task_id=self.request.id)

        # Get status
        import asyncio

        from ...clustering import ClusteringOrchestrator
        from ...core.config import get_config

        config = get_config()
        clustering_config = getattr(config, "clustering", {})

        orchestrator = ClusteringOrchestrator(clustering_config)
        status = asyncio.run(orchestrator.get_clustering_status())

        # Add task metadata
        status["task_id"] = self.request.id
        status["retrieved_at"] = datetime.utcnow().isoformat()

        logger.info(
            "Clustering status retrieved",
            task_id=self.request.id,
            unprocessed_articles=status.get("unprocessed_articles", 0),
            recent_clusters=status.get("recent_clusters_24h", 0),
        )

        return status

    except Exception as exc:
        logger.error(
            "Failed to get clustering status",
            task_id=self.request.id,
            error=str(exc),
            exc_info=True,
        )
        raise


@celery_app.task(bind=True, base=ETLTask)
def cleanup_old_clusters(self, max_age_days: int = 30) -> Dict[str, Any]:
    """
    Clean up old clustering results to prevent table bloat

    Args:
        max_age_days: Maximum age of clusters to keep

    Returns:
        Cleanup results
    """
    from ...core.database import get_db_session

    try:
        logger.info(
            "Starting cluster cleanup",
            task_id=self.request.id,
            max_age_days=max_age_days,
        )

        import asyncio

        async def cleanup():
            async with get_db_session() as session:
                # Delete old cluster assignments
                cleanup_query = """
                DELETE FROM article_clusters 
                WHERE cluster_algorithm = 'CLUST-1' 
                    AND clustered_at < NOW() - INTERVAL '%s days'
                """

                result = await session.execute(cleanup_query, (max_age_days,))
                deleted_count = result.rowcount

                await session.commit()
                return deleted_count

        deleted_count = asyncio.run(cleanup())

        return_data = {
            "task_id": self.request.id,
            "status": "completed",
            "deleted_clusters": deleted_count,
            "max_age_days": max_age_days,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Cluster cleanup completed",
            task_id=self.request.id,
            deleted_clusters=deleted_count,
        )

        return return_data

    except Exception as exc:
        logger.error(
            "Cluster cleanup failed",
            task_id=self.request.id,
            error=str(exc),
            exc_info=True,
        )
        raise


# Task scheduling configuration
CLUSTERING_BEAT_SCHEDULE = {
    "run-clustering-workflow": {
        "task": "etl_pipeline.core.tasks.clustering_tasks.run_complete_clustering_workflow",
        "schedule": 3600.0 * 4,  # Every 4 hours
        "args": (500,),  # Process up to 500 articles
        "options": {"queue": "ml_pipeline", "priority": 5},
    },
    "clustering-status-check": {
        "task": "etl_pipeline.core.tasks.clustering_tasks.get_clustering_status",
        "schedule": 1800.0,  # Every 30 minutes
        "options": {"queue": "monitoring", "priority": 3},
    },
    "cleanup-old-clusters": {
        "task": "etl_pipeline.core.tasks.clustering_tasks.cleanup_old_clusters",
        "schedule": 86400.0 * 7,  # Weekly
        "args": (30,),  # Keep 30 days of data
        "options": {"queue": "maintenance", "priority": 1},
    },
}
