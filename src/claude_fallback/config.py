"""Configuration management for Claude Code Fallback."""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration settings for the fallback tool."""

    def __init__(
        self,
        api_key: str,
        auto_switch: bool = False,
        prompt_before_switch: bool = True,
        cost_limit_per_session: float = 10.0,
        log_usage: bool = True,
        notify_at_percentage: int = 80,
        auto_revert_on_reset: bool = True
    ):
        self.api_key = api_key
        self.auto_switch = auto_switch
        self.prompt_before_switch = prompt_before_switch
        self.cost_limit_per_session = cost_limit_per_session
        self.log_usage = log_usage
        self.notify_at_percentage = notify_at_percentage
        self.auto_revert_on_reset = auto_revert_on_reset

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from JSON file."""
        if config_path is None:
            # Look for config.json in project root
            config_path = Path(__file__).parent.parent.parent / "config.json"

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Config file not found at {config_path}. "
                "Please create config.json based on config.example.json"
            )

        with open(config_path, 'r') as f:
            data = json.load(f)

        return cls(
            api_key=data.get('api_key', ''),
            auto_switch=data.get('auto_switch', False),
            prompt_before_switch=data.get('prompt_before_switch', True),
            cost_limit_per_session=data.get('cost_limit_per_session', 10.0),
            log_usage=data.get('log_usage', True),
            notify_at_percentage=data.get('notify_at_percentage', 80),
            auto_revert_on_reset=data.get('auto_revert_on_reset', True)
        )

    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.api_key or not self.api_key.startswith('sk-ant-'):
            raise ValueError("Invalid API key format. Should start with 'sk-ant-'")

        if self.cost_limit_per_session <= 0:
            raise ValueError("cost_limit_per_session must be positive")

        if not 0 <= self.notify_at_percentage <= 100:
            raise ValueError("notify_at_percentage must be between 0 and 100")

        return True
