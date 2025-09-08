"""SNI-v2 Configuration Management"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


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
    deepseek_api_url: str = Field(default="https://api.deepseek.com/v1", env="DEEPSEEK_API_URL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    llm_provider: str = Field(default="deepseek", env="LLM_PROVIDER")
    llm_model: str = Field(default="deepseek-chat", env="LLM_MODEL")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS_PER_REQUEST")
    
    # Processing
    max_bucket_size: int = Field(default=100, env="MAX_BUCKET_SIZE")
    default_fetch_interval: int = Field(default=60, env="DEFAULT_FETCH_INTERVAL")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Clustering thresholds
    cosine_threshold_dedup: float = Field(default=0.95, env="COSINE_THRESHOLD_DEDUP")
    cosine_threshold_bucket: float = Field(default=0.60, env="COSINE_THRESHOLD_BUCKET") 
    cosine_threshold_gate: float = Field(default=0.70, env="COSINE_THRESHOLD_GATE")
    cosine_threshold_merge: float = Field(default=0.85, env="COSINE_THRESHOLD_MERGE")
    
    # Strategic gate vocabulary paths
    actors_csv_path: str = Field(default="data/actors.csv", env="ACTORS_CSV_PATH")
    mechanisms_json_path: str = Field(default="data/mechanisms.json", env="MECHANISMS_JSON_PATH")
    max_top_anchors: int = Field(default=3, env="MAX_TOP_ANCHORS")
    
    # CLUST-2 Bucket configuration
    bucket_max_span_hours: int = Field(default=72, env="BUCKET_MAX_SPAN_HOURS")
    bucket_min_size: int = Field(default=3, env="BUCKET_MIN_SIZE")
    bucket_since_hours: int = Field(default=72, env="BUCKET_SINCE_HOURS")
    bucket_max_actors: int = Field(default=4, env="BUCKET_MAX_ACTORS")
    
    # Ingestion
    max_items_per_feed: Optional[int] = Field(default=None, env="MAX_ITEMS_PER_FEED")
    lookback_days: int = Field(default=3, env="LOOKBACK_DAYS")
    http_retries: int = Field(default=3, env="HTTP_RETRIES")
    http_timeout_sec: int = Field(default=30, env="HTTP_TIMEOUT_SEC")
    
    # Language - NOTE: System supports ALL languages, these are just optimized/configured ones
    # Pipeline must never fail on unsupported languages (Portuguese, Malay, etc.)
    primary_language: str = Field(default="en", env="PRIMARY_LANGUAGE")
    supported_languages: str = Field(default="en,es,fr,de,ru,zh", env="SUPPORTED_LANGUAGES")
    
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