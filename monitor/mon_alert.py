from datetime import datetime, timedelta
import requests
import time
import os
from dotenv import load_dotenv
import threading

load_dotenv()

PROMETHEUS_URL = "http://host.docker.internal:9090"
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("ALLOWED_USER_IDS", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def send_tg_msg(text):
    try:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": text}
        )
    except Exception as e:
        print(f"❌ Telegram 發送失敗：{e}")

def get_prometheus_value(query, start, end, step=60):
    try:
        r = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step
        })
        data = r.json()
        if data["status"] == "success" and data["data"]["result"]:
            values = data["data"]["result"][0]["values"]
            return [float(v[1]) for v in values if v[1] != "NaN"]
    except Exception as e:
        print(f"❌ Prometheus 查詢錯誤：{e}")
    return []

def call_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "❓ AI 回應失敗")
    except Exception as e:
        return f"❌ Gemini 呼叫失敗：{e}"

def check_anomaly():
    now = datetime.utcnow()
    five_minutes_ago = now - timedelta(minutes=5)
    one_hour_ago = now - timedelta(hours=1)

    query = '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
    
    recent_data = get_prometheus_value(query, five_minutes_ago, now)
    history_data = get_prometheus_value(query, one_hour_ago, now)

    if not recent_data or not history_data:
        return

    recent_avg = sum(recent_data) / len(recent_data)
    history_avg = sum(history_data) / len(history_data)

    if recent_avg > history_avg * 2.5:
        prompt = (
            f"現在伺服器 CPU 使用率異常升高，過去 5 分鐘平均為 {recent_avg:.2f}%，"
            f"而過去 1 小時平均為 {history_avg:.2f}%。請分析可能原因並提供處理建議。"
        )
        result = call_gemini(prompt)
        send_tg_msg(f"⚠️ 檢測到 CPU 使用異常！\n\n{prompt}\n\n🤖 Gemini 建議：\n{result}")

def schedule_loop():
    while True:
        check_anomaly()
        time.sleep(300)

thread = threading.Thread(target=schedule_loop)
thread.start()
