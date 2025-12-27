"""Command-line interface for Claude Code Fallback."""

import os
import signal
import subprocess
import sys
from pathlib import Path

from claude_fallback import __version__ as VERSION
from claude_fallback.config import Config
from claude_fallback.monitor import PID_FILE, is_already_running
from claude_fallback.state import State


def install_shell_functions() -> None:
    """Install shell functions to user's shell configuration."""
    home = Path.home()
    shell = os.environ.get("SHELL", "")

    if "zsh" in shell:
        rc_file = home / ".zshrc"
    elif "bash" in shell:
        rc_file = home / ".bashrc"
    else:
        print(f"Unsupported shell: {shell}")
        print("Please manually source shell_functions.sh in your shell configuration")
        return

    functions_file = Path(__file__).parent / "shell_functions.sh"

    # Check if already installed
    if rc_file.exists():
        content = rc_file.read_text()
        if "claude_fallback/shell_functions.sh" in content:
            print(f"Shell functions already installed in {rc_file}")
            return

    # Add source line to rc file
    source_line = f'\n# Claude Code Fallback\nsource "{functions_file}"\n'

    with open(rc_file, "a") as f:
        f.write(source_line)

    print(f"Shell functions installed to {rc_file}")
    print("\nTo use immediately, run:")
    print(f"  source {rc_file}")
    print("\nOr restart your terminal.")
    print("\nSet your API key (add to shell config for persistence):")
    print("  export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'")


def start_monitor() -> None:
    """Start the background monitor."""
    daemon_mode = "--daemon" in sys.argv

    if is_already_running():
        print("Monitor is already running.")
        print("Use 'claude-fallback status' to see details.")
        return

    if daemon_mode:
        try:
            # Start as background daemon
            proc = subprocess.Popen(
                [sys.executable, "-m", "claude_fallback.monitor"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            print(f"Monitor started in background (PID: {proc.pid})")
            print("Use 'claude-fallback status' to check status")
            print("Use 'claude-fallback stop' to stop")
        except Exception as e:
            print(f"Failed to start daemon: {e}")
            sys.exit(1)
    else:
        # Run in foreground
        try:
            config = Config.load()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("\nSet your API key:")
            print("  export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'")
            print("\nOr create config.json:")
            print('  {"api_key": "sk-ant-api03-..."}')
            sys.exit(1)
        except ValueError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)

        # Import here to avoid circular import issues
        from claude_fallback.monitor import LogMonitor

        monitor = LogMonitor(config)
        try:
            monitor.start()
        except KeyboardInterrupt:
            pass  # Signal handler in monitor takes care of cleanup


def stop_monitor() -> None:
    """Stop the background monitor."""
    if not PID_FILE.exists():
        print("No monitor running (no PID file found)")
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
    except (ValueError, IOError) as e:
        print(f"Error reading PID file: {e}")
        os.remove(PID_FILE)
        return

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent stop signal to monitor (PID: {pid})")
        # Give it a moment to clean up
        import time

        time.sleep(0.5)
        # Verify it stopped
        try:
            os.kill(pid, 0)
            print("Warning: Monitor may still be stopping...")
        except ProcessLookupError:
            print("Monitor stopped successfully.")
    except ProcessLookupError:
        print("Monitor process not found (may have already stopped)")
        os.remove(PID_FILE)
    except PermissionError:
        print(f"Permission denied stopping PID {pid}")


def show_status() -> None:
    """Show current status of monitor and mode."""
    print(f"Claude Code Fallback v{VERSION}\n")

    # Check monitor status
    if is_already_running():
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()
        print(f"Monitor:  Running (PID: {pid})")
    else:
        print("Monitor:  Not running")

    # Check current mode from state
    state = State.load()
    print(f"Mode:     {state.mode.capitalize()}")

    if state.limit_detected:
        print(f"Status:   Limit detected at {state.limit_detected_at}")
        print("\n  Run 'claude-api' to switch to API billing")
    else:
        print("Status:   OK")

    # Show environment
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("\nEnvironment: ANTHROPIC_API_KEY is set (API mode active)")
    elif os.environ.get("CLAUDE_FALLBACK_API_KEY"):
        print("\nEnvironment: CLAUDE_FALLBACK_API_KEY is set (ready to switch)")
    else:
        print("\nEnvironment: No API key in environment")


def clear_state() -> None:
    """Clear the limit detected state."""
    state = State.load()
    state.clear_limit()
    print("Limit state cleared.")


def show_version() -> None:
    """Print the version number."""
    print(f"Claude Code Fallback v{VERSION}")


def show_help() -> None:
    """Print usage instructions."""
    help_text = f"""Claude Code Fallback v{VERSION}

Automatically switch to API billing when Claude Code hits usage limits.

Usage:
  claude-fallback <command> [options]

Commands:
  install     Install shell functions (claude-api, claude-sub)
  start       Start monitor in foreground
  start --daemon  Start monitor in background
  stop        Stop the background monitor
  status      Show current status
  clear       Clear limit detected state
  version     Show version
  help        Show this help

Shell Commands (after install):
  claude-api  Switch to API billing mode
  claude-sub  Switch to subscription mode

Setup:
  1. Set your API key:
     export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'

  2. Install shell functions:
     claude-fallback install

  3. Start the monitor:
     claude-fallback start --daemon

  4. Use Claude normally - you'll be notified when limits are hit
"""
    print(help_text)


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]

    commands = {
        "install": install_shell_functions,
        "start": start_monitor,
        "stop": stop_monitor,
        "status": show_status,
        "clear": clear_state,
        "version": show_version,
        "v": show_version,
        "help": show_help,
        "h": show_help,
        "-h": show_help,
        "--help": show_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print("Run 'claude-fallback help' for usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
