#!/bin/bash
# 戏讯一键解析同步脚本
# Usage: ./one_click_sync.sh [URL]

# Get the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate venv if it exists (adjust path if needed)
if [ -d "$DIR/venv" ]; then
    source "$DIR/venv/bin/activate"
fi

# Run the python CLI
python3 "$DIR/backend/cli.py" "$@"
