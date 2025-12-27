"""JSONL log monitor for Claude Code usage limits."""

import glob
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from claude_fallback.config import Config
from claude_fallback.detector import UsageLimitDetector
from claude_fallback.notifier import Notifier
from claude_fallback.state import State

# PID file location
PID_FILE = Path.home() / ".claude_fallback.pid"
ERROR_LOG = Path.home() / ".claude_fallback_error.log"


def log_error(message: str) -> None:
    """Log error with timestamp to error log file."""
    timestamp = datetime.now().isoformat()
    with open(ERROR_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


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
        self.state = State.load()
        self.running = False
        self.notified_for_session = False
        self.base_path = Path.home() / ".claude" / "projects"
        self.current_log: Optional[Path] = None
        self.last_pos = 0

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        print(f"\nReceived {sig_name}, shutting down...")
        self.stop()

    def find_latest_log(self) -> Optional[Path]:
        """Finds the most recently modified .jsonl file across all projects."""
        pattern = str(self.base_path / "**" / "sessions" / "*.jsonl")
        log_files = glob.glob(pattern, recursive=True)
        if not log_files:
            return None
        return Path(max(log_files, key=os.path.getmtime))

    def _check_for_updates(self) -> None:
        """Check for new log entries and detect usage limits."""
        if self.current_log is None:
            return

        try:
            # Check if file still exists
            if not self.current_log.exists():
                self.current_log = None
                self.last_pos = 0
                return

            with open(self.current_log, "r") as f:
                f.seek(self.last_pos)
                lines = f.readlines()
                self.last_pos = f.tell()

                for line in lines:
                    if not line.strip():
                        continue

                    detection = self.detector.check_event(line)
                    if detection and not self.notified_for_session:
                        self._handle_limit_detected(detection)

        except PermissionError as e:
            log_error(f"Permission denied reading log: {e}")
            self.current_log = None
        except IOError as e:
            log_error(f"IO error reading log: {e}")
            self.current_log = None

    def _handle_limit_detected(self, detection: dict) -> None:
        """Handle a detected usage limit."""
        self.notified_for_session = True

        # Update state
        self.state.set_limit_detected()

        # Get details for notification
        details = detection.get("details", "Usage limit reached")

        if self.config.auto_restart:
            # Auto-restart mode: kill Claude and restart with API key
            print(f"\n[LIMIT DETECTED] {details}")
            print("Auto-restarting Claude in API mode...")

            self.notifier.notify(
                title="Claude Code Usage Limit",
                message="Auto-switching to API mode...",
            )

            self._auto_restart_claude()
        else:
            # Manual mode: just notify
            self.notifier.notify(
                title="Claude Code Usage Limit",
                message=f"{details}\nRun 'claude-api' to switch to API mode",
            )

            print(f"\n[LIMIT DETECTED] {details}")
            print("Run 'claude-api' to switch to API billing mode")

    def _auto_restart_claude(self) -> None:
        """Kill running Claude process and restart with API key."""
        try:
            # Find Claude process and its working directory
            result = subprocess.run(
                ["pgrep", "-f", "claude"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print("No Claude process found to restart")
                return

            pids = result.stdout.strip().split("\n")
            claude_pid = None
            working_dir = None

            for pid in pids:
                if not pid:
                    continue
                try:
                    # Get working directory of the process
                    # On macOS, use lsof; on Linux, use /proc
                    if sys.platform == "darwin":
                        lsof_result = subprocess.run(
                            ["lsof", "-p", pid, "-Fn"],
                            capture_output=True,
                            text=True,
                        )
                        for line in lsof_result.stdout.split("\n"):
                            if line.startswith("n") and line.endswith("cwd"):
                                continue
                            if line.startswith("n/"):
                                # This is a file path, check if it's cwd
                                pass
                        # Fallback: use pwdx equivalent
                        cwd_result = subprocess.run(
                            ["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"],
                            capture_output=True,
                            text=True,
                        )
                        for line in cwd_result.stdout.split("\n"):
                            if line.startswith("n/"):
                                working_dir = line[1:]
                                claude_pid = int(pid)
                                break
                    else:
                        # Linux: read from /proc
                        cwd_link = f"/proc/{pid}/cwd"
                        if os.path.exists(cwd_link):
                            working_dir = os.readlink(cwd_link)
                            claude_pid = int(pid)
                            break
                except (ValueError, OSError):
                    continue

            if claude_pid and working_dir:
                # Kill the Claude process
                print(f"Stopping Claude (PID: {claude_pid})...")
                os.kill(claude_pid, signal.SIGTERM)
                time.sleep(1)

                # Start new Claude with API key
                print(f"Starting Claude in API mode in {working_dir}...")
                env = os.environ.copy()
                env["ANTHROPIC_API_KEY"] = self.config.api_key

                subprocess.Popen(
                    ["claude"],
                    cwd=working_dir,
                    env=env,
                    start_new_session=True,
                )

                # Update state
                self.state.switch_to_api()
                print("Claude restarted in API mode")
            else:
                print("Could not determine Claude working directory")
                print("Run 'claude-api' manually to switch")

        except Exception as e:
            log_error(f"Auto-restart failed: {e}")
            print(f"Auto-restart failed: {e}")
            print("Run 'claude-api' manually to switch")

    def start(self) -> None:
        """Start the monitoring loop."""
        print(f"Watching {self.base_path} for Claude Code sessions...")
        print("Press Ctrl+C to stop\n")

        self.running = True

        while self.running:
            try:
                latest = self.find_latest_log()

                # Switch to new session if detected
                if latest and latest != self.current_log:
                    print(f"Monitoring session: {latest.name}")
                    self.current_log = latest
                    self.last_pos = os.path.getsize(latest)
                    self.notified_for_session = False  # Reset for new session

                if self.current_log:
                    self._check_for_updates()

                time.sleep(2)  # Polling interval

            except Exception as e:
                log_error(f"Monitor loop error: {e}")
                time.sleep(5)  # Back off on error

    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        print("Monitor stopped.")


def write_pid_file() -> None:
    """Write current PID to file."""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid_file() -> None:
    """Remove PID file on exit."""
    if PID_FILE.exists():
        os.remove(PID_FILE)


def is_already_running() -> bool:
    """Check if another monitor instance is already running."""
    if not PID_FILE.exists():
        return False

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        # Check if process is actually running
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        # Process not running or invalid PID - clean up stale file
        remove_pid_file()
        return False


def main() -> None:
    """Entry point for the monitor process (foreground or daemon)."""
    # Check for existing instance
    if is_already_running():
        print("Monitor is already running. Use 'claude-fallback stop' to stop it.")
        sys.exit(1)

    try:
        config = Config.load()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Write PID file
    write_pid_file()

    try:
        monitor = LogMonitor(config)
        monitor.start()
    except Exception as e:
        log_error(f"Fatal error: {e}")
        raise
    finally:
        remove_pid_file()


if __name__ == "__main__":
    main()
