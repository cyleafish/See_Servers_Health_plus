from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 讀取 token
instance = os.getenv("your_server_ip")


# 中文字體
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

PROMETHEUS_URL = 'http://localhost:9090'

# 判斷是否為 instance（ip:port）
def is_instance(s):
    return ':' in s

# 處理參數，傳回 instance, start, end
def parse_mem_picture_args(args):
    now = datetime.now()
    instance = os.getenv("your_server_ip")
    if not args:
        # /mem_picture
        start = now - timedelta(minutes=5)
        end = now
    elif len(args) == 1:
        if is_instance(args[0]):
            instance = args[0]
            start = now - timedelta(minutes=5)
            end = now
        else:
            start = now - timedelta(minutes=int(args[0]))
            end = now
    elif len(args) == 2:
        if is_instance(args[0]):
            instance = args[0]
            start = now - timedelta(minutes=int(args[1]))
            end = now
        else:
            center = datetime.strptime(args[0], "%H%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            offset = int(args[1])
            start = center - timedelta(minutes=offset)
            end = center + timedelta(minutes=offset)
    elif len(args) == 3:
        instance = args[0]
        center = datetime.strptime(args[1], "%H%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        offset = int(args[2])
        start = center - timedelta(minutes=offset)
        end = center + timedelta(minutes=offset)
    else:
        raise ValueError("參數格式錯誤")

    return instance, start, end


# 查即時 CPU 使用率
async def mon_mem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and is_instance(args[0]):
        instance = args[0]
    else:
        instance = os.getenv("your_server_ip")
    query = f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}})) * 100'
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    result = response.json().get('data', {}).get('result', [])

    if not result:
        await update.message.reply_text(f"⚠️ 找不到 {instance} 的即時 Memory 資料")
        return

    value = float(result[0]['value'][1])
    timestamp = datetime.fromtimestamp(float(result[0]['value'][0]))
    await update.message.reply_text(f"🖥️ {instance} 即時 Memory 使用率：{value:.2f}%（時間：{timestamp.strftime('%H:%M:%S')}）")


# 查區段內 CPU 使用率並畫圖
async def mon_mem_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instance = os.getenv("your_server_ip")
    try:
        args = context.args
        instance, start, end = parse_mem_picture_args(args)
    except Exception as e:
        await update.message.reply_text(f"⚠️ 指令錯誤：{e}")
        return
    query = f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}})) * 100'
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": 15
        }
    )

    data = response.json().get('data', {}).get('result', [])
    if not data:
        await update.message.reply_text(f"❌ 找不到 {instance} 的 Memory 資料，請確認 node_exporter 是否有啟動")
        return

    timestamps = [datetime.fromtimestamp(float(x[0])) for x in data[0]['values']]
    values = [float(x[1]) for x in data[0]['values']]

    plt.figure(figsize=(10, 4))
    plt.plot(timestamps, values, label='Memory Usage %', color='blue', linewidth=3, linestyle='--')
    plt.title(f'{instance} 的 Memory 使用率')
    plt.xlabel('時間')
    plt.ylabel('%')
    plt.ylim(0, 100)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('mem_usage.png')
    plt.close()

    with open('mem_usage.png', 'rb') as photo:
        await update.message.reply_photo(photo=photo)


print("✅ Telegram Bot 開始運行")
