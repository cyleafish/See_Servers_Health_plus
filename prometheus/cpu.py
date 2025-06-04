# cpu.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

#chinese
import matplotlib.font_manager as fm

# 設定中文字體
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False  # 避免負號顯示錯誤

PROMETHEUS_URL = 'http://localhost:9090'
instance = '192.168.1.195:9090'

def is_ip(ip):
    if (":" in ip):
        return True
    else:
        return False

def parse_cpu_picture_args(args):
    now = datetime.now()
    
    if not args:
        # 沒有參數，預設抓「現在 - 5分鐘」到「現在」
        end = now
        start = now - timedelta(minutes=5)

    elif len(args) == 1:
        if (is_ip(args[0])):
            instance=args[0]
            end = now
            start = now - timedelta(minutes=5)
        else:# 一個參數：/cpu_picture 40
            end = now
            start = now - timedelta(minutes=int(args[0]))
    elif len(args) == 2:
        if (is_ip(args[0])):
            instance=args[0]
            end = now
            start = now - timedelta(minutes=int(args[1]))
        # 兩個參數：/cpu_picture 1940 10
        center = datetime.strptime(args[0], "%H%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        offset = int(args[1])
        start = center - timedelta(minutes=offset)
        end = center + timedelta(minutes=offset)
    elif len(args)==3:
        instance=args[0]
        center = datetime.strptime(args[1], "%H%M").replace(
        year=now.year, month=now.month, day=now.day
        )
        offset = int(args[2])
        start = center - timedelta(minutes=offset)
        end = center + timedelta(minutes=offset)
    else:
        raise ValueError("參數格式錯誤")

    return start, end


#當下的 cpu usage
async def mon_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args)==1:
        instance=args[0]
    else:
        instance="192.168.1.195:9100"
    query = f'100 - (rate(node_cpu_seconds_total{{instance="{instance}", mode="idle"}}[1m]) * 100)'
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query}
    )

    result = response.json().get('data', {}).get('result', [])
    if not result:
        return "⚠️ 找不到即時 CPU 使用資料"

    # 可能有多個 instance，這邊只取第一個
    value = float(result[0]['value'][1])
    timestamp = datetime.fromtimestamp(float(result[0]['value'][0]))
    await update.message.reply_text(f"🖥️ 即時 CPU 使用率：{value:.2f}%（時間：{timestamp.strftime('%H:%M:%S')}）")

#時間區段中的 cpu usage
async def mon_cpu_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 查詢 CPU 使用率的圖片
    try:
        args = context.args
        start, end = parse_cpu_picture_args(args)

        # 傳給 Prometheus 查詢，畫圖
        #chart_path = draw_cpu_usage_chart(start, end)

        #update.message.reply_photo(photo=open(chart_path, 'rb'))

    except Exception as e:
        update.message.reply_text(f"⚠️ 指令錯誤：{e}")
        return

    query ='100 - (rate(node_cpu_seconds_total{{instance="{instance}", mode="idle"}}[1m]) * 100)'
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": 15
        }
    )

    data = response.json()['data']['result']
    if not data:
        await update.message.reply_text("找不到 CPU 資料，請確認時間輸入正確且 Prometheus 有啟動並抓到 node_exporter。")
        return

    timestamps = [datetime.fromtimestamp(float(x[0])) for x in data[0]['values']]
    values = [float(x[1]) for x in data[0]['values']]

    # 繪圖
    plt.figure(figsize=(10, 4))
    plt.plot(timestamps, values, label='CPU Usage %', color='green', linewidth=3, linestyle='--')
    plt.title('CPU 使用率 ')
    plt.xlabel('時間')
    plt.ylabel('%')
    plt.ylim(0, 100)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('cpu_usage.png')
    plt.close()
    # 發送圖片
    with open('cpu_usage.png', 'rb') as photo:
        await update.message.reply_photo(photo=photo)

print("✅ Telegram Bot 開始運行")
