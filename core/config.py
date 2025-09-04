"""SNI-v2 Configuration Management"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT") 
    name: str = Field(default="sni_v2", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class APIConfig(BaseSettings):
    """API server configuration"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")


class LLMConfig(BaseSettings):
    """LLM provider configuration"""
    provider: str = Field(default="openai", env="LLM_PROVIDER")
    model: str = Field(default="gpt-4-turbo-preview", env="LLM_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS_PER_REQUEST")


class ProcessingConfig(BaseSettings):
    """Processing pipeline configuration"""
    max_bucket_size: int = Field(default=100, env="MAX_BUCKET_SIZE")
    default_fetch_interval: int = Field(default=60, env="DEFAULT_FETCH_INTERVAL")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    cosine_threshold_dedup: float = Field(default=0.95, env="COSINE_THRESHOLD_DEDUP")
    cosine_threshold_bucket: float = Field(default=0.60, env="COSINE_THRESHOLD_BUCKET")
    

class LanguageConfig(BaseSettings):
    """Language processing configuration"""
    primary_language: str = Field(default="en", env="PRIMARY_LANGUAGE")
    supported_languages: str = Field(default="en,es,fr,de,ru,zh", env="SUPPORTED_LANGUAGES")
    
    @property
    def supported_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.supported_languages.split(",")]


class SNIConfig(BaseSettings):
    """Main SNI configuration"""
    
    # Load from .env file
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    # Sub-configs
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    language: LanguageConfig = Field(default_factory=LanguageConfig)
    
    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    
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