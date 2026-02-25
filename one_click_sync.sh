#!/bin/bash
# 戏讯一键解析同步脚本
# Usage: ./one_click_sync.sh [URL]

set -e

# Get the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$DIR/venv"
VENV_PY="$VENV_DIR/bin/python3"
REQ_FILE="$DIR/backend/requirements.txt"

recreate_venv() {
    echo "检测到虚拟环境不可用，正在重建 venv..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
}

# 1) 检查 venv 是否存在且可用（目录改名后常见失效）
if [ ! -x "$VENV_PY" ]; then
    recreate_venv
elif ! "$VENV_PY" -c "import sys" >/dev/null 2>&1; then
    recreate_venv
fi

# 2) 确保 pip 可用
if ! "$VENV_PY" -m pip --version >/dev/null 2>&1; then
    echo "初始化 pip..."
    "$VENV_PY" -m ensurepip --upgrade
fi

# 3) 自动补依赖（首次运行或缺包时）
if ! "$VENV_PY" -c "import requests" >/dev/null 2>&1; then
    echo "安装 Python 依赖..."
    "$VENV_PY" -m pip install -r "$REQ_FILE"
fi

# 4) Run the python CLI
"$VENV_PY" "$DIR/backend/cli.py" "$@"
