"""State management for Claude Code Fallback."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class State:
    """Manages persistent state for mode tracking and limit detection."""

    STATE_FILE = Path.home() / ".claude_fallback_state.json"
    FLAG_FILE = Path.home() / ".claude_fallback_active"

    def __init__(
        self,
        mode: str = "subscription",
        limit_detected: bool = False,
        limit_detected_at: Optional[str] = None,
        last_switch_at: Optional[str] = None,
    ):
        self.mode = mode
        self.limit_detected = limit_detected
        self.limit_detected_at = limit_detected_at
        self.last_switch_at = last_switch_at

    @classmethod
    def load(cls) -> "State":
        """Load state from file, creating default if not exists."""
        if not cls.STATE_FILE.exists():
            return cls()

        try:
            with open(cls.STATE_FILE, "r") as f:
                data = json.load(f)
            return cls(
                mode=data.get("mode", "subscription"),
                limit_detected=data.get("limit_detected", False),
                limit_detected_at=data.get("limit_detected_at"),
                last_switch_at=data.get("last_switch_at"),
            )
        except (json.JSONDecodeError, IOError):
            return cls()

    def save(self) -> None:
        """Save current state to file."""
        data = {
            "mode": self.mode,
            "limit_detected": self.limit_detected,
            "limit_detected_at": self.limit_detected_at,
            "last_switch_at": self.last_switch_at,
        }
        with open(self.STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def set_limit_detected(self) -> None:
        """Mark that a usage limit was detected."""
        self.limit_detected = True
        self.limit_detected_at = datetime.now().isoformat()
        self.save()
        # Also create flag file for shell functions
        self.FLAG_FILE.touch()

    def switch_to_api(self) -> None:
        """Switch to API mode."""
        self.mode = "api"
        self.limit_detected = False
        self.last_switch_at = datetime.now().isoformat()
        self.save()
        self._clear_flag()

    def switch_to_subscription(self) -> None:
        """Switch to subscription mode."""
        self.mode = "subscription"
        self.limit_detected = False
        self.last_switch_at = datetime.now().isoformat()
        self.save()
        self._clear_flag()

    def clear_limit(self) -> None:
        """Clear the limit detected flag without switching modes."""
        self.limit_detected = False
        self.save()
        self._clear_flag()

    def _clear_flag(self) -> None:
        """Remove the flag file."""
        if self.FLAG_FILE.exists():
            os.remove(self.FLAG_FILE)

    @classmethod
    def is_limit_active(cls) -> bool:
        """Quick check if limit flag is set (for shell functions)."""
        return cls.FLAG_FILE.exists()

    def __repr__(self) -> str:
        return (
            f"State(mode={self.mode!r}, limit_detected={self.limit_detected}, "
            f"limit_detected_at={self.limit_detected_at!r})"
        )
