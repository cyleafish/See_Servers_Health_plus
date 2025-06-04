from flask import Flask, request, jsonify
import os
import requests
import time
import threading
from dotenv import load_dotenv
import json
import psutil
from prometheus_client import generate_latest, CollectorRegistry, Gauge, Counter

# 導入 Agent 專用模組
from agent_modules.shell_ops import execute_shell_command
from agent_modules.monitoring import handle_monitoring_command
from agent_modules.login_watcher import LoginWatcher

load_dotenv()

app = Flask(__name__)

# Agent configuration
AGENT_ID = os.getenv("AGENT_ID", "agent1")
AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8001"))
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8002")

# 初始化登入監控器
login_watcher = LoginWatcher(SERVER_URL, AGENT_ID)

# Prometheus metrics 初始化
registry = CollectorRegistry()
cpu_usage = Gauge('agent_cpu_usage_percent', 'CPU usage percentage', ['agent_id'], registry=registry)
memory_usage = Gauge('agent_memory_usage_percent', 'Memory usage percentage', ['agent_id'], registry=registry)
disk_usage = Gauge('agent_disk_usage_percent', 'Disk usage percentage', ['agent_id'], registry=registry)
requests_total = Counter('agent_requests_total', 'Total requests', ['agent_id', 'method', 'endpoint'], registry=registry)

def update_system_metrics():
    """更新系統指標"""
    try:
        cpu_usage.labels(agent_id=AGENT_ID).set(psutil.cpu_percent())
        memory_usage.labels(agent_id=AGENT_ID).set(psutil.virtual_memory().percent)
        disk_usage.labels(agent_id=AGENT_ID).set(psutil.disk_usage('/').percent)
    except Exception as e:
        print(f"⚠️ Metrics update error: {e}")

@app.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint"""
    try:
        update_system_metrics()
        requests_total.labels(agent_id=AGENT_ID, method="GET", endpoint="/metrics").inc()
        return generate_latest(registry), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"Error generating metrics: {e}", 500

@app.route("/exec", methods=["POST"])
def exec_cmd():
    """Execute commands sent from the server"""
    data = request.json
    cmd = data.get("cmd", "")
    cmd_type = data.get("type", "shell")
    
    try:
        if cmd_type == "shell":
            result = execute_shell_command(cmd)
            # 添加 Agent ID 標識
            result["result"] = f"[{AGENT_ID}] {result['result']}"
            return jsonify(result)
            
        elif cmd_type == "monitor":
            result = handle_monitoring_command(cmd)
            # 添加 Agent ID 標識
            result["result"] = f"[{AGENT_ID}] {result['result']}"
            return jsonify(result)
            
        elif cmd_type == "login":
            return handle_login_command(cmd)
            
        else:
            return jsonify({"success": False, "result": f"❌ [{AGENT_ID}] Unknown command type: {cmd_type}"})
    except Exception as e:
        return jsonify({"success": False, "result": f"❌ [{AGENT_ID}] Agent error: {str(e)}"})

def handle_login_command(cmd):
    """處理登入監控相關指令"""
    try:
        if "start" in cmd.lower():
            return jsonify(login_watcher.start_watching())
        elif "stop" in cmd.lower():
            return jsonify(login_watcher.stop_watching())
        elif "status" in cmd.lower():
            return jsonify(login_watcher.get_status())
        else:
            return jsonify({"success": False, "result": f"❌ [{AGENT_ID}] 未知登入監控指令: {cmd}"})
    except Exception as e:
        return jsonify({"success": False, "result": f"❌ [{AGENT_ID}] 登入監控錯誤: {str(e)}"})

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for the server"""
    try:
        # 更新 Prometheus metrics
        update_system_metrics()
        requests_total.labels(agent_id=AGENT_ID, method="GET", endpoint="/health").inc()
        
        # 使用 monitoring 模組的功能
        cpu_info = handle_monitoring_command("cpu")
        mem_info = handle_monitoring_command("mem")
        disk_info = handle_monitoring_command("disk")
        
        return jsonify({
            "agent_id": AGENT_ID,
            "status": "healthy",
            "timestamp": time.time(),
            "login_watcher_status": "running" if login_watcher.running else "stopped",
            "system_info": {
                "cpu": cpu_info.get("data", {}),
                "memory": mem_info.get("data", {}),
                "disk": disk_info.get("data", {})
            }
        })
    except Exception as e:
        return jsonify({
            "agent_id": AGENT_ID,
            "status": "error",
            "timestamp": time.time(),
            "error": str(e)
        })

def register_with_server():
    """Register this agent with the central server"""
    registration_data = {
        "agent_id": AGENT_ID,
        "host": AGENT_HOST,
        "port": AGENT_PORT,
        "capabilities": ["shell", "monitor", "login"]
    }
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.post(f"{SERVER_URL}/register", json=registration_data, timeout=10)
            if response.status_code == 200:
                print(f"✅ Agent {AGENT_ID} registered successfully with server")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to register with server (attempt {retry_count + 1}): {e}")
        
        retry_count += 1
        time.sleep(5)
    
    print(f"❌ Failed to register after {max_retries} attempts")
    return False

def send_heartbeat():
    """Send periodic heartbeat to server"""
    while True:
        try:
            response = requests.post(f"{SERVER_URL}/heartbeat", 
                                   json={"agent_id": AGENT_ID, "timestamp": time.time()}, 
                                   timeout=5)
            if response.status_code != 200:
                print(f"⚠️ Heartbeat failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Heartbeat error: {e}")
        
        time.sleep(30)  # Send heartbeat every 30 seconds

if __name__ == "__main__":
    print(f"🤖 Starting Agent {AGENT_ID} on {AGENT_HOST}:{AGENT_PORT}")
    
    # Register with server in a separate thread
    registration_thread = threading.Thread(target=register_with_server)
    registration_thread.daemon = True
    registration_thread.start()
    
    # Start heartbeat in a separate thread
    heartbeat_thread = threading.Thread(target=send_heartbeat)
    heartbeat_thread.daemon = True
    heartbeat_thread.start()
    
    # Start Flask app
    app.run(host=AGENT_HOST, port=AGENT_PORT, debug=False)