from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import os

# === 中文字體設定 ===
plt.rcParams['font.family'] = 'Noto Sans CJK JP'  # 你有安裝 Noto Sans CJK JP
plt.rcParams['axes.unicode_minus'] = False

# === Bot Token & Prometheus URL ===
BOT_TOKEN = '8114141180:AAFrHkrSkomz0eswNDSoh7uTSTTihZsz4Rk'
PROMETHEUS_URL = 'http://localhost:9090'


# === 參數解析 ===
def parse_cpu_picture_args(args):
    now = datetime.now()

    if not args:
        end = now
        start = now - timedelta(minutes=5)
    elif len(args) == 1:
        center = datetime.strptime(args[0], "%H%M").replace(year=now.year, month=now.month, day=now.day)
        start = center - timedelta(minutes=5)
        end = center + timedelta(minutes=5)
    elif len(args) == 2:
        center = datetime.strptime(args[0], "%H%M").replace(year=now.year, month=now.month, day=now.day)
        offset = int(args[1])
        start = center - timedelta(minutes=offset)
        end = center + timedelta(minutes=offset)
    else:
        raise ValueError("參數格式錯誤")
    return start, end


# === 畫圖函數 ===
def draw_cpu_usage_chart(start: datetime, end: datetime) -> str:
    query = '100 - (avg by (instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    step = '15'  # 每15秒一筆資料

    # Prometheus API 查詢
    url = f'{PROMETHEUS_URL}/api/v1/query_range'
    params = {
        'query': query,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'step': step,
    }

    resp = requests.get(url, params=params)
    data = resp.json()

    # 畫圖處理
    results = data['data']['result']
    if not results:
        raise ValueError("查無資料，可能時間區間不對")

    plt.figure(figsize=(10, 5))
    for result in results:
        timestamps = [datetime.fromtimestamp(float(v[0])) for v in result['values']]
        values = [float(v[1]) for v in result['values']]
        plt.plot(timestamps, values, label=result['metric'].get('instance', 'unknown'))

    plt.title("CPU 使用率 (%)")
    plt.xlabel("時間")
    plt.ylabel("使用率 (%)")
    plt.ylim(0, 100)  # y 軸 0～100%
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gcf().autofmt_xdate()
    plt.grid(True)
    plt.legend()

    path = '/tmp/cpu_usage.png'
    plt.savefig(path)
    plt.close()
    return path


# === Bot 指令處理 ===
async def cpu_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        start, end = parse_cpu_picture_args(args)
        chart_path = draw_cpu_usage_chart(start, end)
        await update.message.reply_photo(photo=open(chart_path, 'rb'))
    except Exception as e:
        await update.message.reply_text(f"⚠️ 錯誤：{e}")


# === Bot 啟動 ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("cpu_picture", cpu_picture))
    print("Bot 已啟動")
    app.run_polling()


if __name__ == "__main__":
    main()

