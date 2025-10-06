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

    # LLM Configuration - MAP/REDUCE Parameters
    llm_timeout_seconds: int = Field(default=180, env="LLM_TIMEOUT_SECONDS")
    llm_max_tokens_generic: int = Field(default=4000, env="LLM_MAX_TOKENS_GENERIC")
    llm_temperature: float = Field(default=0.2, env="LLM_TEMPERATURE")
    llm_retry_attempts: int = Field(default=3, env="LLM_RETRY_ATTEMPTS")
    llm_retry_backoff: float = Field(default=2.0, env="LLM_RETRY_BACKOFF")

    # Incident-First Processing Configuration (Primary System)
    # Hybrid architecture: Incident clustering → Analysis → Single-title EF seeds for orphans
    # Optimized for production performance:
    # - DeepSeek API: 128K context, 8K max output, dynamic throttling
    # - Production settings: MAP=8, REDUCE=12 for optimal throughput
    # - Achieves 100% strategic coverage with zero fragmentation
    # - Processing time: 50 titles → 20 EFs in ~3-4 minutes (100% coverage)
    incident_processing_enabled: bool = Field(
        default=True, env="INCIDENT_PROCESSING_ENABLED"
    )
    map_batch_size: int = Field(
        default=100, env="MAP_BATCH_SIZE"
    )  # Titles per incident clustering call
    map_concurrency: int = Field(
        default=8, env="MAP_CONCURRENCY"
    )  # Parallel incident clustering operations
    map_timeout_seconds: int = Field(
        default=300, env="MAP_TIMEOUT_SECONDS"
    )  # Extended for clustering
    reduce_concurrency: int = Field(
        default=12, env="REDUCE_CONCURRENCY"
    )  # Parallel incident analysis operations
    reduce_timeout_seconds: int = Field(
        default=180, env="REDUCE_TIMEOUT_SECONDS"
    )  # Extended for analysis

    # Token Budget Calculations for Incident Processing:
    # MAP Phase (Incident Clustering): ~100 titles × 50 tokens = 5K input + 8K output = 13K total
    # REDUCE Phase (Incident Analysis): Variable input based on cluster size + 8K output
    # All within DeepSeek 131K context limit; concurrent requests are independent
    map_max_tokens: int = Field(
        default=8192, env="MAP_MAX_TOKENS"
    )  # Maximum tokens for MAP phase (incident clustering)
    reduce_max_tokens: int = Field(
        default=8192, env="REDUCE_MAX_TOKENS"
    )  # Maximum tokens for REDUCE phase (incident analysis)

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

    # EF Enrichment Configuration
    enrichment_enabled: bool = Field(default=True, env="ENRICHMENT_ENABLED")
    daily_enrichment_cap: int = Field(default=100, env="DAILY_ENRICHMENT_CAP")
    enrichment_max_tokens: int = Field(default=200, env="ENRICHMENT_MAX_TOKENS")
    enrichment_temperature: float = Field(default=0.0, env="ENRICHMENT_TEMPERATURE")
    enrichment_concurrency: int = Field(default=4, env="ENRICHMENT_CONCURRENCY")

    # Phase Control (enable/disable individual phases)
    phase_1_ingest_enabled: bool = Field(default=True, env="PHASE_1_INGEST_ENABLED")
    phase_2_filter_enabled: bool = Field(default=True, env="PHASE_2_FILTER_ENABLED")
    phase_3_generate_enabled: bool = Field(default=True, env="PHASE_3_GENERATE_ENABLED")
    phase_4_enrich_enabled: bool = Field(default=True, env="PHASE_4_ENRICH_ENABLED")

    # Phase Limits (for controlled execution)
    phase_1_max_feeds: Optional[int] = Field(default=None, env="PHASE_1_MAX_FEEDS")
    phase_2_max_titles: Optional[int] = Field(default=1000, env="PHASE_2_MAX_TITLES")
    phase_3_max_titles: Optional[int] = Field(default=500, env="PHASE_3_MAX_TITLES")
    phase_4_max_items: Optional[int] = Field(
        default=None, env="PHASE_4_MAX_ITEMS"
    )  # None = use daily_enrichment_cap

    # Phase Timeouts (in minutes) - based on realistic expectations
    phase_1_timeout_minutes: int = Field(
        default=10, env="PHASE_1_TIMEOUT_MINUTES"
    )  # RSS ingestion: 137 feeds
    phase_2_timeout_minutes: int = Field(
        default=15, env="PHASE_2_TIMEOUT_MINUTES"
    )  # Strategic filtering: 10k batch with LLM fallback
    phase_3_timeout_minutes: int = Field(
        default=15, env="PHASE_3_TIMEOUT_MINUTES"
    )  # EF generation: 500 titles
    phase_4_timeout_minutes: int = Field(
        default=30, env="PHASE_4_TIMEOUT_MINUTES"
    )  # Enrichment: 100 EFs with LLM

    # Concurrency Settings
    phase_2_concurrency: int = Field(
        default=5, env="PHASE_2_CONCURRENCY"
    )  # Parallel LLM calls for P2 filtering (5-10 recommended)
    phase_2_mini_batch_size: int = Field(
        default=100, env="PHASE_2_MINI_BATCH_SIZE"
    )  # Mini-batch size for parallel processing (memory management)
    phase_4_concurrency: int = Field(
        default=4, env="PHASE_4_CONCURRENCY"
    )  # Parallel enrichment processing

    # Business Logic Thresholds
    enrichment_confidence_high: float = Field(
        default=0.7, env="ENRICHMENT_CONFIDENCE_HIGH"
    )  # Centroid match high confidence threshold
    enrichment_confidence_medium: float = Field(
        default=0.4, env="ENRICHMENT_CONFIDENCE_MEDIUM"
    )  # Centroid match medium confidence threshold
    enrichment_summary_min_words: int = Field(
        default=50, env="ENRICHMENT_SUMMARY_MIN_WORDS"
    )  # Minimum words for valid summary
    enrichment_summary_max_words: int = Field(
        default=120, env="ENRICHMENT_SUMMARY_MAX_WORDS"
    )  # Maximum words in summary before truncation
    enrichment_keyword_score_bonus: int = Field(
        default=2, env="ENRICHMENT_KEYWORD_SCORE_BONUS"
    )  # Points added per strategic keyword match
    enrichment_max_title_count_score: int = Field(
        default=10, env="ENRICHMENT_MAX_TITLE_COUNT_SCORE"
    )  # Cap for title count in priority scoring
    enrichment_recency_days: int = Field(
        default=7, env="ENRICHMENT_RECENCY_DAYS"
    )  # Days to look back for enrichment queue

    ef_title_max_length: int = Field(
        default=120, env="EF_TITLE_MAX_LENGTH"
    )  # Maximum characters for EF title
    ef_summary_max_length: int = Field(
        default=280, env="EF_SUMMARY_MAX_LENGTH"
    )  # Maximum characters for EF summary

    map_success_rate_threshold: float = Field(
        default=0.5, env="MAP_SUCCESS_RATE_THRESHOLD"
    )  # Minimum success rate for MAP clustering (50%)

    strategic_priority_keywords: list = Field(
        default_factory=lambda: [
            "NATO",
            "nuclear",
            "sanctions",
            "invasion",
            "assassination",
            "diplomatic",
            "alliance",
            "security",
            "escalation",
        ],
        env="STRATEGIC_PRIORITY_KEYWORDS"
    )  # Keywords that boost EF enrichment priority

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
