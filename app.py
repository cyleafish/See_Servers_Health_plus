from telegram import Update,ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import requests
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

from monitor.cpu import mon_cpu_picture, mon_cpu
from monitor.mem import mon_mem_picture, mon_mem
from monitor.disk import mon_disk_picture, mon_disk
from utils.whitelist import is_user_allowed
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
app = ApplicationBuilder().token(BOT_TOKEN).build()
PROMETHEUS_URL= os.getenv("PROMETHEUS_URL", "")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8002")

#按鈕
custom_keyboard = [
    ["/agents","/broadcast ps"],
    ["/op_exec Agent1 ps", "/op_port Agent1", "/op_stop Agent1"],
    ["/mon_cpu Agent1","/mon_mem Agent1", "/mon_disk Agent1"],
    ["/mon_cpu_picture", "/mon_cpu_picture Agent1"],
    ["/more", "/more_info_GitHub"]
]

reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)


# /op_exec 指令 - 新格式: /op_exec agent_id command
async def op_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ 使用格式: /op_exec <agent_id> <command>\n例如: /op_exec agent1 ls -l")
        return

    agent_id = context.args[0]
    cmd = "/op_exec " + " ".join(context.args[1:])
    
    try:
        response = requests.post(f"{SERVER_URL}/exec", json={
            "agent_id": agent_id,
            "cmd": cmd,
            "type": "shell"
        })
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 呼叫伺服器失敗：{e}")

# /op_stop 指令 - 新格式: /op_stop agent_id port
async def op_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ 使用格式: /op_stop <agent_id> <port>\n例如: /op_stop agent1 8080")
        return

    agent_id = context.args[0]
    port = context.args[1]
    cmd = f"/op_stop -p {port}"
    
    try:
        response = requests.post(f"{SERVER_URL}/exec", json={
            "agent_id": agent_id,
            "cmd": cmd,
            "type": "shell"
        })
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 呼叫伺服器失敗：{e}")

# /op_port 指令 - 新格式: /op_port agent_id
async def op_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if not context.args:
        await update.message.reply_text("⚠️ 使用格式: /op_port <agent_id>\n例如: /op_port agent1")
        return

    agent_id = context.args[0]
    cmd = "/op_port"
    
    try:
        response = requests.post(f"{SERVER_URL}/exec", json={
            "agent_id": agent_id,
            "cmd": cmd,
            "type": "shell"
        })
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 呼叫伺服器失敗：{e}")

# /agents 指令 - 列出所有可用的 agents
# async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_user_allowed(update.effective_user.id):
#         await update.message.reply_text("🚫 沒有權限")
#         return

#     try:
#         response = requests.get(f"{SERVER_URL}/agents")
#         data = response.json()
#         agents_list = data.get("agents", [])
        
#         if not agents_list:
#             await update.message.reply_text("⚠️ 目前沒有可用的 agents")
#             return
        
#         message = "🤖 可用的 Agents:\n"
#         for agent in agents_list:
#             status_emoji = "🟢" if agent["status"] == "active" else "🔴"
#             message += f"{status_emoji} {agent['agent_id']} ({agent['host']}:{agent['port']}) - {agent['status']}\n"
        
#         await update.message.reply_text(message)
#     except Exception as e:
#         await update.message.reply_text(f"❌ 獲取 agents 失敗：{e}")

async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/targets")
        data = resp.json()

        active_targets = data['data']['activeTargets']

        if not active_targets:
            await update.message.reply_text("❌ 沒有找到任何正在監控的 server。")
            return

        reply_lines = ["🖥️ 目前監控中的 Agent：\n"]
        for target in active_targets:
            instance = target.get("labels", {}).get("instance", "Unknown")
            job = target.get("labels", {}).get("job", "Unknown")
            health = target.get("health", "unknown")
            reply_lines.append(f"🔹 {instance} (Job: {job}) → {'✅ UP' if health == 'up' else '❌ DOWN'}")

        await update.message.reply_text("\n".join(reply_lines))

    except Exception as e:
        await update.message.reply_text(f"⚠️ 讀取伺服器資訊時發生錯誤：{e}")



# /broadcast 指令 - 廣播指令到所有 agents
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if not context.args:
        await update.message.reply_text("⚠️ 使用格式: /broadcast <command>\n例如: /broadcast ps")
        return

    cmd = "/op_exec " + " ".join(context.args)
    
    try:
        response = requests.post(f"{SERVER_URL}/broadcast", json={
            "cmd": cmd,
            "type": "shell"
        })
        data = response.json()
        results = data.get("broadcast_results", {})
        
        if not results:
            await update.message.reply_text("⚠️ 沒有任何結果")
            return
        
        message = f"📡 廣播指令結果 `{' '.join(context.args)}`:\n\n"
        for agent_id, result in results.items():
            status = "✅" if result.get("success") else "❌"
            message += f"{status} **{agent_id}**:\n{result.get('result', 'No result')}\n\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ 廣播失敗：{e}")

# Monitor commands with agent support
# async def mon_cpu_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_user_allowed(update.effective_user.id):
#         await update.message.reply_text("🚫 沒有權限")
#         return

#     # if not context.args:
#     #     await update.message.reply_text("⚠️ 使用格式: /mon_cpu <agent_id>\n例如: /mon_cpu agent1")
#     #     return

#     agent_id = context.args[0]
    
#     try:
#         response = requests.post(f"{SERVER_URL}/exec", json={
#             "agent_id": agent_id,
#             "cmd": "cpu",
#             "type": "monitor"
#         })
#         result = response.json().get("result", "❓ 沒有回應內容")
#         await update.message.reply_text(result)
#     except Exception as e:
#         await update.message.reply_text(f"❌ 監控失敗：{e}")

# async def mon_mem_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_user_allowed(update.effective_user.id):
#         await update.message.reply_text("🚫 沒有權限")
#         return

#     if not context.args:
#         await update.message.reply_text("⚠️ 使用格式: /mon_mem <agent_id>\n例如: /mon_mem agent1")
#         return

#     agent_id = context.args[0]
    
#     try:
#         response = requests.post(f"{SERVER_URL}/exec", json={
#             "agent_id": agent_id,
#             "cmd": "mem",
#             "type": "monitor"
#         })
#         result = response.json().get("result", "❓ 沒有回應內容")
#         await update.message.reply_text(result)
#     except Exception as e:
#         await update.message.reply_text(f"❌ 監控失敗：{e}")

# async def mon_disk_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_user_allowed(update.effective_user.id):
#         await update.message.reply_text("🚫 沒有權限")
#         return

#     if not context.args:
#         await update.message.reply_text("⚠️ 使用格式: /mon_disk <agent_id>\n例如: /mon_disk agent1")
#         return

#     agent_id = context.args[0]
    
#     try:
#         response = requests.post(f"{SERVER_URL}/exec", json={
#             "agent_id": agent_id,
#             "cmd": "disk",
#             "type": "monitor"
#         })
#         result = response.json().get("result", "❓ 沒有回應內容")
#         await update.message.reply_text(result)
#     except Exception as e:
#         await update.message.reply_text(f"❌ 監控失敗：{e}")

# # Grafana 圖表獲取功能
# async def get_grafana_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_user_allowed(update.effective_user.id):
#         await update.message.reply_text("🚫 沒有權限")
#         return
    
#     if len(context.args) < 2:
#         await update.message.reply_text("⚠️ 使用格式: /chart <agent_id> <metric_type>\n例如: /chart agent1 cpu")
#         return
    
#     agent_id = context.args[0]
#     metric_type = context.args[1]
    
#     # Grafana 設定
#     grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
#     dashboard_uid = os.getenv("DASHBOARD_UID", "agent-monitoring")
#     grafana_api_key = os.getenv("GRAFANA_API_KEY", "")
    
#     panel_map = {
#         "cpu": 1,    # Panel ID for CPU metrics
#         "memory": 2, # Panel ID for Memory metrics  
#         "disk": 3    # Panel ID for Disk metrics
#     }
    
#     if metric_type not in panel_map:
#         await update.message.reply_text("❌ 支援的 metric 類型: cpu, memory, disk")
#         return
    
#     try:
#         # 使用 Grafana Render API
#         url = f"{grafana_url}/render/d-solo/{dashboard_uid}"
#         params = {
#             "panelId": panel_map[metric_type],
#             "from": "now-1h",
#             "to": "now",
#             "width": 800,
#             "height": 400,
#             "var-agent": agent_id
#         }
        
#         headers = {}
#         # 如果沒有 API Key，嘗試使用基本認證或匿名訪問
#         if grafana_api_key and grafana_api_key != "your_grafana_api_key_here":
#             headers["Authorization"] = f"Bearer {grafana_api_key}"
#         else:
#             # 嘗試基本認證 (預設 admin/admin)
#             import base64
#             credentials = base64.b64encode(b'admin:admin').decode('ascii')
#             headers["Authorization"] = f"Basic {credentials}"
        
#         response = requests.get(url, params=params, headers=headers, timeout=30)
        
#         if response.status_code == 200:
#             photo = io.BytesIO(response.content)
#             photo.name = f"{agent_id}_{metric_type}_chart.png"
            
#             await update.message.reply_photo(
#                 photo=photo,
#                 caption=f"📊 {agent_id} - {metric_type.upper()} 監控圖表"
#             )
#         elif response.status_code == 401:
#             await update.message.reply_text(f"❌ Grafana 認證失敗，嘗試使用 Prometheus 圖表:\n使用 `/prom_chart {agent_id} agent_{metric_type}_usage_percent`")
#         else:
#             await update.message.reply_text(f"❌ 無法獲取 Grafana 圖表 ({response.status_code})，請嘗試:\n`/prom_chart {agent_id} agent_{metric_type}_usage_percent`")
            
#     except Exception as e:
#         await update.message.reply_text(f"❌ Grafana 圖表失敗: {e}\n\n💡 建議使用 Prometheus 圖表:\n`/prom_chart {agent_id} agent_{metric_type}_usage_percent`")

# Prometheus 數據圖表生成
# async def create_prometheus_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_user_allowed(update.effective_user.id):
#         await update.message.reply_text("🚫 沒有權限")
#         return
        
#     if len(context.args) < 2:
#         await update.message.reply_text("⚠️ 使用格式: /prom_chart <agent_id> <metric>\n例如: /prom_chart agent1 agent_cpu_usage_percent")
#         return
    
#     agent_id = context.args[0]
#     metric = context.args[1]
    
#     try:
#         # 查詢 Prometheus
#         prom_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
#         query = f'{metric}{{instance="{agent_id}:8001"}}'
        
#         end_time = datetime.now()
#         start_time = end_time - timedelta(hours=1)
        
#         params = {
#             'query': query,
#             'start': start_time.isoformat(),
#             'end': end_time.isoformat(),
#             'step': '60s'
#         }
        
#         response = requests.get(f"{prom_url}/api/v1/query_range", params=params, timeout=30)
#         data = response.json()
        
#         if data['status'] != 'success' or not data['data']['result']:
#             await update.message.reply_text(f"❌ 沒有找到 {metric} 的數據")
#             return
        
#         # 繪製圖表
#         plt.figure(figsize=(12, 6))
#         for result in data['data']['result']:
#             values = result['values']
#             timestamps = [datetime.fromtimestamp(float(v[0])) for v in values]
#             metrics = [float(v[1]) for v in values]
            
#             plt.plot(timestamps, metrics, label=f"{agent_id}-{metric}", linewidth=2)
        
#         plt.title(f'{metric} - {agent_id}', fontsize=14, fontweight='bold')
#         plt.xlabel('時間')
#         plt.ylabel('數值')
#         plt.legend()
#         plt.xticks(rotation=45)
#         plt.grid(True, alpha=0.3)
#         plt.tight_layout()
        
#         # 儲存並發送
#         chart_path = f'/tmp/{agent_id}_{metric}_chart.png'
#         plt.savefig(chart_path, dpi=150, bbox_inches='tight')
#         plt.close()
        
#         with open(chart_path, 'rb') as photo:
#             await update.message.reply_photo(
#                 photo=photo,
#                 caption=f"📊 {agent_id} - {metric} 監控圖表 (最近1小時)"
#             )
        
#         os.remove(chart_path)
        
#     except Exception as e:
#         await update.message.reply_text(f"❌ 圖表生成失敗: {e}")

start_test="""
🤖 這裡是 SeeServerHealth Agent-Server 架構版本！\n
現在支援分散式多 Agent 操作，我們提供以下功能：\n
🔧 Agent 管理
- /agents 查看所有可用的 agents
- /broadcast <cmd> 廣播指令到所有 agents\n
🖥 Server 控制 (需指定 agent)
- /op_exec <agent_id> <cmd> 在指定 agent 執行 shell 指令
- /op_port <agent_i> 查看指定 agent 的開啟 port
- /op_stop <agent_id> <port> 關閉指定 agent 的 port\n
📊 監控數據
- /mon_cpu 顯示 server 的 CPU 使用率
- /mon_cpu <agent_ip> 顯示指定 agent 的 CPU 使用率
- /mon_mem <agent_ip> 顯示指定 agent 的記憶體使用率
- /mon_disk <agent_ip> 顯示指定 agent 的磁碟使用率\n
- /mon_cpu_picture 顯示 server 5 分鐘前到現在的 CPU 使用率
- /mon_cpu_picture <agent_ip> 顯示指定 agent 5 分鐘前到現在的 CPU 使用率
- /mon_cpu_picture <agent_ip> <參數> 顯示指定 agent ?分鐘前到現在 CPU 使用率的圖片
- /mon_cpu_picture <agent_ip> <時間> <參數> 顯示指定 agent <時間> 前後 ? 分鐘內的CPU 使用率的圖片
cpu 可以換成 mem 或 disk 可以查看記憶體與磁碟使用率

"""

# /start 指令時顯示自訂鍵盤
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
            start_test,
        reply_markup=reply_markup
    )

# server terminal
async def more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    web_terminal_url = "https://573a-2001-e10-6840-107-e453-e7ba-3530-6c08.ngrok-free.app"
    out_text = "🔗 請點以下網址開啟並登入\n" + web_terminal_url
    await update.message.reply_text(
        out_text,
        reply_markup=reply_markup
    )

#GitHub link
async def more_info_GitHub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    web_terminal_url="https://github.com/cyleafish/See_Servers_Health_plus/tree/main"
    out_text= "請點以下網址查看 GitHub\n"+web_terminal_url
    await update.message.reply_text(
            out_text,
        reply_markup=reply_markup
    )

# 指令註冊
# app.add_handler(CommandHandler("op_exec", op_exec))
# app.add_handler(CommandHandler("op_stop", op_stop))
# app.add_handler(cpu_picture_handler())  # /cpu_picture

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("more", more))
app.add_handler(CommandHandler("more_info_GitHub", more_info_GitHub))

# Agent-Server architecture commands
app.add_handler(CommandHandler("agents", agents))
app.add_handler(CommandHandler("broadcast", broadcast))

app.add_handler(CommandHandler("op_exec", op_exec))
app.add_handler(CommandHandler("op_stop", op_stop))
app.add_handler(CommandHandler("op_port", op_port))

# New agent-based monitoring commands
app.add_handler(CommandHandler("mon_cpu", mon_cpu))
# app.add_handler(CommandHandler("mon_cpu", mon_cpu_agent))
app.add_handler(CommandHandler("mon_mem", mon_mem))
app.add_handler(CommandHandler("mon_disk", mon_disk))

# Chart generation commands
#app.add_handler(CommandHandler("chart", get_grafana_chart))
#app.add_handler(CommandHandler("prom_chart", create_prometheus_chart))

# Keep original monitoring commands for backward compatibility
app.add_handler(CommandHandler("mon_cpu_local", mon_cpu))
app.add_handler(CommandHandler("mon_cpu_picture", mon_cpu_picture))
app.add_handler(CommandHandler("mon_mem_local", mon_mem))
app.add_handler(CommandHandler("mon_mem_picture", mon_mem_picture))
app.add_handler(CommandHandler("mon_disk_local", mon_disk))
app.add_handler(CommandHandler("mon_disk_picture", mon_disk_picture))

if __name__ == "__main__":
    print("✅ Bot 開始運行")
    app.run_polling()
