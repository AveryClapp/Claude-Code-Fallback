"""Command-line interface for Claude Code Fallback."""

import os
import sys
from pathlib import Path

from claude_fallback.config import Config
from claude_fallback.monitor import LogMonitor


def install_shell_functions():
    """Install shell functions to user's shell configuration."""
    # Find user's shell config file
    home = Path.home()
    shell = os.environ.get("SHELL", "")

    if "zsh" in shell:
        rc_file = home / ".zshrc"
    elif "bash" in shell:
        rc_file = home / ".bashrc"
    else:
        print(f"Unsupported shell: {shell}")
        print("Please manually add shell_functions.sh to your shell configuration")
        return

    # Path to shell_functions.sh
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
    print("\nOr restart your terminal")
    print("\nDon't forget to set your API key:")
    print("  export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'")


def start_monitor():
    """Start the background monitor."""
    try:
        config = Config.load()
        monitor = LogMonitor(config)
        print("Starting Claude Code monitor...")
        print("Press Ctrl+C to stop")
        monitor.start()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nCreate a config.json file with your settings:")
        print("""
{
  "api_key": "sk-ant-api03-...",
  "log_usage": true
}
        """)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()


def show_status():
    """Show current status."""
    import subprocess

    # Check if monitor is running
    result = subprocess.run(
        ["pgrep", "-f", "python.*claude_fallback.*monitor"],
        capture_output=True
    )

    if result.returncode == 0:
        print("Monitor: Running")
    else:
        print("Monitor: Not running")

    # Check current mode
    if "ANTHROPIC_API_KEY" in os.environ:
        print("Mode: API")
    else:
        print("Mode: Subscription")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: claude-fallback <command>")
        print("\nCommands:")
        print("  install  - Install shell functions to your shell configuration")
        print("  start    - Start the background monitor")
        print("  status   - Show current status")
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        install_shell_functions()
    elif command == "start":
        start_monitor()
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
