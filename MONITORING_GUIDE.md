# 📊 Prometheus + Node Exporter 監控系統指南

## 🎯 **架構說明**

你的監控系統已經成功改為使用 **Prometheus + Node Exporter** 架構：

```
Telegram Bot → Server → Prometheus API → Node Exporter (各 Agent)
```

## 🚀 **啟動順序**

### 1. 啟動 Prometheus Stack
```bash
cd prometheus
docker compose up -d
```

### 2. 在各 Agent 主機安裝並啟動 Node Exporter
```bash
# 下載 node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.6.1.linux-amd64.tar.gz
cd node_exporter-1.6.1.linux-amd64

# 啟動 node_exporter (預設 port 9100)
./node_exporter &
```

### 3. 啟動中央 Server
```bash
python server.py
```

### 4. 啟動 Telegram Bot
```bash
python app.py
```

## 📋 **支援的監控指令**

### **即時監控數據**
```bash
/mon_cpu                        # 預設 localhost:9100 的 CPU
/mon_cpu 192.168.80.47:9100     # 指定 instance 的 CPU
/mon_mem                        # 預設 localhost:9100 的 Memory  
/mon_mem 192.168.80.47:9100     # 指定 instance 的 Memory
/mon_disk                       # 預設 localhost:9100 的 Disk
/mon_disk 192.168.80.47:9100    # 指定 instance 的 Disk
```

### **圖表監控 (matplotlib)**
```bash
/mon_cpu_picture                         # 預設 instance, 最近 5 分鐘
/mon_cpu_picture 192.168.80.47:9100      # 指定 instance, 最近 5 分鐘
/mon_cpu_picture 30                      # 預設 instance, 最近 30 分鐘
/mon_cpu_picture 192.168.80.47:9100 30   # 指定 instance, 最近 30 分鐘

# 同樣適用於 memory 和 disk
/mon_mem_picture 192.168.80.47:9100 60
/mon_disk_picture 192.168.80.47:9100 15
```

### **Prometheus 圖表**
```bash
/prom_chart agent1 node_cpu_seconds_total
/chart agent1 cpu                         # Grafana 圖表 (如果可用)
```

### **查看監控目標**
```bash
/agents    # 顯示所有 Prometheus 監控的 targets
```

## ⚙️ **配置檔案**

### Prometheus 配置 (`prometheus/prometheus.yml`)
```yaml
scrape_configs:
  - job_name: 'Server'
    scrape_interval: 15s
    static_configs:
      - targets: ['192.168.80.49:9100']  
  
  - job_name: 'Agent1'
    scrape_interval: 15s
    static_configs:
      - targets: ['192.168.80.47:9100']

  - job_name: 'Agent2'
    scrape_interval: 15s
    static_configs:
      - targets: ['146.190.147.94:9100']
```

### 環境變數 (`.env`)
```bash
PROMETHEUS_URL=http://localhost:9090
BOT_TOKEN=your_bot_token
SERVER_URL=http://localhost:8002
```

## 🔧 **新功能特點**

### ✅ **統一的 Instance 支援**
- 所有監控指令都支援指定 instance (IP:Port)
- 自動檢測參數是否為 instance 格式
- 預設使用 `localhost:9100`

### ✅ **改善的錯誤處理**
- 清楚的錯誤訊息
- 自動檢測 node_exporter 是否運行
- 支援 Prometheus 連接失敗的情況

### ✅ **更好的圖表**
- 使用中文字體
- 包含 instance 資訊的標題
- 統一的樣式和配色

### ✅ **環境變數支援**
- 所有模組都使用 `.env` 中的 `PROMETHEUS_URL`
- 便於不同環境部署

## 🔍 **故障排除**

### 1. **Node Exporter 未運行**
錯誤：`❌ 找不到 192.168.80.47:9100 的 CPU 資料`

解決：
```bash
# 檢查 node_exporter 是否運行
curl http://192.168.80.47:9100/metrics

# 如果沒有回應，啟動 node_exporter
./node_exporter &
```

### 2. **Prometheus 連接失敗**
錯誤：`Prometheus 查詢錯誤`

解決：
```bash
# 檢查 Prometheus 是否運行
curl http://localhost:9090/api/v1/targets

# 重新啟動 Prometheus
cd prometheus && docker compose restart
```

### 3. **圖表生成失敗**
錯誤：`圖表生成失敗`

解決：
- 檢查 matplotlib 是否正確安裝
- 確認有權限在當前目錄寫入檔案
- 檢查中文字體是否安裝

## 📈 **監控界面**

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (可選)
- **Alertmanager**: http://localhost:9093

## 🎯 **使用範例**

```bash
# 查看所有監控目標
/agents

# 監控特定 Agent 的 CPU
/mon_cpu 192.168.80.47:9100

# 生成 30 分鐘的 Memory 使用圖表
/mon_mem_picture 192.168.80.47:9100 30

# 監控本地伺服器的 Disk
/mon_disk

# 生成即時數據圖表
/prom_chart agent1 node_memory_MemAvailable_bytes
```

## 💡 **最佳實踐**

1. **定期檢查 Node Exporter 狀態**：使用 `/agents` 指令
2. **設定適當的監控間隔**：預設 15 秒已足夠
3. **使用圖表分析趨勢**：比文字更直觀
4. **設定告警規則**：在資源使用率過高時自動通知