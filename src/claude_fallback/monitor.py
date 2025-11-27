"""JSONL log monitor for Claude Code usage limits."""

import os
import time
from pathlib import Path
from typing import Optional

from claude_fallback.detector import UsageLimitDetector
from claude_fallback.notifier import Notifier
from claude_fallback.config import Config


class LogMonitor:
    """Monitors Claude Code JSONL logs for usage limit events."""

    def __init__(self, config: Config):
        """
        Initialize the monitor.

        Args:
            config: Configuration object
        """
        self.config = config
        self.detector = UsageLimitDetector()
        self.notifier = Notifier(enable_sound=True)
        self.running = False
        self.notified = False  # Track if we've already notified for current session

    def find_active_log(self) -> Optional[Path]:
        """
        Find the most recent JSONL log file for the current directory.

        Returns:
            Path to the log file, or None if not found
        """
        cwd = os.getcwd()
        # Convert path to Claude's project directory naming convention
        # e.g., /Users/foo/project -> -Users-foo-project
        project_name = cwd.replace("/", "-")

        projects_dir = Path.home() / ".claude" / "projects" / project_name

        if not projects_dir.exists():
            return None

        # Find most recent .jsonl file (excluding agent logs)
        jsonl_files = [
            f for f in projects_dir.glob("*.jsonl")
            if not f.name.startswith("agent-")
        ]

        if not jsonl_files:
            return None

        # Return most recently modified file
        return max(jsonl_files, key=lambda f: f.stat().st_mtime)

    def tail_log(self, log_path: Path):
        """
        Tail follow a log file and check for usage limits.

        Args:
            log_path: Path to the JSONL log file
        """
        with open(log_path, "r") as f:
            # Seek to end of file
            f.seek(0, os.SEEK_END)

            while self.running:
                line = f.readline()
                if not line:
                    time.sleep(0.1)  # Wait for new content
                    continue

                # Check for usage limit
                detection = self.detector.check_event(line)
                if detection and not self.notified:
                    self._handle_limit_detected(detection)
                    self.notified = True

    def _handle_limit_detected(self, detection: dict):
        """
        Handle a detected usage limit.

        Args:
            detection: Detection info from detector
        """
        self.notifier.notify(
            title="Claude Code Usage Limit Reached",
            message="Run 'claude-api' to switch to API billing and continue working."
        )

    def start(self):
        """Start monitoring the active log file."""
        self.running = True

        while self.running:
            log_path = self.find_active_log()

            if log_path:
                print(f"Monitoring: {log_path}")
                try:
                    self.tail_log(log_path)
                except FileNotFoundError:
                    # Log file was deleted, find new one
                    pass
                except Exception as e:
                    print(f"Error monitoring log: {e}")
                    time.sleep(5)
            else:
                # No active log found, wait and retry
                time.sleep(2)

    def stop(self):
        """Stop monitoring."""
        self.running = False


def main():
    """Main entry point for the monitor daemon."""
    config = Config.load()
    monitor = LogMonitor(config)

    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()


if __name__ == "__main__":
    main()
