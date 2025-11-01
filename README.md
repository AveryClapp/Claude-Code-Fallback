# Claude Code Fallback

Automatically switch from your Claude subscription to API billing when you hit usage limits, keeping your coding session uninterrupted.

## Why This Exists

Claude Code usage is shared with your web Claude.ai usage and resets every 5 hours. When you hit these limits during an active coding session, you're forced to either wait or manually switch to API billing. This tool automates that transition so you never lose momentum.

## How It Works

The tool monitors your Claude Code session for usage limit errors and automatically:

1. Detects when you've hit your subscription usage limits
2. Prompts you to switch to API mode (or switches automatically if configured)
3. Sets the `ANTHROPIC_API_KEY` environment variable to enable API billing
4. Allows you to continue your session seamlessly
5. Optionally switches back to subscription mode when limits reset

## Features

- 🔄 **Automatic Detection**: Monitors for usage limit errors in real-time
- ⚡ **Seamless Switching**: Continues your session without losing context
- 🔔 **Smart Notifications**: Alerts you before switching or when approaching limits
- ⏰ **Auto-Reset**: Switches back to subscription mode when your limits reset
- 🛡️ **Safe Mode**: Optional prompt before spending API credits

## Project Overview

This project is currently in early development. The planned architecture includes:

### Source Files (src/claude_fallback/)

- **`__init__.py`** - Package initialization and version info
- **`cli.py`** - Command-line interface using Typer for user interactions
- **`monitor.py`** - Background process monitor to detect Claude Code usage limit errors
- **`config.py`** - Configuration management using Pydantic for settings validation
- **`session.py`** _(planned)_ - Session state management and mode switching logic

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

### As a Wrapper

```bash
# Run Claude Code through the fallback wrapper
python claude-fallback.py
```

### As a Background Monitor

```bash
# Monitor an existing Claude Code session
python monitor.py --pid <claude-code-pid>
```

### Manual Control

```bash
# Force switch to API mode
python claude-fallback.py --force-api

# Check current mode and usage
python claude-fallback.py --status

# Reset to subscription mode
python claude-fallback.py --use-subscription
```

## Subscription Plans Reference

- **Pro ($20/month)**: ~45 messages or 10-40 prompts every 5 hours
- **Max 5x ($100/month)**: ~225 messages or 50-200 prompts every 5 hours
- **Max 20x ($200/month)**: ~900 messages or 200-800 prompts every 5 hours

Usage varies based on codebase size, conversation length, and model choice (Opus uses ~5x more than Sonnet).

## Cost Comparison

**Example: Heavy coding session**

- Subscription: $20/month Pro = ~40-80 hours of Sonnet 4
- API: ~$0.003/prompt input + ~$0.015/prompt output (varies by context)

For most users, subscription + occasional API usage is more cost-effective than pure API usage.

## Requirements

- Python 3.8+ (Python 3.12 recommended with mise)
- Active Claude Pro or Max subscription
- Anthropic API key (for fallback)
- Claude Code installed
- **macOS or Linux** (uses PTY for process interaction - Windows support planned)
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
