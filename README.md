# Claude Code Fallback

[![PyPI version](https://badge.fury.io/py/claude-code-fallback.svg)](https://pypi.org/project/claude-code-fallback/)
[![Downloads](https://pepy.tech/badge/claude-code-fallback)](https://pepy.tech/project/claude-code-fallback)

Automatically switch from your Claude subscription to API billing when you hit usage limits, keeping your coding session uninterrupted.

## Why This Exists

Claude Code usage is shared with your web Claude.ai usage and resets every 5 hours. When you hit these limits during an active coding session, you're forced to either wait or manually switch to API billing. This tool automates that transition so you never lose momentum.

## How It Works

A lightweight background monitor watches Claude Code's JSONL logs for usage limit errors:

1. You run Claude Code normally (no wrapper needed)
2. Background monitor detects when you've hit subscription limits by parsing `~/.claude/projects/` logs
3. You receive a notification: "Usage limit reached! Run 'claude-api' to switch"
4. You exit Claude Code and run `claude-api` to restart with API billing
5. Continue working seamlessly in the same directory
6. Optionally run `claude-sub` to switch back to subscription mode

## Features

- **Log-Based Detection**: Monitors JSONL logs for usage limit errors (works in tmux/ssh/any terminal)
- **Simple Shell Functions**: Switch modes with `claude-api` and `claude-sub` commands
- **Native Notifications**: OS-level alerts when limits are detected
- **Directory Preservation**: Automatically restarts Claude in your working directory
- **No Process Wrapping**: Claude Code runs normally, no PTY manipulation

## What Works

**Automatic limit detection** - Monitors Claude Code for usage limit errors
**Seamless API fallback** - Switches to API mode without losing context
**Smart notifications** - Native OS alerts when usage limits are detected

## Architecture

The new architecture uses JSONL log monitoring instead of PTY wrapping:

- **`monitor.py`** - Watches `~/.claude/projects/[project]/[session].jsonl` for usage limit events
- **`detector.py`** - Parses JSON events and detects usage limit patterns
- **`notifier.py`** - Cross-platform notifications (macOS/Linux)
- **`config.py`** - Simple configuration (API key, notification preferences)
- **`shell_functions.sh`** - Shell functions for `claude-api` and `claude-sub`

## Installation

### With mise + uv (Recommended)

This project uses [mise](https://mise.jdx.dev/) for tool version management and [uv](https://docs.astral.sh/uv/) for fast Python dependency management.

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-code-api-fallback.git
cd claude-code-api-fallback

# Install mise (if not already installed)
# macOS/Linux:
curl https://mise.run | sh

# Install dependencies (mise will automatically set up Python 3.12 and create a venv with uv)
mise install

# Configure your settings
cp config.example.json config.json
vim config.json
```

### Installation Verification

After installation, verify everything is working:

```bash
# Check the tool is installed
claude-fallback version

# Verify configuration
claude-fallback status

# Test the wrapper (won't start Claude Code if limits already hit)
claude-fallback help
```

Expected output:

- Version should match the latest PyPI release
- Status should show your current mode (subscription or API)
- Help should display all available commands

## Configuration

Edit `config.json` with your preferences:

```json
{
  "api_key": "sk-ant-api03-...",
  "auto_switch": false,
  "prompt_before_switch": true,
  "cost_limit_per_session": 10.0,
  "log_usage": true,
  "notify_at_percentage": 80,
  "auto_revert_on_reset": true
}
```

### Configuration Options

- `api_key`: Your Anthropic API key (get one from console.anthropic.com)
- `auto_switch`: Automatically switch without prompting (default: false)
- `prompt_before_switch`: Ask before switching to API mode (default: true)
- `cost_limit_per_session`: Maximum API spend per session in USD
- `log_usage`: Track and log all API usage (default: true)
- `notify_at_percentage`: Alert when reaching X% of subscription limits
- `auto_revert_on_reset`: Switch back to subscription when limits reset

## Usage

### Setup

```bash
# Install shell functions (adds to ~/.zshrc or ~/.bashrc)
claude-fallback install

# Start background monitor
claude-fallback start

# Check status
claude-fallback status
```

### Daily Workflow

```bash
# Start Claude Code normally
claude

# When you hit limits, you'll see a notification
# Exit Claude Code (Ctrl+D or type 'exit')

# Switch to API mode
claude-api

# Continue working...

# Later, switch back to subscription
claude-sub
```

### Shell Functions

The installer adds these functions to your shell:

```bash
# Switch to API billing
claude-api() {
  export ANTHROPIC_API_KEY="your-key"
  exec claude
}

# Switch to subscription billing
claude-sub() {
  unset ANTHROPIC_API_KEY
  exec claude
}
```

## Real-World Usage

My typical workflow:

1. Start a coding session with `claude` (runs normally, no wrapper)
2. Background monitor watches the session logs
3. Work normally until I hit subscription limits
4. Get a native OS notification: "Usage limit reached! Run 'claude-api'"
5. Exit Claude Code and run `claude-api` to switch
6. Continue working in the same directory
7. When done with heavy work, run `claude-sub` to switch back

The background monitor is lightweight (just tailing a log file) and works perfectly in tmux, ssh sessions, or any terminal environment. I've found that subscription + API fallback costs about $5-10/month in API usage, far less than going API-only.

Usage varies based on codebase size, conversation length, and model choice (Opus uses ~5x more than Sonnet).

## Requirements

- Python 3.8+ (Python 3.12 recommended with mise)
- Active Claude Pro or Max subscription
- Anthropic API key (for fallback)
- Claude Code installed
- **macOS or Linux** (Windows support via WSL)
- Optional: [mise](https://mise.jdx.dev/) for streamlined setup

## Security Notes

- Store your API key securely (use environment variables or encrypted config)
- The tool only reads/writes the `ANTHROPIC_API_KEY` environment variable
- All usage logs are stored locally
- Your API key is never transmitted except to Anthropic's API

## Roadmap

- [ ] Cost prediction based on codebase analysis

## Contributing

Contributions welcome! This project addresses a real need expressed in [Anthropic's GitHub Issue #2944](https://github.com/anthropics/claude-code/issues/2944).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

This is an unofficial tool not affiliated with Anthropic. Use at your own risk. Always monitor your API usage and costs. The tool respects Anthropic's terms of service by only switching between legitimate authentication methods.

## License

APACHE 2.0 License - see LICENSE file for details

## Acknowledgments

- Inspired by [Issue #2944](https://github.com/anthropics/claude-code/issues/2944) on the claude-code repository
- Built for developers who need uninterrupted coding sessions
- Thanks to the Anthropic team for building Claude Code

---
