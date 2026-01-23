#!/bin/bash

# 戏讯解析助手启动脚本

echo "================================"
echo "  戏讯解析助手"
echo "================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.installed" ]; then
    echo "安装依赖..."
    pip install -r backend/requirements.txt
    touch venv/.installed
fi

# 检查端口占用并清理
PORT=5001
PID=$(lsof -ti:$PORT)
if [ ! -z "$PID" ]; then
    echo "发现端口 $PORT 被占用 (PID: $PID)，正在清理..."
    kill -9 $PID
    sleep 1
    echo "端口已释放"
fi

# 启动服务
echo ""
echo "启动后端服务..."
echo "访问地址: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================"
echo ""

cd backend && python app.py
