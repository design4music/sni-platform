"""
ETL Pipeline Configuration Settings
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    OPENAI = "openai"


class PipelineSettings(BaseSettings):
    """Core pipeline configuration"""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/narrative_intelligence"
    )
    database_pool_size: int = Field(default=10)
    database_pool_max_overflow: int = Field(default=20)

    # Redis Configuration (for Celery)
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Pipeline Timing
    processing_window_hours: int = Field(default=4)
    daily_start_hour: int = Field(default=2)  # 2 AM UTC
    batch_size: int = Field(default=100)
    max_retries: int = Field(default=3)
    retry_delay_seconds: int = Field(default=300)  # 5 minutes

    # Data Sources
    max_feed_sources: int = Field(default=80)
    feed_timeout_seconds: int = Field(default=30)
    api_rate_limit_per_minute: int = Field(default=60)

    # Language Processing
    supported_languages: List[str] = Field(default=["en", "ru", "de", "fr"])
    default_language: str = Field(default="en")

    # ML/NLP Configuration
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)
    clustering_min_samples: int = Field(default=3)
    clustering_eps: float = Field(default=0.5)
    similarity_threshold: float = Field(default=0.7)

    # LLM Configuration
    primary_llm_provider: LLMProvider = Field(default=LLMProvider.DEEPSEEK)
    fallback_llm_providers: List[LLMProvider] = Field(
        default=[LLMProvider.CLAUDE, LLMProvider.OPENAI]
    )

    # API Keys (loaded from environment)
    deepseek_api_key: Optional[str] = Field(default=None)
    claude_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=8000)
    sentry_dsn: Optional[str] = Field(default=None)
    log_level: str = Field(default="INFO")

    # Data Quality
    min_article_length: int = Field(default=100)
    max_article_length: int = Field(default=50000)
    duplicate_threshold: float = Field(default=0.9)

    # Performance
    max_concurrent_tasks: int = Field(default=10)
    chunk_size: int = Field(default=1000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class FeedSourceConfig:
    """Configuration for news feed sources"""

    RSS_FEEDS = {
        "reuters": {
            "url": "https://feeds.reuters.com/reuters/topNews",
            "language": "en",
            "category": "general",
            "priority": 1,
        },
        "bbc": {
            "url": "http://feeds.bbci.co.uk/news/rss.xml",
            "language": "en",
            "category": "general",
            "priority": 1,
        },
        "cnn": {
            "url": "http://rss.cnn.com/rss/edition.rss",
            "language": "en",
            "category": "general",
            "priority": 2,
        },
        "rt_russian": {
            "url": "https://russian.rt.com/rss",
            "language": "ru",
            "category": "general",
            "priority": 2,
        },
        "dw_german": {
            "url": "https://rss.dw.com/rdf/rss-de-all",
            "language": "de",
            "category": "general",
            "priority": 2,
        },
        "france24": {
            "url": "https://www.france24.com/fr/rss",
            "language": "fr",
            "category": "general",
            "priority": 2,
        },
    }

    API_SOURCES = {
        "newsapi": {
            "endpoint": "https://newsapi.org/v2/top-headlines",
            "rate_limit": 500,  # requests per day
            "languages": ["en", "ru", "de", "fr"],
            "priority": 1,
        }
    }


class ClusteringConfig:
    """Configuration for clustering stages"""

    CLUST_1_THEMATIC = {
        "algorithm": "dbscan",
        "eps": 0.3,
        "min_samples": 3,
        "metric": "cosine",
        "features": ["title_embedding", "content_embedding", "entities"],
    }

    CLUST_2_INTERPRETIVE = {
        "algorithm": "agglomerative",
        "n_clusters": None,
        "distance_threshold": 0.4,
        "linkage": "ward",
        "features": ["sentiment", "topics", "narrative_elements"],
    }

    CLUST_3_TEMPORAL_ANOMALY = {
        "algorithm": "isolation_forest",
        "contamination": 0.1,
        "time_window_hours": 24,
        "features": ["publish_time", "engagement_rate", "source_reliability"],
    }

    CLUST_4_CONSOLIDATION = {
        "algorithm": "hierarchical",
        "merge_threshold": 0.6,
        "max_clusters": 50,
        "features": ["all_previous_stages"],
    }


class GenerationConfig:
    """Configuration for generation stages"""

    GEN_1_NARRATIVE_BUILDER = {
        "model_config": {"temperature": 0.3, "max_tokens": 2000, "top_p": 0.9},
        "prompt_template": "narrative_builder.jinja2",
        "output_format": "structured_narrative",
    }

    GEN_2_UPDATES = {
        "model_config": {"temperature": 0.2, "max_tokens": 1000, "top_p": 0.8},
        "prompt_template": "narrative_updater.jinja2",
        "update_threshold": 0.5,
    }

    GEN_3_CONTRADICTION_DETECTION = {
        "model_config": {"temperature": 0.1, "max_tokens": 500, "top_p": 0.7},
        "prompt_template": "contradiction_detector.jinja2",
        "contradiction_threshold": 0.7,
    }


# Global settings instance
settings = PipelineSettings()
