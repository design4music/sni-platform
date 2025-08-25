"""
Pipeline configuration loader for Strategic Narrative Intelligence

Simplified centralized configuration matching the operational spec:
- Different window types for different stages (library=30d, strategic=300h, current=72h)
- Environment overrides (production, staging, development)
- CLI argument defaults with config fallback
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

# Simple configuration loader matching the operational spec


def load_config():
    """Load pipeline configuration from YAML file"""
    config_path = os.getenv("SNI_CONFIG", "config/pipeline.yml")

    # Try multiple paths for config file
    config_paths = [
        Path.cwd() / config_path,
        Path(__file__).parent.parent.parent / config_path,
        Path.cwd() / "config" / "pipeline.yml",
    ]

    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break

    if not config_file:
        # Return safe defaults if no config found
        return {
            "keywords": {"window_hours": 72},
            "library": {"lib_window_days": 30, "hubs_top_n": 12, "df_min": 2},
            "strategic_filter": {"strategic_window_hours": 300},
            "clust1": {
                "window_hours": 72,
                "use_hub_assist": True,
                "hub_pair_cos": 0.90,
            },
            "clust2": {
                "window_hours": 72,
                "input_min_cluster_size": 4,
                "input_min_sources": 3,
            },
            "clust3": {"candidate_window_hours": 72, "similarity_threshold": 0.82},
            "publisher": {
                "evidence_days": 7,
                "parent_days": 14,
                "min_articles": 4,
                "min_sources": 3,
                "entropy_max": 2.40,
            },
            "gen1": {"enabled": True},
            "gen2": {"enabled": True},
            "gen3": {"enabled": True},
        }

    # Load YAML configuration
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config from {config_file}: {e}")

    # Apply environment-specific overrides
    environment = os.getenv("SNI_ENVIRONMENT", "development")  # Default to development
    if "environments" in config and environment in config["environments"]:
        env_overrides = config["environments"][environment]
        config = deep_merge(config, env_overrides)

    return config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


# Global configuration instance
CFG = load_config()


def get(path: str, default: Any = None) -> Any:
    """Get configuration value by dot-notation path"""
    current = CFG
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current if current is not None else default


def get_windows_summary() -> Dict[str, Any]:
    """Get summary of all pipeline windows for display (matching spec)"""
    environment = os.getenv("SNI_ENVIRONMENT", "development")

    return {
        "environment": environment,
        "keywords_window_hours": get("keywords.window_hours", 72),
        "library_lib_window_days": get("library.lib_window_days", 30),
        "strategic_filter_window_hours": get(
            "strategic_filter.strategic_window_hours", 300
        ),
        "clust1_window_hours": get("clust1.window_hours", 72),
        "clust2_window_hours": get("clust2.window_hours", 72),
        "clust3_candidate_window_hours": get("clust3.candidate_window_hours", 72),
        "publisher_evidence_days": get("publisher.evidence_days", 7),
        "publisher_parent_days": get("publisher.parent_days", 14),
    }
