"""Load MCP/routing configuration."""

import os
from pathlib import Path
from typing import Any

import yaml


def load_mcp_config() -> dict[str, Any]:
    """Load config from mcp.yaml. Falls back to env and defaults."""
    config: dict[str, Any] = {
        "primary_model": "gpt-4o-mini",
        "primary_provider": "openai",
        "fallback_model": None,
        "fallback_provider": None,
        "max_retries": 2,
    }

    # Try to find mcp.yaml relative to project root
    base = Path(__file__).resolve().parent.parent.parent.parent
    config_path = base / "config" / "mcp.yaml"
    if config_path.exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f) or {}
        config.update({k: v for k, v in file_config.items() if v is not None})

    # Env overrides
    if os.getenv("PRIMARY_MODEL"):
        config["primary_model"] = os.getenv("PRIMARY_MODEL")
    if os.getenv("PRIMARY_PROVIDER"):
        config["primary_provider"] = os.getenv("PRIMARY_PROVIDER")

    return config
