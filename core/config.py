"""WorldBrief Configuration Management"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SNIConfig(BaseSettings):
    """Main WorldBrief configuration"""

    # Load from .env file, ignore extra fields
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # ========================================================================
    # Core Infrastructure
    # ========================================================================

    # Database
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="sni_v2", env="DB_NAME")
    db_user: str = Field(default="postgres", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")

    # LLM - DeepSeek primary
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    deepseek_api_url: str = Field(
        default="https://api.deepseek.com/v1", env="DEEPSEEK_API_URL"
    )
    llm_provider: str = Field(default="deepseek", env="LLM_PROVIDER")
    llm_model: str = Field(default="deepseek-chat", env="LLM_MODEL")

    # LLM Configuration
    llm_timeout_seconds: int = Field(default=600, env="LLM_TIMEOUT_SECONDS")
    llm_temperature: float = Field(default=0.2, env="LLM_TEMPERATURE")
    llm_retry_attempts: int = Field(default=3, env="LLM_RETRY_ATTEMPTS")
    llm_retry_backoff: float = Field(default=2.0, env="LLM_RETRY_BACKOFF")

    # ========================================================================
    # Pipeline Configuration
    # ========================================================================

    # Phase 1: RSS Ingestion
    max_items_per_feed: Optional[int] = Field(default=None, env="MAX_ITEMS_PER_FEED")
    lookback_days: int = Field(default=3, env="LOOKBACK_DAYS")
    http_retries: int = Field(default=3, env="HTTP_RETRIES")
    http_timeout_sec: int = Field(default=30, env="HTTP_TIMEOUT_SEC")

    # Phase 2: Centroid Matching (3-pass mechanical, no LLM)
    v3_p2_batch_size: int = Field(default=100, env="V3_P2_BATCH_SIZE")
    v3_p2_timeout_seconds: int = Field(default=180, env="V3_P2_TIMEOUT_SECONDS")
    v3_p2_max_titles: Optional[int] = Field(default=1000, env="V3_P2_MAX_TITLES")

    # Phase 3: Intel Gating + Track Classification (LLM-based)
    v3_p3_temperature: float = Field(default=0.0, env="V3_P3_TEMPERATURE")
    v3_p3_max_tokens_gating: int = Field(default=500, env="V3_P3_MAX_TOKENS_GATING")
    v3_p3_max_tokens_tracks: int = Field(default=500, env="V3_P3_MAX_TOKENS_TRACKS")
    v3_p3_centroid_batch_size: int = Field(default=50, env="V3_P3_CENTROID_BATCH_SIZE")
    v3_p3_concurrency: int = Field(default=8, env="V3_P3_CONCURRENCY")
    v3_p3_timeout_seconds: int = Field(default=300, env="V3_P3_TIMEOUT_SECONDS")
    v3_p3_max_titles: Optional[int] = Field(default=1000, env="V3_P3_MAX_TITLES")

    # Phase 4: Events Digest and Summary Generation
    v3_p4_batch_size: int = Field(default=70, env="V3_P4_BATCH_SIZE")
    v3_p4_min_titles: int = Field(default=30, env="V3_P4_MIN_TITLES")
    v3_p4_max_concurrent: int = Field(default=5, env="V3_P4_MAX_CONCURRENT")
    v3_p4_temperature: float = Field(default=0.5, env="V3_P4_TEMPERATURE")
    v3_p4_max_tokens: int = Field(default=500, env="V3_P4_MAX_TOKENS")
    v3_p4_timeout_seconds: int = Field(default=180, env="V3_P4_TIMEOUT_SECONDS")

    # Database Tables
    v3_centroids_table: str = Field(default="centroids_v3", env="V3_CENTROIDS_TABLE")
    v3_taxonomy_table: str = Field(default="taxonomy_v3", env="V3_TAXONOMY_TABLE")
    v3_ctm_table: str = Field(default="ctm", env="V3_CTM_TABLE")
    v3_titles_table: str = Field(default="titles_v3", env="V3_TITLES_TABLE")

    # Language Support
    primary_language: str = Field(default="en", env="PRIMARY_LANGUAGE")
    supported_languages: str = Field(default="en,es,fr,de,ru,zh,ar", env="SUPPORTED_LANGUAGES")

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def pipeline_root_path(self) -> Path:
        """Root directory for pipeline"""
        return self.project_root / "pipeline"

    @property
    def supported_languages_list(self) -> List[str]:
        """Languages with specific configurations
        NOTE: System handles ALL languages gracefully, not just these."""
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
