from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 中文字體
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

PROMETHEUS_URL = 'http://localhost:9090'

import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 讀取 token
instance = os.getenv("your_server_ip")

# 判斷是否為 instance（ip:port）
def is_instance(s):
    agent_file="./prometheus/agent_name_ip.txt"
    agent_name_ip={}
    with open(agent_file, "r") as f:
        for line in f:
            if not line.strip():
                continue  # 跳過空行
            try:
                name, ip = line.strip().split()
                agent_name_ip[name]=ip
            except ValueError:
                print(f"⚠️ 格式錯誤（應為名稱 空格 IP:PORT）→ {line.strip()}")
    if (':' in s):
        return True, s
    if not s.isdigit():
        #agent_name_ip[s]
        return True, agent_name_ip[s]
    return False, s

# 處理參數，傳回 instance, start, end
def parse_cpu_picture_args(args):
    now = datetime.now()
    instance = os.getenv("your_server_ip")

    if not args:
        start = now - timedelta(minutes=5)
        end = now
    elif len(args) == 1:
        yn, resolved = resolve_instance(args[0])
        if yn:
            instance = resolved
            start = now - timedelta(minutes=5)
            end = now
        else:
            start = now - timedelta(minutes=int(args[0]))
            end = now
    elif len(args) == 2:
        yn, resolved = resolve_instance(args[0])
        if yn:
            instance = resolved
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
        yn, resolved = resolve_instance(args[0])
        instance = resolved if yn else args[0]
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
async def mon_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        yn, instance = is_instance(args[0])
    else:
        instance = os.getenv("your_server_ip")
    query = f'100 - (avg by (instance)(rate(node_cpu_seconds_total{{mode="idle",instance="{instance}"}}[1m])) * 100)'
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    result = response.json().get('data', {}).get('result', [])

    if not result:
        await update.message.reply_text(f"⚠️ 找不到 {instance} 的即時 CPU 資料")
        return

    value = float(result[0]['value'][1])
    timestamp = datetime.fromtimestamp(float(result[0]['value'][0]))
    await update.message.reply_text(f"🖥️ {instance} 即時 CPU 使用率：{value:.2f}%（時間：{timestamp.strftime('%H:%M:%S')}）")


# 查區段內 CPU 使用率並畫圖
async def mon_cpu_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instance = os.getenv("your_server_ip")
    try:
        args = context.args
        instance, start, end = parse_cpu_picture_args(args)
    except Exception as e:
        await update.message.reply_text(f"⚠️ 指令錯誤：{e}")
        return
    query = f'100 - (avg by (instance)(rate(node_cpu_seconds_total{{mode="idle",instance="{instance}"}}[1m])) * 100)'
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
        await update.message.reply_text(f"❌ 找不到 {instance} 的 CPU 資料，請確認 node_exporter 是否有啟動")
        return

    timestamps = [datetime.fromtimestamp(float(x[0])) for x in data[0]['values']]
    values = [float(x[1]) for x in data[0]['values']]

    plt.figure(figsize=(10, 4))
    plt.plot(timestamps, values, label='CPU Usage %', color='green', linewidth=3, linestyle='--')
    plt.title(f'{instance} 的 CPU 使用率')
    plt.xlabel('時間')
    plt.ylabel('%')
    plt.ylim(0, 100)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('cpu_usage.png')
    plt.close()

    with open('cpu_usage.png', 'rb') as photo:
        await update.message.reply_photo(photo=photo)


print("✅ Telegram Bot 開始運行")
