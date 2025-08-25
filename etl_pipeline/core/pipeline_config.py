"""
Pipeline-specific configuration management for Strategic Narrative Intelligence

This module extends the base configuration system with pipeline window management,
providing centralized parameter control for all ETL pipeline stages.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Standalone pipeline configuration - no base config dependency needed


@dataclass
class WindowConfig:
    """Configuration for pipeline time windows"""

    keywords_window_hours: int = 72
    clust1_window_hours: int = 72
    clust2_limit: int = 10
    clust3_candidate_window_hours: int = 72
    clust3_library_days: int = 90
    publisher_evidence_days: int = 7
    publisher_parent_days: int = 14


class PipelineConfig:
    """Pipeline-specific configuration manager"""

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._effective_config: Optional[Dict[str, Any]] = None

    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration from YAML file"""
        if self._config is not None:
            return self._config

        # Find config file
        config_paths = [
            Path.cwd() / "config" / "pipeline.yml",
            Path(__file__).parent.parent.parent / "config" / "pipeline.yml",
        ]

        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break

        if not config_file:
            # Return default configuration
            self._config = {
                "environment": "development",
                "keywords": {"window_hours": 72, "mode": "auto"},
                "clust1": {
                    "window_hours": 72,
                    "profile": "strict",
                    "use_hub_assist": True,
                    "hub_pair_cos": 0.90,
                },
                "clust2": {"limit": 10},
                "clust3": {
                    "candidate_window_hours": 72,
                    "library_days": 90,
                    "similarity_threshold": 0.82,
                    "jaccard_threshold": 0.40,
                },
                "gen1": {"enabled": True, "limit": 10},
                "gen2": {"enabled": True, "limit": 10},
                "gen3": {"enabled": True, "limit": 10},
                "publisher": {
                    "evidence_days": 7,
                    "parent_days": 14,
                    "min_articles": 4,
                    "min_sources": 3,
                    "entropy_max": 2.40,
                },
            }
            return self._config

        # Load YAML configuration
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load pipeline config from {config_file}: {e}"
            )

        return self._config

    def _get_effective_config(self) -> Dict[str, Any]:
        """Get effective configuration with environment overrides"""
        if self._effective_config is not None:
            return self._effective_config

        base_config = self._load_config()

        # Get environment from env var or config
        environment = os.getenv(
            "SNI_ENVIRONMENT", base_config.get("environment", "development")
        )

        # Start with base config
        effective = dict(base_config)

        # Apply environment-specific overrides
        if "environments" in base_config and environment in base_config["environments"]:
            env_overrides = base_config["environments"][environment]
            effective = self._deep_merge(effective, env_overrides)

        # Update environment in effective config
        effective["environment"] = environment

        self._effective_config = effective
        return self._effective_config

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict(base)

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation path"""
        config = self._get_effective_config()

        keys = path.split(".")
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        config = self._get_effective_config()
        return config.get(section, {})


# Global pipeline configuration instance
_pipeline_config = None


def get_pipeline_config() -> PipelineConfig:
    """Get global pipeline configuration instance"""
    global _pipeline_config
    if _pipeline_config is None:
        _pipeline_config = PipelineConfig()
    return _pipeline_config


def get(path: str, default: Any = None) -> Any:
    """Get configuration value by dot-notation path"""
    return get_pipeline_config().get(path, default)


def get_section(section: str) -> Dict[str, Any]:
    """Get entire configuration section"""
    return get_pipeline_config().get_section(section)


def get_window_config() -> WindowConfig:
    """Get pipeline window configuration"""
    config = get_pipeline_config()

    return WindowConfig(
        keywords_window_hours=config.get("keywords.window_hours", 72),
        clust1_window_hours=config.get("clust1.window_hours", 72),
        clust2_limit=config.get("clust2.limit", 10),
        clust3_candidate_window_hours=config.get("clust3.candidate_window_hours", 72),
        clust3_library_days=config.get("clust3.library_days", 90),
        publisher_evidence_days=config.get("publisher.evidence_days", 7),
        publisher_parent_days=config.get("publisher.parent_days", 14),
    )


def get_windows_summary() -> Dict[str, Any]:
    """Get summary of all pipeline windows for display"""
    config = get_pipeline_config()

    return {
        "environment": config.get("environment", "unknown"),
        "keywords_window_hours": config.get("keywords.window_hours", "N/A"),
        "clust1_window_hours": config.get("clust1.window_hours", "N/A"),
        "clust2_window_hours": config.get(
            "clust2.limit", "N/A"
        ),  # Note: CLUST-2 uses limit, not hours
        "clust3_candidate_window_hours": config.get(
            "clust3.candidate_window_hours", "N/A"
        ),
        "library_lib_window_days": config.get("clust3.library_days", "N/A"),
        "strategic_filter_window_hours": config.get(
            "clust1.window_hours", "N/A"
        ),  # Same as CLUST-1
        "publisher_evidence_days": config.get("publisher.evidence_days", "N/A"),
        "publisher_parent_days": config.get("publisher.parent_days", "N/A"),
    }
