#!/bin/bash
# Shell functions for Claude Code API fallback
# This file is sourced by your shell configuration (.zshrc, .bashrc, etc.)

# State and flag files
_CLAUDE_FALLBACK_STATE="$HOME/.claude_fallback_state.json"
_CLAUDE_FALLBACK_FLAG="$HOME/.claude_fallback_active"

# Switch Claude Code to API billing mode
claude-api() {
    local api_key="${CLAUDE_FALLBACK_API_KEY}"

    if [ -z "$api_key" ]; then
        echo "Error: CLAUDE_FALLBACK_API_KEY not set"
        echo ""
        echo "Add to your shell config (~/.zshrc or ~/.bashrc):"
        echo "  export CLAUDE_FALLBACK_API_KEY='sk-ant-api03-...'"
        return 1
    fi

    # Update state file
    if command -v python3 &> /dev/null; then
        python3 -c "
import json
from pathlib import Path
from datetime import datetime
state_file = Path.home() / '.claude_fallback_state.json'
state = {'mode': 'api', 'limit_detected': False, 'last_switch_at': datetime.now().isoformat()}
if state_file.exists():
    try:
        state.update(json.loads(state_file.read_text()))
    except: pass
state['mode'] = 'api'
state['limit_detected'] = False
state['last_switch_at'] = datetime.now().isoformat()
state_file.write_text(json.dumps(state, indent=2))
" 2>/dev/null
    fi

    # Clear the flag file
    rm -f "$_CLAUDE_FALLBACK_FLAG"

    export ANTHROPIC_API_KEY="$api_key"
    echo "Switched to API billing mode"
    echo "Starting Claude Code..."
    exec claude
}

# Switch Claude Code back to subscription mode
claude-sub() {
    # Update state file
    if command -v python3 &> /dev/null; then
        python3 -c "
import json
from pathlib import Path
from datetime import datetime
state_file = Path.home() / '.claude_fallback_state.json'
state = {'mode': 'subscription', 'limit_detected': False, 'last_switch_at': datetime.now().isoformat()}
if state_file.exists():
    try:
        state.update(json.loads(state_file.read_text()))
    except: pass
state['mode'] = 'subscription'
state['limit_detected'] = False
state['last_switch_at'] = datetime.now().isoformat()
state_file.write_text(json.dumps(state, indent=2))
" 2>/dev/null
    fi

    # Clear the flag file
    rm -f "$_CLAUDE_FALLBACK_FLAG"

    unset ANTHROPIC_API_KEY
    echo "Switched to subscription mode"
    echo "Starting Claude Code..."
    exec claude
}

# Check if limit was detected (for scripts/automation)
claude-limit-detected() {
    if [ -f "$_CLAUDE_FALLBACK_FLAG" ]; then
        return 0  # true - limit detected
    else
        return 1  # false - no limit
    fi
}

# Show current mode
claude-mode() {
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        echo "Current mode: API"
    else
        echo "Current mode: Subscription"
    fi

    if [ -f "$_CLAUDE_FALLBACK_FLAG" ]; then
        echo "Status: Usage limit detected - run 'claude-api' to switch"
    fi
}
