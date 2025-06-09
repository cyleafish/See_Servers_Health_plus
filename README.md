# See_Servers_Health_plus

[TOC]
## See_Servers_Health_plus 介紹

:information_source: 是 [See_Server_Health](https://github.com/cyleafish/See-Server-Health) 的進階版

## See_Server_Health 的專案動機
日常網站或伺服器管理中，管理人員不見得能隨時攜帶電腦，而一旦系統出現異常可能就已經錯過第一時間處理的最佳時機！為了解決這個問題，我們建立了一套整合 Telegram Bot 的監控與操作系統，能讓使用者能得到系統資源使用狀況（如 CPU、記憶體等），並提供控制指令，也提供遠端控制網頁兩種方案做選擇，協助管理人員隨時掌握服務狀態並立即做出反應。
另外，也有即時警告，當有新的登入行為，將即時傳送給管理者，若想要做更多操作，我們也有網頁版 Terminal 可登入做指令。

:warning:但一次只能監控一台
所以，我們的 See_Servers_Health_plus 則是基於上述專案，更改成 Agent-Server-Client 架構，可一次監控、控制多台 Server 在統一的 TG Bot 中！


## 專案功能
- 查看所有的監控對象（後面以 Agent 稱呼）
- Alert：用 prometheus 專案中的 alertmanager
    -  agent_alerts 警告
        -  AgentDown：失去連線 1 分鐘以上
        -  AgentHighCPU：CPU 使用率高於 80% 持續 2 分鐘
        -  AgentHighMemory：記憶體使用率高於 85% 持續 2 分鐘
        -  AgentHighDisk：磁碟使用率高於 90% 持續 1 分鐘
    -  system_alerts 警告
        -  HighLoad：系統 1 分鐘平均負載過高
        -  HighMemoryUsage：可用記憶體過低（使用率高於 85%）
-  查看 Server 和每個 Agent 的 CPU、Memory、Disk 使用率，與圖表

## 架構圖
![image](https://hackmd.io/_uploads/ByMPagymex.png)

## 專案結構
#### Server
```bash
See-Servers-Health_plus/
├── monitor/                  #  圖表繪製與查詢邏輯(使用 python)
│   ├── cpu.py
│   └── (disk.py ...)
├── promethues/             # Prometheus 的設定檔
│   ├── docker-compose.yml  # 抓取監控資料
├────├── promethues/ 
│    ├────── prometheus.yml 
│    └────── alert.rules
├── utils/                  # 管理能使用此 Bot 的使用者清單
│    └── whitelist.py  
├── agent_name_ip.txt        # job_name 對應 IP 表
├── app.py                   # Telegram Bot 主程式
├── server.py                # HTTP API 接收層（/alerts、/exec 等）
├── auto_yml.py              # 自動生成 prometheus.yml 腳本
├── requirements.txt         # Server 所需套件
├── .env                     # BOT_TOKEN, ALERT_CHAT_ID, SERVER_URL 等
├── start_build.sh           # 自動腳本，可一次自動開啟各個服務
└── README.md

```
#### Agent

```bash
See-Servers-Health_plus/Agent/
├── agent.py                 # Agent 主程式
├── start_agent.sh           # 自動啟動 Agent 的腳本
├── agent_env.example        # .env 格式範例
├── agent_requirements.txt   # Agent 所需套件
├── node_exporter-*/         # Node Exporter 執行檔與設定
└── agent_modules/           # Agent 功能模組
│    ├── shell_ops.py
└──  └── (login_watcher.py ...)
```
## 使用方法
### 環境
#### Telegram Bot 教學
:information_source: 如何獲得上述 `<your_bot_token>` 與 `your_telegram_id`，這邊教你如何新增自己的 Telegram Bot 
- 打開 Telegram，搜尋 @BotFather
![image](https://hackmd.io/_uploads/Syc9dXXCyx.png)
- 傳送指令 /start、然後 /newbot
- 根據提示輸入：
    - Bot 名稱（例如：MyMonitorBot）
    - 使用者名稱（結尾需是 bot，如：my_monitor_bot）
- 你會拿到一個 Bot Token：
![image](https://hackmd.io/_uploads/rkJ124KC1x.png)
- 找到你的 bot 輸入 /start
![image](https://hackmd.io/_uploads/H1Vg_7XR1e.png)
- 在瀏覽器輸入
`https://api.telegram.org/bot<YourBotToken>/getUpdates` 並找出 id
![image](https://hackmd.io/_uploads/rkFLn4tRJe.png)

#### Agent 環境設定指南 
- Agent 會用到的 port(使用時需避免撞到)：
    - 8001: agent.py
    - 9100: node exproter
- 操作部分
    - 下載專案中的 Agent/ 資料夾
    - 將檔案中的 `agent_env.example`複製並取名叫 `.env`
        - 修改裡面的資料
         ```
            # Agent 配置範例
            AGENT_ID=agent1     # 改成你要的名字（注意名字不要重複）
            AGENT_HOST=0.0.0.0  # AGENT 的 ip
            AGENT_PORT=8001     # 確保 8001 port 沒有被撞到
            SERVER_URL=http://your-central-server:8002
         ```
#### 快速執行
設定好 .env 後執行 `start_agent.sh` 
他會自動執行：
- 下載相關套件
    - `pip install -r agent_requirements.txt`
- 開啟 node_exporter
    - `cd node_exporter-1.9.1.linux-amd64`
    - `./node_exporter &`
- 最後執行 `agent.py`
    - `./agent.py`

#### Server 設定指南 
- Server 會使用到的 port(使用時需避免撞到)：
    - 3000: grafana -> 不會用到
    - 8002: server.py
    - 9090: prometheus
    - 9093: alertmanager
    - 9100: node exproter
- 下載此專案中 `git clone https://github.com/cyleafish/See_Servers_Health_plus.git`
- 將檔案中的 `.env.example`複製並取名叫 `.env`
    ```
    # Telegram Bot Configuration
    BOT_TOKEN = your_telegram_bot_token_here
    chat_id = your_chat_id_here
    ALERT_CHAT_ID = your_alert_chat_id_here
    
    # Whitelist Configuration (user IDs)
    ALLOWED_USERS=123456789,987654321

    # Server Configuration
    SERVER_HOST=0.0.0.0
    SERVER_PORT=8002
    SERVER_URL=http://localhost:8002

    PROMETHEUS_URL=http://localhost:9090
    ```
- 增加 Agent：修改 agent_name_ip.txt
    - 格式為：名稱<空格>ip:port
    - 範例：
        ```
        Server 192.168.0.0:9100
        Agent1 146.190.0.0:9100
        Agent2 10.107.0.0:9100
        ```
#### 快速執行
設定好 .env 跟 agent_name_ip.txt 執行 `./start_build.sh` 
他會自動執行：
- 執行 auto_yml.py：他會自動生成 prometheus 需要的 .yml 檔案
    - `python3 auto_yml.py`
- 執行 server.py：用於指令操作
    - `python3 server.py`
- 啟動 docker：用於 prometheus -> 監控部分 
    - `cd prometheus`
    - `docker compose up --build`
- 啟動 Telegram Bot..."
python3 app.py
:information_source:
若有改動 agent_name_ip.txt，要執行以下步驟做更新：
- `python3 auto_yml.py`：重新生成新的 .yml
- `cd prometheus`
- `docker compose restart`：重新執行 docker

## DEMO
- 在 Telegram 輸入 `/start` 後就可以開始使用
    - ![image](https://hackmd.io/_uploads/r1dZNDN7gg.png )
- `/agents` 查看所有正在監控中的 agents(包含狀態)
    - ![image](https://hackmd.io/_uploads/ByZrBwNQll.png)
#### 操作指令
- `/broadcast <cmd>` 廣播指令到所有 agents
    - ![image](https://hackmd.io/_uploads/rkFNDvEQlx.png)
- `/op_exec <agent> <cmd>` 在指定 agent 執行 shell 指令
    - ![image](https://hackmd.io/_uploads/SyG_9DVXgg.png)
- `/op_port <agent>` 查看指定 agent 所有開啟的 port
    - ![image](https://hackmd.io/_uploads/B1qWovVQlg.png)
- `/op_stop <agent> <port>` 關閉指定 agent 的 port
    - ![image](https://hackmd.io/_uploads/HyIGswVQxg.png)


#### 資源監控
- `/mon_cpu` 顯示 server 當下的 CPU 使用率
    - `/mon_cpu <agent_ip>或<agent_name>` 顯示指定 agent 當下的 CPU 使用率
    - ![image](https://hackmd.io/_uploads/HkxZKDEmex.png)
- `/mon_cpu_picture` 顯示 server 5 分鐘前到現在的 CPU 使用率折線圖
- ![image](https://hackmd.io/_uploads/ByKNFDEmlx.png)
    - `/mon_cpu_picture <參數>` 顯示 server ? 分鐘前到現在的 CPU 使用率折線圖
    - `/mon_cpu_picture <時間> <參數>` 顯示 server <時間> 前後 ? 分鐘內的 CPU 使用率的折線圖
- `/mon_cpu_picture <agent_ip>或<agent_name>` 顯示 指定 agent 5 分鐘前到現在的 CPU 使用率折線圖
    - ![image](https://hackmd.io/_uploads/BJuUYP4mex.png)
    - `/mon_cpu_picture <agent_ip>或<agent_name> <參數>` 顯示指定 agent ? 分鐘前到現在 CPU 使用率折線圖
    - ![image](https://hackmd.io/_uploads/HJSOtPVQlg.png)
    - `/mon_cpu_picture <agent_ip>或<agent_name> <時間> <參數>` 顯示 指定 agent <時間> 前後 ? 分鐘內的 CPU 使用率的折線圖
:information_source:
格式補充說明
<參數>：分鐘
<時間>：hhmm 24小時制

#### 警告範例
- 登入警告
    - ![image](https://hackmd.io/_uploads/HyD9oP4Qxl.png)
- Agent 失去連線
    - ![image](https://hackmd.io/_uploads/rkDNnvEQex.png)
- Agent HighLoad 警告
    - ![螢幕擷取畫面 2025-06-09 221517](https://hackmd.io/_uploads/BJvyaPN7gg.png)
## 未來展望
- 使用者可以透過 Telegram 新增 Agent（監控對象）
- AI 分析結果：若偵測到異常流量，將會交給 AI 做判斷並給予操作建議
- 資安問題：限制只能打哪些指令，或給予特定的低權限使用者帳號，或需要輸入密碼等
- 更多種類的圖表：用 Python 畫直方圖、圓餅圖等，或嘗試抓 Grafana 的圖片
- 更詳細的資訊：例如 CPU 使用率過高，可以顯示占用 CPU 最高的幾個 Process

## 資料來源
- [See_Server_Health](https://github.com/cyleafish/See-Server-Health)
## 分工表
| 姓名 | 工作 |
| -------- | -------- |
| 葉芷妤     | 期末報告：Telegram bot、Docker 架設、報告、ReadME<br>期末報告補充：Server 操作指令改成 Agent-Server-Client 架構、README、報告 |
| 賴詩璿     | 期末報告：網頁 Terminal(ngrok、ttyd)、報告、ReadME|
| 陳子晴     | 期末報告：Telegram bot、Prometheous 監控、報告、ReadME<br>期末報告補充：監控 CPU、Memory、Disk 使用率改成 Agent-Server-Client 架構、README、報告 |
