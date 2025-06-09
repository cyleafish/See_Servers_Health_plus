#!/bin/bash

# Agent 啟動腳本
# 用法: ./start_agent.sh [agent_id] [server_url]

# 安裝依賴
echo "📦 安裝依賴..."
pip install -r agent_requirements.txt

echo "🔧 開啟 node_exporter..."
cd node_exporter-1.9.1.linux-amd64
./node_exporter &

# 啟動 Agent
echo "🚀 啟動 Agent "
cd ..
python3 agent.py