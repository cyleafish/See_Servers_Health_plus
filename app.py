from telegram import Update,ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import requests

from monitor.cpu import mon_cpu_picture, mon_cpu
from monitor.mem import mon_mem_picture, mon_mem
from monitor.disk import mon_disk_picture, mon_disk
from utils.whitelist import is_user_allowed
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
app = ApplicationBuilder().token(BOT_TOKEN).build()

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8002")

#按鈕
custom_keyboard = [
    ["/op_exec agent1 ps", "/op_port agent1", "/op_stop agent1"],
    ["/agents", "/mon_cpu agent1", "/broadcast ps"],
    ["/mon_mem agent1", "/mon_disk agent1"],
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
async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    try:
        response = requests.get(f"{SERVER_URL}/agents")
        data = response.json()
        agents_list = data.get("agents", [])
        
        if not agents_list:
            await update.message.reply_text("⚠️ 目前沒有可用的 agents")
            return
        
        message = "🤖 可用的 Agents:\n"
        for agent in agents_list:
            status_emoji = "🟢" if agent["status"] == "active" else "🔴"
            message += f"{status_emoji} {agent['agent_id']} ({agent['host']}:{agent['port']}) - {agent['status']}\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ 獲取 agents 失敗：{e}")

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
async def mon_cpu_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if not context.args:
        await update.message.reply_text("⚠️ 使用格式: /mon_cpu <agent_id>\n例如: /mon_cpu agent1")
        return

    agent_id = context.args[0]
    
    try:
        response = requests.post(f"{SERVER_URL}/exec", json={
            "agent_id": agent_id,
            "cmd": "cpu",
            "type": "monitor"
        })
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 監控失敗：{e}")

async def mon_mem_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if not context.args:
        await update.message.reply_text("⚠️ 使用格式: /mon_mem <agent_id>\n例如: /mon_mem agent1")
        return

    agent_id = context.args[0]
    
    try:
        response = requests.post(f"{SERVER_URL}/exec", json={
            "agent_id": agent_id,
            "cmd": "mem",
            "type": "monitor"
        })
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 監控失敗：{e}")

async def mon_disk_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if not context.args:
        await update.message.reply_text("⚠️ 使用格式: /mon_disk <agent_id>\n例如: /mon_disk agent1")
        return

    agent_id = context.args[0]
    
    try:
        response = requests.post(f"{SERVER_URL}/exec", json={
            "agent_id": agent_id,
            "cmd": "disk",
            "type": "monitor"
        })
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 監控失敗：{e}")

start_test="""
🤖 這裡是 SeeServerHealth Agent-Server 架構版本！\n
現在支援分散式多 Agent 操作，我們提供以下功能：\n
🔧 Agent 管理
- /agents 查看所有可用的 agents
- /broadcast <cmd> 廣播指令到所有 agents\n
🖥️ Server 控制 (需指定 agent)
- /op_exec <agent_id> <cmd> 在指定 agent 執行 shell 指令
- /op_port <agent_id> 查看指定 agent 的開啟 port
- /op_stop <agent_id> <port> 關閉指定 agent 的 port\n
📊 監控數據 (需指定 agent)
- /mon_cpu <agent_id> 顯示指定 agent 的 CPU 使用率
- /mon_mem <agent_id> 顯示指定 agent 的記憶體使用率
- /mon_disk <agent_id> 顯示指定 agent 的磁碟使用率\n
例如: /op_exec agent1 ls -l 或 /mon_cpu agent1
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
    web_terminal_url="https://github.com/cyleafish/See-Server-Health/tree/main"
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
app.add_handler(CommandHandler("mon_cpu", mon_cpu_agent))
app.add_handler(CommandHandler("mon_mem", mon_mem_agent))
app.add_handler(CommandHandler("mon_disk", mon_disk_agent))

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
