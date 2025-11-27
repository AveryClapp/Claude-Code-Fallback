"""Pattern detection for usage limits in Claude Code JSONL logs."""

import json
from typing import Optional, Dict, Any


class UsageLimitDetector:
    """Detects usage limit errors in JSONL log events."""

    def __init__(self):
        """Initialize the detector with known patterns."""
        self.error_patterns = [
            "usage limit",
            "rate limit",
            "usage resets",
            "overloaded_error",
            "rate_limit_error",
        ]

    def check_event(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Check a JSONL log line for usage limit indicators.

        Args:
            line: A single line from the JSONL log file

        Returns:
            Dict with detection info if limit found, None otherwise
        """
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return None

        # Check for explicit error type
        if event.get("type") == "error":
            error = event.get("error", {})
            if self._is_rate_limit_error(error):
                return {
                    "detected": True,
                    "reason": "error_type",
                    "details": error.get("message", "Rate limit error")
                }

        # Check assistant message content
        if event.get("type") == "assistant":
            message = event.get("message", {})
            content = message.get("content", [])

            if self._contains_limit_message(content):
                return {
                    "detected": True,
                    "reason": "message_content",
                    "details": "Usage limit mentioned in response"
                }

        # Check stop reason
        message = event.get("message", {})
        stop_reason = message.get("stop_reason")
        if stop_reason in ["rate_limit", "overloaded"]:
            return {
                "detected": True,
                "reason": "stop_reason",
                "details": f"Stop reason: {stop_reason}"
            }

        return None

    def _is_rate_limit_error(self, error: Dict[str, Any]) -> bool:
        """Check if error object indicates rate limiting."""
        error_type = error.get("type", "").lower()
        error_msg = error.get("message", "").lower()

        return any(pattern in error_type or pattern in error_msg
                   for pattern in self.error_patterns)

    def _contains_limit_message(self, content: list) -> bool:
        """Check if message content mentions usage limits."""
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "").lower()
                if any(pattern in text for pattern in self.error_patterns):
                    return True
        return False
