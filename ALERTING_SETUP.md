# 🚨 Alertmanager + Telegram Bot 整合設定指南

## 📋 設定步驟

### 1. 環境變數設定
複製並修改環境變數：
```bash
cp .env.example .env
```

**重要設定：**
- `BOT_TOKEN`: 你的 Telegram Bot Token
- `ALERT_CHAT_ID`: 接收告警的 Chat ID（可以是個人或群組）

### 2. 獲取 Chat ID
發送訊息給你的 Bot，然後訪問：
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
從 `chat.id` 欄位獲取 Chat ID

### 3. 啟動服務

**啟動 Prometheus Stack：**
```bash
cd prometheus
docker-compose up -d
```

**啟動 Server：**
```bash
python server.py
```

**啟動 Agent：**
```bash
cd Agent
python agent.py
```

**啟動 Telegram Bot：**
```bash
python app.py
```

## 🔧 測試告警功能

### 手動測試告警接收
```bash
curl -X POST http://localhost:8002/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "TestAlert",
          "instance": "test:8001",
          "severity": "warning"
        },
        "annotations": {
          "summary": "This is a test alert",
          "description": "Testing Telegram integration"
        }
      }
    ]
  }'
```

### 觸發真實告警
1. **停止 Agent 服務** - 觸發 `AgentDown` 告警
2. **模擬高 CPU** - 在 Agent 機器執行：
   ```bash
   # 模擬高 CPU 使用
   yes > /dev/null &
   # 停止：killall yes
   ```

## 📊 可用的告警規則

- **AgentDown**: Agent 服務下線
- **AgentHighCPU**: CPU 使用率 > 80%
- **AgentHighMemory**: 記憶體使用率 > 85%  
- **AgentHighDisk**: 磁碟使用率 > 90%
- **ServiceDown**: 任何監控服務下線
- **HighLoad**: 系統負載過高

## 🎯 Telegram Bot 新功能

### 圖表指令
- `/chart agent1 cpu` - Grafana 圖表
- `/prom_chart agent1 agent_cpu_usage_percent` - Prometheus 數據圖表

### 監控指令
- `/agents` - 查看所有 agents
- `/mon_cpu agent1` - CPU 監控
- `/mon_mem agent1` - 記憶體監控
- `/mon_disk agent1` - 磁碟監控

## 🔍 故障排除

### 1. 告警沒有發送到 Telegram
- 檢查 `ALERT_CHAT_ID` 是否正確設定
- 確認 Bot 有權限發送訊息到該 Chat
- 查看 server.py 的 console 輸出

### 2. Agent metrics 沒有顯示
- 確認 Agent 的 `/metrics` endpoint 正常：`curl http://localhost:8001/metrics`
- 檢查 Prometheus targets 狀態：http://localhost:9090/targets

### 3. Grafana 圖表無法生成
- 確認 Grafana 服務運行正常：http://localhost:3000
- 設定 `GRAFANA_API_KEY`（在 Grafana 中建立 API Key）
- 確認 Dashboard UID 正確

## 📈 監控界面

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Alertmanager**: http://localhost:9093

## 🔐 安全建議

1. 使用專門的告警群組，限制成員
2. 設定適當的 `ALLOWED_USERS` 白名單
3. 定期檢查告警規則的準確性
4. 避免在 `.env` 檔案中暴露敏感資訊