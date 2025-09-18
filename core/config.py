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

    # DeepSeek API Constraints & Limits (for informed concurrency optimization)
    # Source: DeepSeek API documentation and testing results
    # Context Window: 128K tokens (131,072 tokens) for deepseek-chat model
    # Max Output: 8K tokens (8,192 tokens) - hard limit, no higher setting possible
    # Rate Limits: No traditional rate limits - uses dynamic throttling instead
    # Request Timeout: 30 minutes maximum per request
    # Concurrency: No documented hard limits, but dynamic throttling applies
    # Token Counting: Uses tiktoken cl100k_base encoding

    # Current Conservative Settings Based on API Constraints:
    deepseek_context_window_tokens: int = Field(
        default=131072, env="DEEPSEEK_CONTEXT_WINDOW"
    )  # 128K
    deepseek_max_output_tokens: int = Field(
        default=8192, env="DEEPSEEK_MAX_OUTPUT_TOKENS"
    )  # 8K hard limit
    deepseek_request_timeout_minutes: int = Field(
        default=30, env="DEEPSEEK_REQUEST_TIMEOUT"
    )  # API maximum
    deepseek_dynamic_throttling: bool = Field(
        default=True, env="DEEPSEEK_DYNAMIC_THROTTLING"
    )  # No rate limits

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

    # MAP/REDUCE Configuration (Alternative Processing)
    # Concurrency Optimization Guidelines:
    # - DeepSeek uses dynamic throttling, not hard rate limits
    # - Current settings (MAP=4, REDUCE=8) are conservative for reliability
    # - Higher concurrency possible but may trigger throttling/delays
    # - Optimal range likely MAP=8-16, REDUCE=12-24 based on API behavior
    # - Token limits: MAP=8000 (near max), REDUCE=4000 (default)
    # - Monitor response times: >10s may indicate throttling
    mapreduce_enabled: bool = Field(default=False, env="MAPREDUCE_ENABLED")
    map_batch_size: int = Field(
        default=100, env="MAP_BATCH_SIZE"
    )  # Titles per MAP call (fits in context)
    map_concurrency: int = Field(
        default=8, env="MAP_CONCURRENCY"
    )  # Production: max parallelism
    map_timeout_seconds: int = Field(default=90, env="MAP_TIMEOUT_SECONDS")
    map_max_tokens: int = Field(
        default=8000, env="MAP_MAX_TOKENS"
    )  # Near DeepSeek's 8192 limit
    reduce_concurrency: int = Field(
        default=12, env="REDUCE_CONCURRENCY"
    )  # Production: max parallelism
    reduce_timeout_seconds: int = Field(default=45, env="REDUCE_TIMEOUT_SECONDS")
    reduce_max_titles: int = Field(
        default=12, env="REDUCE_MAX_TITLES"
    )  # Titles per REDUCE call

    # Concurrency Testing Strategy (for educated optimization):
    # 1. Baseline: Current conservative settings (MAP=4, REDUCE=8)
    # 2. Moderate: MAP=8, REDUCE=12 (2x increase)
    # 3. Aggressive: MAP=16, REDUCE=24 (4x increase)
    # 4. Monitor metrics: response_time_avg, throttling_events, error_rate
    # 5. Success criteria: <5s avg response, <5% errors, minimal throttling
    # 6. If throttling detected (>10s responses), back off by 25-50%

    # Token Budget Calculations:
    # MAP Phase: ~100 titles × 50 tokens = 5K input + 8K output = 13K total (within 131K limit)
    # REDUCE Phase: ~12 titles × 50 tokens = 600 input + 4K output = 4.6K total (within 131K limit)
    # Concurrent requests share no token budget (each request independent)

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
