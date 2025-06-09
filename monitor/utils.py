# monitor/utils.py - 監控工具函數

import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# 設定中文字體
plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams['axes.unicode_minus'] = False

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

def is_instance(s):
    """判斷字串是否為 instance 格式 (ip:port)"""
    return ':' in s and len(s.split(':')) == 2

def get_prometheus_targets():
    """獲取 Prometheus 的所有監控目標"""
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=10)
        data = resp.json()
        
        if data['status'] == 'success':
            active_targets = data['data']['activeTargets']
            return [
                {
                    'instance': target.get("labels", {}).get("instance", "Unknown"),
                    'job': target.get("labels", {}).get("job", "Unknown"),
                    'health': target.get("health", "unknown")
                }
                for target in active_targets
            ]
        return []
    except Exception as e:
        print(f"獲取 Prometheus targets 失敗: {e}")
        return []

def parse_monitor_args(args, default_instance='localhost:9100'):
    """
    解析監控指令參數
    支援格式：
    - /mon_cpu                    -> 預設 instance, 5分鐘
    - /mon_cpu 192.168.1.100:9100 -> 指定 instance, 5分鐘
    - /mon_cpu 30                 -> 預設 instance, 30分鐘
    - /mon_cpu 192.168.1.100:9100 30 -> 指定 instance, 30分鐘
    """
    now = datetime.now()
    instance = default_instance
    
    if not args:
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
            # 時間格式：1940 10 (中心時間和偏移)
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

def query_prometheus_instant(query):
    """查詢 Prometheus 即時數據"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=10
        )
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']['result']
        else:
            print(f"Prometheus 查詢失敗: {data.get('error', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Prometheus 查詢錯誤: {e}")
        return []

def query_prometheus_range(query, start, end, step=15):
    """查詢 Prometheus 範圍數據"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": query,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step
            },
            timeout=30
        )
        data = response.json()
        
        if data['status'] == 'success':
            return data['data']['result']
        else:
            print(f"Prometheus 範圍查詢失敗: {data.get('error', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Prometheus 範圍查詢錯誤: {e}")
        return []

def create_monitoring_chart(data, title, instance, metric_name, color='blue', filename='chart.png'):
    """創建監控圖表"""
    if not data or not data[0].get('values'):
        return None
        
    timestamps = [datetime.fromtimestamp(float(x[0])) for x in data[0]['values']]
    values = [float(x[1]) for x in data[0]['values']]
    
    plt.figure(figsize=(12, 6))
    plt.plot(timestamps, values, label=f'{metric_name} %', color=color, linewidth=3)
    plt.title(f'{instance} 的 {title}', fontsize=14, fontweight='bold')
    plt.xlabel('時間')
    plt.ylabel('%')
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filename

# 預定義的查詢語句
QUERIES = {
    'cpu_usage': '100 - (avg by (instance)(rate(node_cpu_seconds_total{{mode="idle",instance="{instance}"}}[1m])) * 100)',
    'memory_usage': '(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}})) * 100',
    'disk_usage': '100 * (node_filesystem_size_bytes{{mountpoint="/",instance="{instance}"}} - node_filesystem_free_bytes{{mountpoint="/",instance="{instance}"}}) / node_filesystem_size_bytes{{mountpoint="/",instance="{instance}"}}'
}

def get_metric_query(metric_type, instance):
    """獲取指定類型的查詢語句"""
    if metric_type not in QUERIES:
        raise ValueError(f"不支援的 metric 類型: {metric_type}")
    
    return QUERIES[metric_type].format(instance=instance)