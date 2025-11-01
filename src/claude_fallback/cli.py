"""Command-line interface for Claude Code Fallback."""

import typer
from rich.console import Console

from claude_fallback.config import Config
from claude_fallback.session import Session

console = Console()

app = typer.Typer(
    help="Automatically switch Claude Code from subscription to API when usage limits are hit."
)


@app.command()
def run():
    """
    Start Claude Code with automatic fallback to API mode.

    This will launch Claude Code in subscription mode and automatically
    switch to API billing when usage limits are detected.
    """
    try:
        # Load and validate configuration
        config = Config.load()
        config.validate()

        # Create and start session
        session = Session(config)
        session.start()
        session.wait()

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Create a config.json file with your settings:[/yellow]")
        console.print("""
{
  "api_key": "sk-ant-api03-...",
  "auto_switch": false,
  "prompt_before_switch": true,
  "cost_limit_per_session": 10.0,
  "log_usage": true,
  "notify_at_percentage": 80,
  "auto_revert_on_reset": true
}
        """)
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")


@app.command()
def status():
    """Check current mode and usage status."""
    console.print("[yellow]Status command not yet implemented[/yellow]")


if __name__ == "__main__":
    app()
