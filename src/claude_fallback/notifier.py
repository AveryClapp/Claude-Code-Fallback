"""Cross-platform notification system."""

import platform
import subprocess
import sys


class Notifier:
    """Send notifications about usage limits."""

    def __init__(self, enable_sound: bool = True):
        """
        Initialize notifier.

        Args:
            enable_sound: Whether to play notification sound
        """
        self.enable_sound = enable_sound
        self.system = platform.system()

    def notify(self, title: str, message: str):
        """
        Send a notification to the user.

        Args:
            title: Notification title
            message: Notification message
        """
        if self.system == "Darwin":
            self._notify_macos(title, message)
        elif self.system == "Linux":
            self._notify_linux(title, message)
        else:
            self._notify_fallback(title, message)

    def _notify_macos(self, title: str, message: str):
        """Send notification on macOS using osascript."""
        try:
            sound_arg = "sound name \"default\"" if self.enable_sound else ""
            script = f'display notification "{message}" with title "{title}" {sound_arg}'
            subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True
            )
        except Exception:
            self._notify_fallback(title, message)

    def _notify_linux(self, title: str, message: str):
        """Send notification on Linux using notify-send."""
        try:
            cmd = ["notify-send", title, message]
            if self.enable_sound:
                cmd.extend(["-u", "critical"])
            subprocess.run(cmd, check=False, capture_output=True)
        except Exception:
            self._notify_fallback(title, message)

    def _notify_fallback(self, title: str, message: str):
        """Fallback notification using terminal output."""
        # Print to stderr so it doesn't interfere with stdout
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  {title}", file=sys.stderr)
        print(f"  {message}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        # Terminal bell
        if self.enable_sound:
            print("\a", file=sys.stderr, end="", flush=True)
