from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import requests

import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 讀取 token
TOKEN = os.getenv("your_bot_token")

#from op import op_exec
from cpu_test import mon_cpu_picture, mon_cpu
from mem import mon_mem_picture, mon_mem
from disk import mon_disk_picture, mon_disk

OPERATOR_URL = "http://localhost:8000/exec"  # 你本機跑的控制 API
PROMETHEUS_URL = "http://localhost:9090"

#按鈕
custom_keyboard = [
    ["/op_exec ps", "/op_port", "/op_stop"],
    ["/more"],
    ["/mon_cpu", "/mon_cpu_picture", "/mon_cpu_picture 20"],
    ["/mon_mem", "/mon_mem_picture", "/mon_mem_picture 20"],
    ["/mon_disk", "/mon_disk_picture", "/mon_disk_picture 20"],
    ["/more_info_GitHub"]
]
reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)


# /op_exec 指令
async def op_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = "/op_exec " + " ".join(context.args)
    try:
        response = requests.post(OPERATOR_URL, json={"cmd": cmd})
        result = response.text.strip() or "❓ 沒有回應內容"
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 呼叫控制 API 失敗：{e}")

# /op_stop 指令
async def op_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_allowed(update.effective_user.id):
        await update.message.reply_text("🚫 沒有權限")
        return

    if not context.args:
        await update.message.reply_text("⚠️ 請指定 port，例如 /op_stop 8080")
        return

    cmd = f"/op_stop -p {context.args[0]}"
    try:
        response = requests.post(OPERATOR_URL, json={"cmd": cmd})
        result = response.json().get("result", "❓ 沒有回應內容")
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ 呼叫控制 API 失敗：{e}")

# /start 指令時顯示自訂鍵盤
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
            "這裡是 SeeServerHealth，請選擇指令，下為指令說明: \n mon_cpu 為看當前cpu usage %數",
        reply_markup=reply_markup
    )

# server terminal

async def more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    web_terminal_url="https://8818-163-22-18-32.ngrok-free.app"
    out_text= "請點以下網址開啟並登入\n"+web_terminal_url
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

async def agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# 建立 bot 應用
app = ApplicationBuilder().token(TOKEN).build()
# 指令註冊
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("more", more))
app.add_handler(CommandHandler("more_info_GitHub", more_info_GitHub))

app.add_handler(CommandHandler("op_exec", op_exec))
app.add_handler(CommandHandler("op_stop", op_stop))

app.add_handler(CommandHandler("mon_cpu", mon_cpu))
app.add_handler(CommandHandler("mon_cpu_picture", mon_cpu_picture))

app.add_handler(CommandHandler("mon_mem", mon_mem))
app.add_handler(CommandHandler("mon_mem_picture", mon_mem_picture))

app.add_handler(CommandHandler("mon_disk", mon_disk))
app.add_handler(CommandHandler("mon_disk_picture", mon_disk_picture))
app.add_handler(CommandHandler("agent", agent))
app.run_polling()
