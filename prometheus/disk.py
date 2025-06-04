# disk.py

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

def parse_disk_picture_args(args):
    now = datetime.now()
    
    if not args:
        # 沒有參數，預設抓「現在 - 5分鐘」到「現在」
        end = now
        start = now - timedelta(minutes=5)
    elif len(args) == 1:
        # 一個參數：/cpu_picture 40
        end = now
        start = now - timedelta(minutes=int(args[0]))
    elif len(args) == 2:
        # 兩個參數：/cpu_picture 1940 10
        center = datetime.strptime(args[0], "%H%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        offset = int(args[1])
        start = center - timedelta(minutes=offset)
        end = center + timedelta(minutes=offset)
    else:
        raise ValueError("參數格式錯誤")

    return start, end


#當下的 disk usage
async def mon_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = '100 * (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"}'
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query}
    )

    result = response.json().get('data', {}).get('result', [])
    if not result:
        return "⚠️ 找不到即時 Disk 使用資料"

    # 可能有多個 instance，這邊只取第一個
    value = float(result[0]['value'][1])
    timestamp = datetime.fromtimestamp(float(result[0]['value'][0]))
    await update.message.reply_text(f"🖥️ 即時 Disk 使用率：{value:.2f}%（時間：{timestamp.strftime('%H:%M:%S')}）")

#時間區段中的 disk usage
async def mon_disk_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 查詢 disk 使用率的圖片
    try:
        args = context.args
        start, end = parse_disk_picture_args(args)

        # 傳給 Prometheus 查詢，畫圖
        #chart_path = draw_mem_usage_chart(start, end)

        #update.message.reply_photo(photo=open(chart_path, 'rb'))

    except Exception as e:
        update.message.reply_text(f"⚠️ 指令錯誤：{e}")
        return

    query = '100 * (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"}'
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
        await update.message.reply_text("找不到 Disk 資料，請確認時間輸入正確且 Prometheus 有啟動並抓到 node_exporter。")
        return

    timestamps = [datetime.fromtimestamp(float(x[0])) for x in data[0]['values']]
    values = [float(x[1]) for x in data[0]['values']]

    # 繪圖
    plt.figure(figsize=(10, 4))
    plt.plot(timestamps, values, label='Disk Usage %', color='purple', linewidth=3, linestyle='--')
    plt.title('Disk 使用率 ')
    plt.xlabel('時間')
    plt.ylabel('%')
    plt.ylim(0, 100)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('disk_usage.png')
    plt.close()
    # 發送圖片
    with open('disk_usage.png', 'rb') as photo:
        await update.message.reply_photo(photo=photo)

