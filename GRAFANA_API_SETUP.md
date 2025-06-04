# 🔑 Grafana API Key 設定指南

## 問題說明
當你看到以下錯誤時：
```
grafana-1 | logger=authn.service msg="Failed to authenticate request" client=auth.client.api-key error="[api-key.invalid] API key is invalid"
```

這表示 Grafana API Key 設定有問題。

## 🛠️ 解決方案

### 方案 1: 創建 Grafana API Key

1. **登入 Grafana**
   - 訪問：http://localhost:3000
   - 預設帳號：`admin` / `admin`

2. **創建 API Key**
   - 點擊左側選單 → Administration → Service accounts
   - 點擊 "Add service account"
   - 名稱：`telegram-bot`
   - 角色：`Viewer` (或 `Editor`)
   - 點擊 "Create"

3. **生成 Token**
   - 在創建的 Service Account 中點擊 "Add service account token"
   - 名稱：`render-api`
   - 點擊 "Generate token"
   - **複製並保存 token**

4. **設定環境變數**
   ```bash
   # 在 .env 檔案中添加
   GRAFANA_API_KEY=你的_api_key_這裡
   ```

### 方案 2: 使用基本認證 (已自動實現)

程式已經自動回退到基本認證：
- 帳號：`admin`
- 密碼：`admin` (或你設定的密碼)

### 方案 3: 使用 Prometheus 圖表 (推薦)

如果 Grafana 有問題，可以直接使用 Prometheus 數據：

```bash
# 使用 Prometheus 圖表指令
/prom_chart agent1 agent_cpu_usage_percent
/prom_chart agent1 agent_memory_usage_percent
/prom_chart agent1 agent_disk_usage_percent
```

## 🔍 測試 API 連接

```bash
# 測試基本認證
curl -u admin:admin http://localhost:3000/api/health

# 測試 API Key (如果有設定)
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:3000/api/health
```

## 💡 建議

1. **優先使用 Prometheus 圖表** - 更穩定且不需要額外認證
2. **如需 Grafana 圖表** - 設定正確的 API Key
3. **錯誤處理** - 程式已自動提供替代方案

## 🚀 快速測試

重新啟動 Telegram Bot 並嘗試：
```bash
/prom_chart agent1 agent_cpu_usage_percent
```

這個指令不依賴 Grafana，直接從 Prometheus 獲取數據並生成圖表。