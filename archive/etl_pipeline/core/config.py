"""
Configuration management for Strategic Narrative Intelligence ETL Pipeline

This module provides centralized configuration management with environment
variable support, validation, and type safety.
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from crontab import CronTab


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    host: str = "localhost"
    port: int = 5432
    database: str = "narrative_intelligence"
    username: str = "postgres"
    password: str = ""

    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20

    # SSL and security
    ssl_mode: Optional[str] = None

    # Admin credentials for database initialization
    admin_username: Optional[str] = None
    admin_password: Optional[str] = None

    # Query settings
    echo_sql: bool = False

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "narrative_intelligence"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            ssl_mode=os.getenv("DB_SSL_MODE"),
            admin_username=os.getenv("DB_ADMIN_USER"),
            admin_password=os.getenv("DB_ADMIN_PASSWORD"),
            echo_sql=os.getenv("DB_ECHO_SQL", "false").lower() == "true",
        )

    @property
    def connection_url(self) -> str:
        """Get database connection URL for SQLAlchemy"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_connection_params(self) -> dict:
        """Get connection parameters for psycopg2"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.username,
            "password": self.password,
        }


@dataclass
class RedisConfig:
    """Redis configuration"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    # Connection settings
    max_connections: int = 50
    socket_timeout: float = 5.0

    @property
    def url(self) -> str:
        """Get Redis connection URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0")),
        )


@dataclass
class FeedConfig:
    """News feed configuration"""

    active_feeds: List[Dict[str, Any]] = field(default_factory=list)
    max_concurrent_feeds: int = 10
    feed_timeout_seconds: int = 300

    @classmethod
    def from_env(cls) -> "FeedConfig":
        """Create configuration from environment variables"""
        feeds_json = os.getenv("ACTIVE_FEEDS", "[]")
        try:
            active_feeds = json.loads(feeds_json)
        except json.JSONDecodeError:
            active_feeds = []

        return cls(
            active_feeds=active_feeds,
            max_concurrent_feeds=int(os.getenv("MAX_CONCURRENT_FEEDS", "10")),
            feed_timeout_seconds=int(os.getenv("FEED_TIMEOUT_SECONDS", "300")),
        )


@dataclass
class IngestionConfig:
    """Ingestion configuration"""

    # HTTP client settings
    request_timeout_seconds: int = 30
    connect_timeout_seconds: int = 10
    max_retries: int = 3
    retry_delay_seconds: float = 60.0

    # Request headers
    user_agent: str = "Strategic-Narrative-Intelligence-Bot/1.0"

    # API keys for authenticated feeds
    api_keys: Dict[str, str] = field(default_factory=dict)

    # Content validation
    min_content_length: int = 100
    max_content_length: int = 50000

    @classmethod
    def from_env(cls) -> "IngestionConfig":
        """Create configuration from environment variables"""
        # Parse API keys from environment
        api_keys = {}
        for key, value in os.environ.items():
            if key.startswith("API_KEY_"):
                feed_id = key[8:]  # Remove 'API_KEY_' prefix
                api_keys[feed_id] = value

        return cls(
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT", "30")),
            connect_timeout_seconds=int(os.getenv("CONNECT_TIMEOUT", "10")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay_seconds=float(os.getenv("RETRY_DELAY", "60.0")),
            user_agent=os.getenv(
                "USER_AGENT", "Strategic-Narrative-Intelligence-Bot/1.0"
            ),
            api_keys=api_keys,
            min_content_length=int(os.getenv("MIN_CONTENT_LENGTH", "100")),
            max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", "50000")),
        )


@dataclass
class ProcessingConfig:
    """Content processing configuration"""

    # Processing thresholds
    min_relevance_threshold: float = 0.3
    min_quality_threshold: float = 0.4
    min_entity_confidence: float = 0.7
    min_category_confidence: float = 0.5

    # Batch processing
    batch_size: int = 50
    max_workers: int = 4

    # Model configuration
    spacy_models_path: str = ""
    huggingface_cache_dir: str = ""

    # Processing limits
    max_text_length: int = 10000
    max_entities_per_article: int = 100

    @classmethod
    def from_env(cls) -> "ProcessingConfig":
        """Create configuration from environment variables"""
        return cls(
            min_relevance_threshold=float(os.getenv("MIN_RELEVANCE_THRESHOLD", "0.3")),
            min_quality_threshold=float(os.getenv("MIN_QUALITY_THRESHOLD", "0.4")),
            min_entity_confidence=float(os.getenv("MIN_ENTITY_CONFIDENCE", "0.7")),
            min_category_confidence=float(os.getenv("MIN_CATEGORY_CONFIDENCE", "0.5")),
            batch_size=int(os.getenv("PROCESSING_BATCH_SIZE", "50")),
            max_workers=int(os.getenv("PROCESSING_MAX_WORKERS", "4")),
            spacy_models_path=os.getenv("SPACY_MODELS_PATH", ""),
            huggingface_cache_dir=os.getenv("HUGGINGFACE_CACHE_DIR", ""),
            max_text_length=int(os.getenv("MAX_TEXT_LENGTH", "10000")),
            max_entities_per_article=int(os.getenv("MAX_ENTITIES_PER_ARTICLE", "100")),
        )


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration"""

    # Metrics collection
    enable_metrics: bool = True
    metrics_port: int = 8090
    metrics_path: str = "/metrics"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Health checks
    health_check_interval_seconds: int = 60

    # Performance monitoring
    enable_profiling: bool = False
    profiling_sample_rate: float = 0.01

    @classmethod
    def from_env(cls) -> "MonitoringConfig":
        """Create configuration from environment variables"""
        return cls(
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "8090")),
            metrics_path=os.getenv("METRICS_PATH", "/metrics"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            health_check_interval_seconds=int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            enable_profiling=os.getenv("ENABLE_PROFILING", "false").lower() == "true",
            profiling_sample_rate=float(os.getenv("PROFILING_SAMPLE_RATE", "0.01")),
        )


@dataclass
class AlertingConfig:
    """Alerting configuration"""

    # Notification channels
    slack_webhook_url: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)

    # Alert thresholds
    pipeline_failure_threshold: int = 1
    feed_failure_threshold: int = 3
    processing_delay_threshold_minutes: int = 60
    error_rate_threshold: float = 0.1

    # Alert frequency limits
    max_alerts_per_hour: int = 10
    cooldown_minutes: int = 30

    @classmethod
    def from_env(cls) -> "AlertingConfig":
        """Create configuration from environment variables"""
        email_recipients = []
        recipients_str = os.getenv("EMAIL_RECIPIENTS", "")
        if recipients_str:
            email_recipients = [email.strip() for email in recipients_str.split(",")]

        return cls(
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            email_smtp_host=os.getenv("EMAIL_SMTP_HOST"),
            email_smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")),
            email_username=os.getenv("EMAIL_USERNAME"),
            email_password=os.getenv("EMAIL_PASSWORD"),
            email_recipients=email_recipients,
            pipeline_failure_threshold=int(
                os.getenv("PIPELINE_FAILURE_THRESHOLD", "1")
            ),
            feed_failure_threshold=int(os.getenv("FEED_FAILURE_THRESHOLD", "3")),
            processing_delay_threshold_minutes=int(
                os.getenv("PROCESSING_DELAY_THRESHOLD", "60")
            ),
            error_rate_threshold=float(os.getenv("ERROR_RATE_THRESHOLD", "0.1")),
            max_alerts_per_hour=int(os.getenv("MAX_ALERTS_PER_HOUR", "10")),
            cooldown_minutes=int(os.getenv("ALERT_COOLDOWN_MINUTES", "30")),
        )


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""

    # Scheduling
    daily_schedule: str = "0 2 * * *"  # 2 AM daily
    processing_window_hours: int = 4

    # Batch processing
    processing_batch_size: int = 100
    max_parallel_tasks: int = 5

    # Data retention
    article_retention_days: int = 365
    metrics_retention_days: int = 90
    log_retention_days: int = 30

    # Performance limits
    max_memory_usage_mb: int = 4096
    max_cpu_usage_percent: float = 80.0

    @property
    def daily_schedule_cron(self) -> CronTab:
        """Get cron schedule object"""
        return CronTab(self.daily_schedule)

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create configuration from environment variables"""
        return cls(
            daily_schedule=os.getenv("DAILY_SCHEDULE", "0 2 * * *"),
            processing_window_hours=int(os.getenv("PROCESSING_WINDOW_HOURS", "4")),
            processing_batch_size=int(os.getenv("PIPELINE_BATCH_SIZE", "100")),
            max_parallel_tasks=int(os.getenv("MAX_PARALLEL_TASKS", "5")),
            article_retention_days=int(os.getenv("ARTICLE_RETENTION_DAYS", "365")),
            metrics_retention_days=int(os.getenv("METRICS_RETENTION_DAYS", "90")),
            log_retention_days=int(os.getenv("LOG_RETENTION_DAYS", "30")),
            max_memory_usage_mb=int(os.getenv("MAX_MEMORY_USAGE_MB", "4096")),
            max_cpu_usage_percent=float(os.getenv("MAX_CPU_USAGE_PERCENT", "80.0")),
        )


@dataclass
class APIConfig:
    """FastAPI configuration"""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Security
    secret_key: str = ""
    access_token_expire_minutes: int = 30

    # API limits
    rate_limit_requests_per_minute: int = 100
    max_request_size_mb: int = 10

    # CORS
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST"])

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create configuration from environment variables"""
        allowed_origins = ["*"]
        origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if origins_str:
            allowed_origins = [origin.strip() for origin in origins_str.split(",")]

        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            workers=int(os.getenv("API_WORKERS", "1")),
            secret_key=os.getenv("SECRET_KEY", ""),
            access_token_expire_minutes=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "100")),
            max_request_size_mb=int(os.getenv("MAX_REQUEST_SIZE_MB", "10")),
            allowed_origins=allowed_origins,
        )


@dataclass
class Config:
    """Main application configuration"""

    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    feeds: FeedConfig = field(default_factory=FeedConfig)
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    api: APIConfig = field(default_factory=APIConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Create complete configuration from environment variables"""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        environment = Environment(env_str)

        return cls(
            environment=environment,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            database=DatabaseConfig.from_env(),
            redis=RedisConfig.from_env(),
            feeds=FeedConfig.from_env(),
            ingestion=IngestionConfig.from_env(),
            processing=ProcessingConfig.from_env(),
            monitoring=MonitoringConfig.from_env(),
            alerting=AlertingConfig.from_env(),
            pipeline=PipelineConfig.from_env(),
            api=APIConfig.from_env(),
        )

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Database validation
        if not self.database.password and self.environment == Environment.PRODUCTION:
            errors.append("Database password is required in production")

        # Redis validation
        if not self.redis.host:
            errors.append("Redis host is required")

        # API validation
        if not self.api.secret_key and self.environment == Environment.PRODUCTION:
            errors.append("Secret key is required in production")

        # Processing validation
        if (
            self.processing.min_relevance_threshold < 0
            or self.processing.min_relevance_threshold > 1
        ):
            errors.append("min_relevance_threshold must be between 0 and 1")

        if (
            self.processing.min_quality_threshold < 0
            or self.processing.min_quality_threshold > 1
        ):
            errors.append("min_quality_threshold must be between 0 and 1")

        # Pipeline validation
        if (
            self.pipeline.processing_window_hours < 1
            or self.pipeline.processing_window_hours > 24
        ):
            errors.append("processing_window_hours must be between 1 and 24")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, "__dict__"):
                result[key] = value.__dict__
            else:
                result[key] = value
        return result


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config.from_env()

        # Validate configuration
        errors = _config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

    return _config


def set_config(config: Config):
    """Set global configuration instance"""
    global _config
    _config = config


def load_config_from_file(file_path: str) -> Config:
    """Load configuration from JSON file"""
    with open(file_path, "r") as f:
        json.load(f)

    # Create config from dictionary
    # This would need custom deserialization logic
    # For now, we'll use environment variables
    return Config.from_env()


def get_db_connection():
    """Get database connection using centralized configuration

    This is the SINGLE POINT for all database connections in the pipeline.
    All scripts should use this function instead of hardcoded connections.
    """
    import psycopg2

    config = get_config()
    db_params = config.database.get_connection_params()

    return psycopg2.connect(**db_params)
