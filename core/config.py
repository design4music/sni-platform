"""SNI-v2 Configuration Management"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SNIConfig(BaseSettings):
    """Main SNI configuration"""

    # Load from .env file, ignore extra fields
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="sni_v2", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")

    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")

    # LLM - DeepSeek primary, others available
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    deepseek_api_url: str = Field(
        default="https://api.deepseek.com/v1", env="DEEPSEEK_API_URL"
    )
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    llm_provider: str = Field(default="deepseek", env="LLM_PROVIDER")
    llm_model: str = Field(default="deepseek-chat", env="LLM_MODEL")

    # LLM Configuration - Unified Parameters
    llm_timeout_seconds: int = Field(default=180, env="LLM_TIMEOUT_SECONDS")
    llm_max_tokens_ef: int = Field(default=4000, env="LLM_MAX_TOKENS_EF")
    llm_max_tokens_fn: int = Field(default=3000, env="LLM_MAX_TOKENS_FN")
    llm_max_tokens_generic: int = Field(default=2000, env="LLM_MAX_TOKENS_GENERIC")
    llm_temperature: float = Field(default=0.2, env="LLM_TEMPERATURE")
    llm_retry_attempts: int = Field(default=3, env="LLM_RETRY_ATTEMPTS")
    llm_retry_backoff: float = Field(default=2.0, env="LLM_RETRY_BACKOFF")

    # Rate Limiting
    llm_requests_per_minute: int = Field(default=30, env="LLM_REQUESTS_PER_MINUTE")
    llm_concurrent_requests: int = Field(default=1, env="LLM_CONCURRENT_REQUESTS")

    # Batch Processing - Unified Configuration
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    max_titles_per_run: int = Field(default=10000, env="MAX_TITLES_PER_RUN")
    max_event_families_per_run: int = Field(
        default=1000, env="MAX_EVENT_FAMILIES_PER_RUN"
    )

    # Legacy support (deprecated - remove in future)
    default_fetch_interval: int = Field(default=60, env="DEFAULT_FETCH_INTERVAL")

    # Strategic gate vocabulary paths
    actors_csv_path: str = Field(default="data/actors.csv", env="ACTORS_CSV_PATH")

    # Multi-list strategic filtering (go/stop lists)
    go_people_csv_path: str = Field(
        default="data/go_people.csv", env="GO_PEOPLE_CSV_PATH"
    )
    stop_culture_csv_path: str = Field(
        default="data/stop_culture.csv", env="STOP_CULTURE_CSV_PATH"
    )
    go_taxonomy_csv_path: str = Field(
        default="data/go_taxonomy.csv", env="GO_TAXONOMY_CSV_PATH"
    )

    # Processing time windows (unified across all phases)
    # This setting controls how far back to look for titles in all processing phases:
    # - CLUST-1 Strategic Gate (when processing pending titles)
    # - CLUST-2 Big-Bucket Grouping (when creating clusters)
    # - Future processing phases should use this same window for consistency
    processing_window_hours: int = Field(default=72, env="PROCESSING_WINDOW_HOURS")

    # Database Configuration
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_timeout_seconds: int = Field(default=30, env="DB_TIMEOUT_SECONDS")

    # Ingestion Configuration
    max_items_per_feed: Optional[int] = Field(default=None, env="MAX_ITEMS_PER_FEED")
    lookback_days: int = Field(default=3, env="LOOKBACK_DAYS")
    http_retries: int = Field(default=3, env="HTTP_RETRIES")
    http_timeout_sec: int = Field(default=30, env="HTTP_TIMEOUT_SEC")

    # Language - NOTE: System supports ALL languages, these are just optimized/configured ones
    # Pipeline must never fail on unsupported languages (Portuguese, Malay, etc.)
    primary_language: str = Field(default="en", env="PRIMARY_LANGUAGE")
    supported_languages: str = Field(
        default="en,es,fr,de,ru,zh", env="SUPPORTED_LANGUAGES"
    )

    # Pipeline Orchestration
    pipeline_enabled: bool = Field(default=True, env="PIPELINE_ENABLED")
    pipeline_daemon_mode: bool = Field(default=False, env="PIPELINE_DAEMON_MODE")
    pipeline_interval_minutes: int = Field(default=60, env="PIPELINE_INTERVAL_MINUTES")
    pipeline_max_cycles: Optional[int] = Field(default=None, env="PIPELINE_MAX_CYCLES")

    # Phase Control (enable/disable individual phases)
    phase_1_ingest_enabled: bool = Field(default=True, env="PHASE_1_INGEST_ENABLED")
    phase_2_filter_enabled: bool = Field(default=True, env="PHASE_2_FILTER_ENABLED")
    phase_3_generate_enabled: bool = Field(default=True, env="PHASE_3_GENERATE_ENABLED")

    # Phase Limits (for controlled execution)
    phase_1_max_feeds: Optional[int] = Field(default=None, env="PHASE_1_MAX_FEEDS")
    phase_2_max_titles: Optional[int] = Field(default=1000, env="PHASE_2_MAX_TITLES")
    phase_3_max_titles: Optional[int] = Field(default=500, env="PHASE_3_MAX_TITLES")

    # Monitoring and Safety
    pipeline_error_threshold: int = Field(default=3, env="PIPELINE_ERROR_THRESHOLD")
    pipeline_heartbeat_file: str = Field(
        default="logs/pipeline_heartbeat.json", env="PIPELINE_HEARTBEAT_FILE"
    )
    pipeline_status_file: str = Field(
        default="logs/pipeline_status.json", env="PIPELINE_STATUS_FILE"
    )

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def supported_languages_list(self) -> List[str]:
        """Languages with specific configurations (spaCy models, etc.)
        NOTE: System must handle ALL languages gracefully, not just these."""
        return [lang.strip() for lang in self.supported_languages.split(",")]

    @property
    def logs_dir(self) -> Path:
        logs_path = self.project_root / "logs"
        logs_path.mkdir(exist_ok=True)
        return logs_path


# Global config instance
config = SNIConfig()


def get_config() -> SNIConfig:
    """Get the global configuration instance"""
    return config
