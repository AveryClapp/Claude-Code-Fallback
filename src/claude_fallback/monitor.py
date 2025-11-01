"""Background process monitor to detect Claude Code usage limit errors."""

import os
import sys
import threading
import time
from typing import Optional, IO

from rich.console import Console

console = Console()


class Monitor:
    """Monitors Claude Code process output for usage limits and errors."""

    def __init__(self, process, output_fd: Optional[int] = None):
        """
        Initialize monitor.

        Args:
            process: The Claude Code process
            output_fd: File descriptor to read output from (for pty mode)
        """
        self.process = process
        self.output_fd = output_fd
        self.should_switch = False
        self.process_exited = False
        self.monitoring_thread = None
        self.running = False
        self.output_buffer = []

    def start(self):
        """Start monitoring in a background thread."""
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        console.print("[dim]Monitor started[/dim]")

    def _monitor_loop(self):
        """Background thread that reads output and checks for patterns."""
        while self.running:
            self._read_and_check_output()
            self._check_process_health()
            time.sleep(0.01)  # Small sleep to avoid busy-waiting

    def _read_and_check_output(self):
        """Read output from pty, display it, and check for usage limits."""
        if self.output_fd is None:
            return

        try:
            # Non-blocking read from the pty
            data = os.read(self.output_fd, 4096)
            if data:
                # Decode and display to user
                text = data.decode('utf-8', errors='ignore')
                sys.stdout.write(text)
                sys.stdout.flush()

                # Check for usage limit pattern (more specific)
                # Claude Code shows messages like "Usage resets in X hours"
                text_lower = text.lower()
                if ('usage' in text_lower and 'resets' in text_lower) or \
                   'usage limit reached' in text_lower or \
                   'rate limit' in text_lower:
                    # Give visual indication
                    console.print("\n[yellow]⚠ Usage limit detected![/yellow]")
                    self.should_switch = True

        except OSError:
            # No data available or error reading
            pass
        except Exception as e:
            # Ignore other errors during reading
            pass

    def _check_process_health(self):
        """Check if process crashed or exited."""
        if self.process.poll() is not None:
            self.process_exited = True
            self.running = False

    def get_status(self):
        """
        Called by Session.wait() to determine action.

        Returns:
            'exited' - Process ended, user quit
            'switch' - Usage limit detected, need to switch to API
            'continue' - Everything normal, keep running
        """
        if self.process_exited:
            return "exited"
        elif self.should_switch:
            return "switch"
        else:
            return "continue"

    def reset_switch_flag(self):
        """Reset the switch flag after handling."""
        self.should_switch = False

    def stop(self):
        """Stop monitoring thread."""
        self.running = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
