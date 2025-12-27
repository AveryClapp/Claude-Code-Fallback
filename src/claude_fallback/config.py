"""Configuration management for Claude Code Fallback."""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration settings for the fallback tool."""

    ENV_VAR_NAME = "CLAUDE_FALLBACK_API_KEY"

    def __init__(self, api_key: str, auto_restart: bool = False):
        self.api_key = api_key
        self.auto_restart = auto_restart

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variable or JSON file.

        Priority:
        1. CLAUDE_FALLBACK_API_KEY environment variable
        2. config.json file

        auto_restart can be set via:
        - CLAUDE_FALLBACK_AUTO_RESTART=1 environment variable
        - "auto_restart": true in config.json
        """
        auto_restart = os.environ.get("CLAUDE_FALLBACK_AUTO_RESTART", "").lower() in (
            "1",
            "true",
            "yes",
        )

        # First, try environment variable for API key
        api_key = os.environ.get(cls.ENV_VAR_NAME)
        if api_key:
            return cls(api_key=api_key, auto_restart=auto_restart)

        # Fall back to config.json
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.json"

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"API key not found. Either:\n"
                f"  1. Set {cls.ENV_VAR_NAME} environment variable, or\n"
                f"  2. Create config.json with your API key"
            )

        with open(config_path, "r") as f:
            data = json.load(f)

        api_key = data.get("api_key", "")
        if not api_key:
            raise ValueError("No api_key found in config.json")

        # Config file can also set auto_restart
        if not auto_restart:
            auto_restart = data.get("auto_restart", False)

        return cls(api_key=api_key, auto_restart=auto_restart)

    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.api_key or not self.api_key.startswith("sk-ant-"):
            raise ValueError("Invalid API key format. Should start with 'sk-ant-'")
        return True
