#!/bin/bash

# Agent 啟動腳本
# 用法: ./start_agent.sh [agent_id] [server_url]

# 設定預設值
AGENT_ID=${1:-"agent1"}
SERVER_URL=${2:-"http://localhost:8002"}
AGENT_PORT=${3:-"8001"}

echo "🤖 啟動 Agent: $AGENT_ID"
echo "📡 Central Server: $SERVER_URL"
echo "🔌 Agent Port: $AGENT_PORT"

# 檢查是否已有 .env 檔案
if [ ! -f ".env" ]; then
    echo "📝 創建 .env 配置檔案..."
    cat > .env << EOF
AGENT_ID=$AGENT_ID
AGENT_HOST=0.0.0.0
AGENT_PORT=$AGENT_PORT
SERVER_URL=$SERVER_URL
EOF
fi

# 安裝依賴
echo "📦 安裝依賴..."
pip install -r agent_requirements.txt

# 啟動 Agent
echo "🚀 啟動 Agent $AGENT_ID..."
export AGENT_ID=$AGENT_ID
export AGENT_PORT=$AGENT_PORT
export SERVER_URL=$SERVER_URL
python3 agent.py