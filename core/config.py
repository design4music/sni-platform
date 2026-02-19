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
    v3_p2_max_titles: Optional[int] = Field(default=None, env="V3_P2_MAX_TITLES")

    # Phase 3.1: Event Label + Signal Extraction (ELO v2.0)
    v3_p31_temperature: float = Field(default=0.1, env="V3_P31_TEMPERATURE")
    v3_p31_max_tokens: int = Field(default=4000, env="V3_P31_MAX_TOKENS")
    v3_p31_batch_size: int = Field(default=25, env="V3_P31_BATCH_SIZE")
    v3_p31_concurrency: int = Field(default=5, env="V3_P31_CONCURRENCY")
    v3_p31_timeout_seconds: int = Field(default=180, env="V3_P31_TIMEOUT_SECONDS")
    v3_p31_max_titles: int = Field(default=500, env="V3_P31_MAX_TITLES")

    # Phase 3.3: Intel Gating + Track Classification (LLM-based)
    v3_p33_temperature: float = Field(default=0.0, env="V3_P33_TEMPERATURE")
    v3_p33_max_tokens_gating: int = Field(default=500, env="V3_P33_MAX_TOKENS_GATING")
    v3_p33_max_tokens_tracks: int = Field(default=500, env="V3_P33_MAX_TOKENS_TRACKS")
    v3_p33_centroid_batch_size: int = Field(
        default=50, env="V3_P33_CENTROID_BATCH_SIZE"
    )
    v3_p33_concurrency: int = Field(default=8, env="V3_P33_CONCURRENCY")
    v3_p33_timeout_seconds: int = Field(default=300, env="V3_P33_TIMEOUT_SECONDS")
    v3_p33_max_titles: Optional[int] = Field(default=1000, env="V3_P33_MAX_TITLES")

    # Phase 4: Events Digest and Summary Generation
    v3_p4_batch_size: int = Field(default=70, env="V3_P4_BATCH_SIZE")
    v3_p4_min_titles: int = Field(default=30, env="V3_P4_MIN_TITLES")
    v3_p4_max_concurrent: int = Field(default=5, env="V3_P4_MAX_CONCURRENT")
    v3_p4_temperature: float = Field(default=0.5, env="V3_P4_TEMPERATURE")
    v3_p4_max_tokens: int = Field(default=500, env="V3_P4_MAX_TOKENS")
    v3_p4_timeout_seconds: int = Field(default=180, env="V3_P4_TIMEOUT_SECONDS")

    # Phase 4.5: CTM Summaries
    v3_p45_cooldown_hours: int = Field(default=24, env="V3_P45_COOLDOWN_HOURS")

    # Phase 4.5a: Event Summaries
    v3_p45a_max_events: int = Field(default=500, env="V3_P45A_MAX_EVENTS")
    v3_p45a_interval: int = Field(default=900, env="V3_P45A_INTERVAL")  # 15 min

    # Phase 5: CTM Narrative Extraction
    v3_p5_min_titles: int = Field(default=100, env="V3_P5_MIN_TITLES")
    v3_p5_refresh_growth: int = Field(default=100, env="V3_P5_REFRESH_GROWTH")
    v3_p5_interval: int = Field(default=86400, env="V3_P5_INTERVAL")  # 24h

    # Phase 5: Event Narrative Extraction
    v3_p5e_min_sources: int = Field(default=100, env="V3_P5E_MIN_SOURCES")
    v3_p5e_refresh_growth: int = Field(default=50, env="V3_P5E_REFRESH_GROWTH")

    # Phase 6: RAI (Risk Assessment Intelligence) Analysis
    rai_api_url: str = Field(
        default="https://rai-backend-ldy4.onrender.com/api/v1/analyze",
        env="RAI_API_URL",
    )
    rai_worldbrief_url: str = Field(
        default="https://rai-backend-ldy4.onrender.com/api/v1/worldbrief/analyze",
        env="RAI_WORLDBRIEF_URL",
    )
    rai_signals_url: str = Field(
        default="https://rai-backend-ldy4.onrender.com/api/v1/worldbrief/signals",
        env="RAI_SIGNALS_URL",
    )
    rai_api_key: Optional[str] = Field(default=None, env="RAI_API_KEY")
    rai_timeout_seconds: int = Field(default=120, env="RAI_TIMEOUT_SECONDS")
    rai_enabled: bool = Field(default=False, env="RAI_ENABLED")

    # Events Generation (bucket pass-through, no clustering yet)
    events_min_ctm_titles: int = Field(default=10, env="EVENTS_MIN_CTM_TITLES")

    # Database Tables
    v3_centroids_table: str = Field(default="centroids_v3", env="V3_CENTROIDS_TABLE")
    v3_taxonomy_table: str = Field(default="taxonomy_v3", env="V3_TAXONOMY_TABLE")
    v3_ctm_table: str = Field(default="ctm", env="V3_CTM_TABLE")
    v3_titles_table: str = Field(default="titles_v3", env="V3_TITLES_TABLE")

    # Language Support
    primary_language: str = Field(default="en", env="PRIMARY_LANGUAGE")
    supported_languages: str = Field(
        default="en,es,fr,de,ru,zh,ar", env="SUPPORTED_LANGUAGES"
    )

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


# =============================================================================
# SIGNAL EXTRACTION & CLUSTERING CONSTANTS
# =============================================================================

# Signal types extracted by Phase 3.1 (ELO) - matches title_labels columns
SIGNAL_TYPES = [
    "persons",
    "orgs",
    "places",
    "commodities",
    "policies",
    "systems",
    "named_events",
]

# High-frequency persons to exclude from clustering anchor signals
# These appear across many unrelated stories and reduce clustering quality
HIGH_FREQ_PERSONS = {"TRUMP", "BIDEN", "PUTIN", "ZELENSKY", "XI"}

# Signal weights by track - higher weight = more discriminating for that track
TRACK_WEIGHTS = {
    "geo_economy": {
        "persons": 1.0,  # Moderate - economic actors matter
        "orgs": 3.0,  # Very high - companies, central banks key
        "places": 1.0,  # Moderate
        "commodities": 3.0,  # Very high - oil, gold, wheat distinguish stories
        "policies": 2.0,  # High - tariffs, sanctions key
        "systems": 2.0,  # High - SWIFT, trade systems
        "named_events": 1.5,  # Moderate - Davos, G20
    },
    "geo_security": {
        "persons": 1.5,  # Moderate - military leaders
        "orgs": 2.0,  # High - NATO, militaries
        "places": 3.0,  # Very high - Crimea, Gaza distinguish conflicts
        "commodities": 0.5,  # Low
        "policies": 1.5,  # Moderate - defense agreements
        "systems": 2.5,  # High - S-400, weapons systems
        "named_events": 1.0,  # Moderate
    },
    "geo_politics": {
        "persons": 2.5,  # Very high - political actors key
        "orgs": 1.5,  # Moderate - parties, institutions
        "places": 1.5,  # Moderate
        "commodities": 0.5,  # Low
        "policies": 2.0,  # High - elections, legislation
        "systems": 0.5,  # Low
        "named_events": 2.0,  # High - elections, summits
    },
    "default": {
        "persons": 1.5,
        "orgs": 1.5,
        "places": 1.5,
        "commodities": 1.5,
        "policies": 1.5,
        "systems": 1.5,
        "named_events": 1.5,
    },
}

# Discriminator signals by track - different values in these types PENALIZE similarity
# This prevents merging FED stories with JPMORGAN stories just because both mention TRUMP
# Values closer to 1.0 = stronger penalty (0.8 = 80% reduction in similarity)
TRACK_DISCRIMINATORS = {
    "geo_economy": {"orgs": 0.8, "commodities": 0.5},
    "geo_security": {"places": 0.7, "systems": 0.5},
    "geo_politics": {"persons": 0.5},
    "default": {},
}


# Circuit breaker: max API errors before excluding a title from queue
MAX_API_ERRORS = 3

# (action_class, domain) combos with <2% block rate (n>=10)
# Titles matching these skip LLM gating and go straight to track assignment
GATE_WHITELIST = frozenset(
    {
        ("ALLIANCE_COORDINATION", "ECONOMY"),
        ("ALLIANCE_COORDINATION", "FOREIGN_POLICY"),
        ("ALLIANCE_COORDINATION", "GOVERNANCE"),
        ("ALLIANCE_COORDINATION", "SECURITY"),
        ("ALLIANCE_COORDINATION", "TECHNOLOGY"),
        ("CAPABILITY_TRANSFER", "ECONOMY"),
        ("CAPABILITY_TRANSFER", "SECURITY"),
        ("CAPABILITY_TRANSFER", "TECHNOLOGY"),
        ("COLLECTIVE_PROTEST", "GOVERNANCE"),
        ("COLLECTIVE_PROTEST", "SOCIETY"),
        ("DIPLOMATIC_PRESSURE", "FOREIGN_POLICY"),
        ("DIPLOMATIC_PRESSURE", "GOVERNANCE"),
        ("DIPLOMATIC_PRESSURE", "SECURITY"),
        ("ECONOMIC_DISRUPTION", "ECONOMY"),
        ("ECONOMIC_PRESSURE", "ECONOMY"),
        ("ECONOMIC_PRESSURE", "FOREIGN_POLICY"),
        ("INFORMATION_INFLUENCE", "GOVERNANCE"),
        ("INFORMATION_INFLUENCE", "MEDIA"),
        ("INFORMATION_INFLUENCE", "SECURITY"),
        ("INFRASTRUCTURE_DEVELOPMENT", "ECONOMY"),
        ("INFRASTRUCTURE_DEVELOPMENT", "TECHNOLOGY"),
        ("INSTITUTIONAL_RESISTANCE", "GOVERNANCE"),
        ("LEGAL_CONTESTATION", "GOVERNANCE"),
        ("LEGAL_RULING", "GOVERNANCE"),
        ("LEGAL_RULING", "SOCIETY"),
        ("LEGISLATIVE_DECISION", "ECONOMY"),
        ("LEGISLATIVE_DECISION", "GOVERNANCE"),
        ("LEGISLATIVE_DECISION", "SECURITY"),
        ("LEGISLATIVE_DECISION", "SOCIETY"),
        ("MILITARY_OPERATION", "SECURITY"),
        ("MULTILATERAL_ACTION", "ECONOMY"),
        ("MULTILATERAL_ACTION", "FOREIGN_POLICY"),
        ("MULTILATERAL_ACTION", "GOVERNANCE"),
        ("MULTILATERAL_ACTION", "SECURITY"),
        ("POLICY_CHANGE", "ECONOMY"),
        ("POLICY_CHANGE", "FOREIGN_POLICY"),
        ("POLICY_CHANGE", "GOVERNANCE"),
        ("POLICY_CHANGE", "SECURITY"),
        ("POLICY_CHANGE", "SOCIETY"),
        ("POLICY_CHANGE", "TECHNOLOGY"),
        ("POLITICAL_PRESSURE", "FOREIGN_POLICY"),
        ("POLITICAL_PRESSURE", "GOVERNANCE"),
        ("REGULATORY_ACTION", "ECONOMY"),
        ("REGULATORY_ACTION", "TECHNOLOGY"),
        ("RESOURCE_ALLOCATION", "ECONOMY"),
        ("RESOURCE_ALLOCATION", "SECURITY"),
        ("SANCTION_ENFORCEMENT", "ECONOMY"),
        ("SANCTION_ENFORCEMENT", "FOREIGN_POLICY"),
        ("SECURITY_INCIDENT", "SECURITY"),
        ("SECURITY_INCIDENT", "SOCIETY"),
        ("SOCIAL_INCIDENT", "SOCIETY"),
        ("STRATEGIC_REALIGNMENT", "FOREIGN_POLICY"),
        ("STRATEGIC_REALIGNMENT", "GOVERNANCE"),
        ("STRATEGIC_REALIGNMENT", "SECURITY"),
    }
)


def get_track_weights(track: str) -> dict:
    """Get signal weights for a track."""
    return TRACK_WEIGHTS.get(track, TRACK_WEIGHTS["default"])


def get_track_discriminators(track: str) -> dict:
    """Get discriminator penalties for a track."""
    return TRACK_DISCRIMINATORS.get(track, TRACK_DISCRIMINATORS["default"])
