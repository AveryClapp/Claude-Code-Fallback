# Quick Start Guide

## Setup

1. **Create your config file:**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit config.json and add your API key:**
   ```bash
   # Get your API key from: https://console.anthropic.com/settings/keys
   vim config.json  # or use your preferred editor
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

## Running the Tool

Start Claude Code with automatic fallback:

```bash
claude-fallback run
```

This will:
- Launch Claude Code in subscription mode
- Monitor for usage limit errors (looks for "resets" in output)
- Prompt you to switch to API mode when limits are hit
- Automatically restart with your API key

## Testing the Switch

To test the switching mechanism without hitting real limits, you can:

1. Run the tool
2. In Claude Code, type something that triggers output containing "resets"
3. The tool should detect it and prompt you to switch

## Stopping

Press `Ctrl+C` to stop the session at any time.

## Configuration Options

Edit `config.json` to customize behavior:

- `prompt_before_switch: true` - Ask before switching (recommended)
- `auto_switch: false` - Automatically switch without prompting
- `cost_limit_per_session: 10.0` - Max API spending per session (future feature)

## Platform Support

✅ **Works on:** macOS, Linux
❌ **Not supported:** Windows (requires PTY support)

## Troubleshooting

**"Config file not found"**
- Make sure you created `config.json` from `config.example.json`

**"Invalid API key format"**
- API key should start with `sk-ant-`
- Get yours from https://console.anthropic.com/settings/keys

**Module not found errors**
- Make sure you activated the venv: `source .venv/bin/activate`
- Reinstall if needed: `uv pip install -e .`
