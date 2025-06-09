import threading
import time
import os
import requests
from datetime import datetime

class LoginWatcher:
    """
    從 monitor/login_alert.py 抽取的登入監控邏輯
    在 Agent 上監控登入事件，發送到 Server
    """
    
    def __init__(self, server_url, agent_id, log_file="/var/log/auth.log"):
        self.server_url = server_url
        self.agent_id = agent_id
        self.log_file = log_file
        self.running = False
        self.thread = None
        
    def send_alert_to_server(self, message):
        """發送警報到 Server"""
        try:
            response = requests.post(f"{self.server_url}/alert", json={
                "agent_id": self.agent_id,
                "alert_type": "login",
                "message": message,
                "timestamp": time.time()
            }, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ 登入警報已發送: {message}")
            else:
                print(f"❌ 發送警報失敗: {response.status_code}")
        except Exception as e:
            print(f"❌ 發送警報錯誤: {e}")
    
    def watch_login_events(self):
        """監控登入事件"""
        if not os.path.exists(self.log_file):
            print(f"⚠️ 日誌檔案不存在: {self.log_file}")
            return
            
        try:
            with open(self.log_file, "r") as f:
                # 移到檔案結尾（追蹤模式）
                f.seek(0, 2)
                
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(1)
                        continue
                    
                    # 跳過 cron 相關的日誌
                    if "cron:session" in line:
                        continue
                    
                    # 檢查失敗登入
                    if any(kw in line for kw in ["Failed password", "authentication failure", "invalid user"]):
                        alert_msg = f"🚫 [{self.agent_id}] 登入失敗嘗試：\n{line.strip()}"
                        self.send_alert_to_server(alert_msg)

                    elif any(kw in line for kw in ["Accepted password", "session opened", "New session", "sshd:session"]):
                        alert_msg = f"⚠️ [{self.agent_id}] 登入成功/啟動 session：\n{line.strip()}"
                        self.send_alert_to_server(alert_msg)

                    elif "sshd" in line and "Disconnected from user" in line:
                        alert_msg = f"🔌 [{self.agent_id}] SSH session 結束：\n{line.strip()}"
                        self.send_alert_to_server(alert_msg)

                        
        except Exception as e:
            print(f"❌ 登入監控錯誤: {e}")
    
    def start_watching(self):
        """開始監控"""
        if self.running:
            return {"success": False, "result": "登入監控已在運行"}
        
        self.running = True
        self.thread = threading.Thread(target=self.watch_login_events)
        self.thread.daemon = True
        self.thread.start()
        
        return {"success": True, "result": f"✅ [{self.agent_id}] 登入監控已啟動"}
    
    def stop_watching(self):
        """停止監控"""
        if not self.running:
            return {"success": False, "result": "登入監控未運行"}
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        return {"success": True, "result": f"✅ [{self.agent_id}] 登入監控已停止"}
    
    def get_status(self):
        """獲取監控狀態"""
        status = "運行中" if self.running else "已停止"
        return {
            "success": True, 
            "result": f"📊 [{self.agent_id}] 登入監控狀態: {status}"
        }