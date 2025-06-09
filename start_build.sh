#!/bin/bash
echo "🔧 生成 prometheus 需要的 .yml 檔案"
python3 auto_yml.py

echo "🛠️ 啟動 Operation 操作..."
python3 server.py &

echo "⚠️ 啟動 monitor (prometheus docker)..."
cd prometheus
docker compose up -d 

echo "🤖 啟動 Telegram Bot..."
cd ..
python3 app.py





