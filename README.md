# Claude Code Fallback

[![PyPI version](https://badge.fury.io/py/claude-code-fallback.svg)](https://pypi.org/project/claude-code-fallback/)
[![Downloads](https://pepy.tech/badge/claude-code-fallback)](https://pepy.tech/project/claude-code-fallback)

Automatically switch from your Claude subscription to API billing when you hit usage limits, keeping your coding session uninterrupted.

> **Note (December 2025):** Claude Code now has built-in extra-usage support. This tool remains useful if you want:
>
> - **Background monitoring** with OS notifications before you're blocked
> - **Auto-restart mode** that switches automatically without any prompts
> - **Multi-terminal awareness** (monitor runs independently, works in tmux/ssh)
>
> If the built-in extra-usage feature meets your needs, you may not need this tool.

## Why This Exists

Claude Code usage is shared with your web Claude.ai usage and resets every 5 hours. When you hit these limits during an active coding session, you're forced to either wait or manually switch to API billing. This tool automates that transition so you never lose momentum.

## How It Works

A lightweight background monitor watches Claude Code's JSONL logs for usage limit errors:

1. You run Claude Code normally (no wrapper needed)
2. Background monitor detects when you've hit subscription limits
3. You receive a notification: "Usage limit reached! Run 'claude-api' to switch"
4. Exit Claude Code and run `claude-api` to restart with API billing
5. Continue working seamlessly in the same directory
6. Run `claude-sub` to switch back to subscription mode

## Features

- **Log-Based Detection**: Monitors JSONL logs for usage limit errors
- **Simple Shell Functions**: Switch modes with `claude-api` and `claude-sub` commands
- **Native Notifications**: OS-level alerts when limits are detected
- **Directory Preservation**: Automatically restarts Claude in your working directory
- **No Process Wrapping**: Claude Code runs normally, no PTY manipulation
- **Robust Daemon Mode**: Background monitor with proper signal handling

## Quick Start

### 1. Install

```bash
pip install claude-code-fallback
```

Or with uv:

```bash
uv pip install claude-code-fallback
```

### 2. Set Your API Key

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'
```

Get your API key from [console.anthropic.com](https://console.anthropic.com)

### 3. Install Shell Functions

```bash
claude-fallback install
source ~/.zshrc  # or ~/.bashrc
```

### 4. Start the Monitor

```bash
# Run in background (recommended)
claude-fallback start --daemon

# Or run in foreground
claude-fallback start
```

### 5. Use Claude Normally

```bash
claude
```

When you hit limits, you'll get a notification. Exit Claude and run:

```bash
claude-api    # Switch to API mode
claude-sub    # Switch back to subscription
```

## Commands

### CLI Commands

| Command                          | Description                |
| -------------------------------- | -------------------------- |
| `claude-fallback install`        | Install shell functions    |
| `claude-fallback start`          | Start monitor (foreground) |
| `claude-fallback start --daemon` | Start monitor (background) |
| `claude-fallback stop`           | Stop background monitor    |
| `claude-fallback status`         | Show current status        |
| `claude-fallback clear`          | Clear limit detected state |
| `claude-fallback help`           | Show help                  |

### Shell Functions

| Function      | Description                             |
| ------------- | --------------------------------------- |
| `claude-api`  | Switch to API billing and start Claude  |
| `claude-sub`  | Switch to subscription and start Claude |
| `claude-mode` | Show current mode                       |

## Configuration

The tool uses environment variables (recommended) or a config file:

### Environment Variables

```bash
# Required: Your Anthropic API key
export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'

# Optional: Enable auto-restart (kills Claude and restarts in API mode)
export CLAUDE_FALLBACK_AUTO_RESTART=1
```

### Config File (Alternative)

Create `config.json` in the project directory:

```json
{
  "api_key": "sk-ant-api03-...",
  "auto_restart": true
}
```

### Options

| Option         | Description                                                                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `api_key`      | Your Anthropic API key (required)                                                                                                                                        |
| `auto_restart` | When true, automatically kills Claude and restarts in API mode when limits hit. Your current conversation will end, but a new session starts immediately. Default: false |

## Architecture

```
Claude Code (runs normally)
         |
~/.claude/projects/*/sessions/*.jsonl
         |
LogMonitor (background daemon)
    |-- Detects rate limit patterns
    |-- Sends OS notification
    |-- Sets flag file for shell
         |
Shell Functions
    |-- claude-api: switch to API mode
    |-- claude-sub: switch to subscription
```

## Files

| File                            | Purpose                       |
| ------------------------------- | ----------------------------- |
| `~/.claude_fallback.pid`        | Monitor PID (daemon mode)     |
| `~/.claude_fallback_state.json` | Current mode and status       |
| `~/.claude_fallback_active`     | Flag file when limit detected |
| `~/.claude_fallback_error.log`  | Error log                     |

## Requirements

- Python 3.8+
- Active Claude Pro or Max subscription
- Anthropic API key (for fallback)
- Claude Code installed
- macOS or Linux (Windows via WSL)

## Real-World Usage

My typical workflow:

1. Start a coding session with `claude`
2. Background monitor watches the session logs
3. Work normally until I hit subscription limits
4. Get a native OS notification
5. Exit Claude Code and run `claude-api` to switch
6. Continue working in the same directory
7. When done with heavy work, run `claude-sub` to switch back

Subscription + API fallback typically costs $5-10/month in API usage, far less than going API-only. Usage varies based on codebase size and model choice (Opus uses ~5x more than Sonnet).

## Security Notes

- Store your API key in environment variables
- The tool only reads/writes the `ANTHROPIC_API_KEY` environment variable
- All logs are stored locally
- Your API key is never transmitted except to Anthropic's API

## Contributing

Contributions welcome! This project addresses a real need expressed in [Anthropic's GitHub Issue #2944](https://github.com/anthropics/claude-code/issues/2944).

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Disclaimer

This is an unofficial tool not affiliated with Anthropic. Use at your own risk. Always monitor your API usage and costs. The tool respects Anthropic's terms of service by only switching between legitimate authentication methods.

## License

Apache 2.0 License - see LICENSE file for details

## Acknowledgments

- Inspired by [Issue #2944](https://github.com/anthropics/claude-code/issues/2944)
- Built for developers who need uninterrupted coding sessions
- Thanks to the Anthropic team for building Claude Code
