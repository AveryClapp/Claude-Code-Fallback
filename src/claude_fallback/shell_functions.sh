#!/bin/bash
# Shell functions for Claude Code API fallback
# This file is sourced by your shell configuration (.zshrc, .bashrc, etc.)

# Switch Claude Code to API billing mode
claude-api() {
    local api_key="${CLAUDE_FALLBACK_API_KEY}"

    if [ -z "$api_key" ]; then
        echo "Error: CLAUDE_FALLBACK_API_KEY not set"
        echo "Add this to your ~/.zshrc or ~/.bashrc:"
        echo "  export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'"
        return 1
    fi

    export ANTHROPIC_API_KEY="$api_key"
    echo "Switching to API billing mode..."
    exec claude
}

# Switch Claude Code back to subscription mode
claude-sub() {
    unset ANTHROPIC_API_KEY
    echo "Switching to subscription mode..."
    exec claude
}

# Start the background monitor
claude-monitor-start() {
    if pgrep -f "python.*claude_fallback.*monitor" > /dev/null; then
        echo "Monitor is already running"
        return 0
    fi

    echo "Starting Claude Code monitor..."
    nohup python -m claude_fallback.monitor > /dev/null 2>&1 &
    echo "Monitor started (PID: $!)"
}

# Stop the background monitor
claude-monitor-stop() {
    pkill -f "python.*claude_fallback.*monitor"
    echo "Monitor stopped"
}

# Check monitor status
claude-monitor-status() {
    if pgrep -f "python.*claude_fallback.*monitor" > /dev/null; then
        echo "Monitor is running"
        pgrep -af "python.*claude_fallback.*monitor"
    else
        echo "Monitor is not running"
    fi
}
