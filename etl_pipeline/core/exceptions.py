"""
Custom exceptions for Strategic Narrative Intelligence ETL Pipeline

This module defines custom exception classes for different components
of the ETL pipeline with proper error categorization and context.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class ETLPipelineError(Exception):
    """Base exception for all ETL pipeline errors"""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }

    def __str__(self) -> str:
        base_msg = self.message
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" (Context: {context_str})"
        if self.cause:
            base_msg += f" (Caused by: {str(self.cause)})"
        return base_msg


class PipelineError(ETLPipelineError):
    """Errors related to pipeline orchestration and execution"""

    pass


class ConfigurationError(ETLPipelineError):
    """Errors related to configuration and setup"""

    pass


class DatabaseError(ETLPipelineError):
    """Errors related to database operations"""

    pass


class IngestionError(ETLPipelineError):
    """Errors related to feed ingestion"""

    pass


class FeedError(IngestionError):
    """Specific errors related to feed processing"""

    def __init__(
        self,
        message: str,
        feed_id: Optional[str] = None,
        feed_url: Optional[str] = None,
        http_status: Optional[int] = None,
        **kwargs,
    ):
        context = {"feed_id": feed_id, "feed_url": feed_url, "http_status": http_status}
        # Add any additional context
        context.update(kwargs)
        super().__init__(message, context)


class ContentError(IngestionError):
    """Errors related to content parsing and validation"""

    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
        **kwargs,
    ):
        context = {"content_type": content_type, "content_length": content_length}
        context.update(kwargs)
        super().__init__(message, context)


class ProcessingError(ETLPipelineError):
    """Errors related to content processing and NLP"""

    pass


class NERError(ProcessingError):
    """Errors related to Named Entity Recognition"""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs,
    ):
        context = {"model_name": model_name, "language": language}
        context.update(kwargs)
        super().__init__(message, context)


class ClassificationError(ProcessingError):
    """Errors related to content classification"""

    def __init__(
        self,
        message: str,
        classifier_type: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        **kwargs,
    ):
        context = {
            "classifier_type": classifier_type,
            "confidence_threshold": confidence_threshold,
        }
        context.update(kwargs)
        super().__init__(message, context)


class QualityError(ProcessingError):
    """Errors related to quality assessment"""

    def __init__(
        self,
        message: str,
        quality_metric: Optional[str] = None,
        threshold: Optional[float] = None,
        **kwargs,
    ):
        context = {"quality_metric": quality_metric, "threshold": threshold}
        context.update(kwargs)
        super().__init__(message, context)


class TaskError(ETLPipelineError):
    """Errors related to Celery task execution"""

    def __init__(
        self,
        message: str,
        task_name: Optional[str] = None,
        task_id: Optional[str] = None,
        retry_count: Optional[int] = None,
        **kwargs,
    ):
        context = {
            "task_name": task_name,
            "task_id": task_id,
            "retry_count": retry_count,
        }
        context.update(kwargs)
        super().__init__(message, context)


class ValidationError(ETLPipelineError):
    """Errors related to data validation"""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        **kwargs,
    ):
        context = {
            "field_name": field_name,
            "field_value": field_value,
            "validation_rule": validation_rule,
        }
        context.update(kwargs)
        super().__init__(message, context)


class MonitoringError(ETLPipelineError):
    """Errors related to monitoring and metrics collection"""

    pass


class AlertingError(MonitoringError):
    """Errors related to alerting system"""

    def __init__(
        self,
        message: str,
        alert_type: Optional[str] = None,
        channel: Optional[str] = None,
        **kwargs,
    ):
        context = {"alert_type": alert_type, "channel": channel}
        context.update(kwargs)
        super().__init__(message, context)


class MetricsError(MonitoringError):
    """Errors related to metrics collection"""

    def __init__(
        self,
        message: str,
        metric_name: Optional[str] = None,
        metric_value: Optional[Any] = None,
        **kwargs,
    ):
        context = {"metric_name": metric_name, "metric_value": metric_value}
        context.update(kwargs)
        super().__init__(message, context)


class APIError(ETLPipelineError):
    """Errors related to API operations"""

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        context = {"endpoint": endpoint, "method": method, "status_code": status_code}
        context.update(kwargs)
        super().__init__(message, context)


class AuthenticationError(APIError):
    """Errors related to authentication"""

    pass


class AuthorizationError(APIError):
    """Errors related to authorization"""

    pass


class RateLimitError(APIError):
    """Errors related to rate limiting"""

    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window: Optional[str] = None,
        **kwargs,
    ):
        context = {"limit": limit, "window": window}
        context.update(kwargs)
        super().__init__(message, context)


class TimeoutError(ETLPipelineError):
    """Errors related to timeouts"""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        context = {"timeout_seconds": timeout_seconds, "operation": operation}
        context.update(kwargs)
        super().__init__(message, context)


class ResourceError(ETLPipelineError):
    """Errors related to resource limitations"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        limit: Optional[Any] = None,
        current_usage: Optional[Any] = None,
        **kwargs,
    ):
        context = {
            "resource_type": resource_type,
            "limit": limit,
            "current_usage": current_usage,
        }
        context.update(kwargs)
        super().__init__(message, context)


class RetryableError(ETLPipelineError):
    """Base class for errors that should trigger retries"""

    def __init__(
        self, message: str, max_retries: int = 3, retry_delay: float = 60.0, **kwargs
    ):
        super().__init__(message, **kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay


class NonRetryableError(ETLPipelineError):
    """Base class for errors that should not trigger retries"""

    pass


# Specific retryable errors
class TemporaryFeedError(RetryableError, FeedError):
    """Temporary feed errors that should be retried"""

    pass


class TemporaryDatabaseError(RetryableError, DatabaseError):
    """Temporary database errors that should be retried"""

    pass


class TemporaryProcessingError(RetryableError, ProcessingError):
    """Temporary processing errors that should be retried"""

    pass


# Specific non-retryable errors
class PermanentFeedError(NonRetryableError, FeedError):
    """Permanent feed errors that should not be retried"""

    pass


class InvalidContentError(NonRetryableError, ContentError):
    """Invalid content errors that should not be retried"""

    pass


class ConfigurationValidationError(NonRetryableError, ConfigurationError):
    """Configuration validation errors that should not be retried"""

    pass


# Error categorization helpers
def is_retryable_error(error: Exception) -> bool:
    """Check if an error should trigger retries"""
    return isinstance(error, RetryableError) or isinstance(
        error,
        (
            ConnectionError,
            TimeoutError,
            # Add other Python built-in exceptions that should be retried
        ),
    )


def get_retry_delay(error: Exception, attempt: int = 1) -> float:
    """Get retry delay for an error"""
    if isinstance(error, RetryableError):
        # Exponential backoff with jitter
        base_delay = error.retry_delay
        exponential_delay = base_delay * (2 ** (attempt - 1))
        # Add up to 25% jitter to prevent thundering herd
        import random

        jitter = random.uniform(0.75, 1.25)
        return min(exponential_delay * jitter, base_delay * 10)  # Cap at 10x base delay

    # Default exponential backoff
    return min(60.0 * (2 ** (attempt - 1)), 600.0)  # Cap at 10 minutes


def get_max_retries(error: Exception) -> int:
    """Get maximum retries for an error"""
    if isinstance(error, RetryableError):
        return error.max_retries
    elif isinstance(error, NonRetryableError):
        return 0
    else:
        return 3  # Default retries


# Error context builders
def build_feed_context(
    feed_id: str = None, feed_url: str = None, feed_type: str = None
) -> Dict[str, Any]:
    """Build context dictionary for feed-related errors"""
    return {"feed_id": feed_id, "feed_url": feed_url, "feed_type": feed_type}


def build_article_context(
    article_id: str = None, article_url: str = None, article_title: str = None
) -> Dict[str, Any]:
    """Build context dictionary for article-related errors"""
    return {
        "article_id": article_id,
        "article_url": article_url,
        "article_title": (
            article_title[:100] if article_title else None
        ),  # Truncate long titles
    }


def build_task_context(
    task_name: str = None, task_id: str = None, worker_name: str = None
) -> Dict[str, Any]:
    """Build context dictionary for task-related errors"""
    return {"task_name": task_name, "task_id": task_id, "worker_name": worker_name}


# Error handling decorators
def handle_retryable_errors(max_retries: int = 3, retry_delay: float = 60.0):
    """Decorator to handle retryable errors"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_retries or not is_retryable_error(exc):
                        raise

                    delay = get_retry_delay(exc, attempt)
                    import time

                    time.sleep(delay)

        return wrapper

    return decorator


def convert_to_pipeline_error(error_type: str = "PipelineError"):
    """Decorator to convert exceptions to pipeline errors"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ETLPipelineError:
                # Re-raise pipeline errors as-is
                raise
            except Exception as exc:
                # Convert other exceptions to pipeline errors
                error_class = globals().get(error_type, PipelineError)
                raise error_class(
                    f"{func.__name__} failed: {str(exc)}", cause=exc
                ) from exc

        return wrapper

    return decorator
