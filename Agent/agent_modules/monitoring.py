import psutil
import time
from datetime import datetime
import subprocess

def get_cpu_usage():
    """獲取 CPU 使用率"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        return {
            "success": True, 
            "result": f"🖥️ CPU使用率: {cpu_percent}%",
            "data": {"cpu_percent": cpu_percent, "timestamp": time.time()}
        }
    except Exception as e:
        return {"success": False, "result": f"❌ CPU監控錯誤: {str(e)}"}

def get_memory_usage():
    """獲取記憶體使用率"""
    try:
        memory = psutil.virtual_memory()
        return {
            "success": True, 
            "result": f"💾 記憶體使用率: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)",
            "data": {
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used // 1024 // 1024,
                "memory_total_mb": memory.total // 1024 // 1024,
                "timestamp": time.time()
            }
        }
    except Exception as e:
        return {"success": False, "result": f"❌ 記憶體監控錯誤: {str(e)}"}

def get_disk_usage():
    """獲取磁碟使用率"""
    try:
        disk = psutil.disk_usage('/')
        return {
            "success": True, 
            "result": f"💿 磁碟使用率: {disk.percent}% ({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)",
            "data": {
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used // 1024 // 1024 // 1024,
                "disk_total_gb": disk.total // 1024 // 1024 // 1024,
                "timestamp": time.time()
            }
        }
    except Exception as e:
        return {"success": False, "result": f"❌ 磁碟監控錯誤: {str(e)}"}

def get_system_info():
    """獲取系統基本資訊"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        load_avg = ""
        try:
            # Linux 系統負載
            load1, load5, load15 = psutil.getloadavg()
            load_avg = f"負載: {load1:.2f}, {load5:.2f}, {load15:.2f}"
        except:
            load_avg = "負載資訊不可用"
        
        result = f"""🖥️ 系統資訊:
⏱️ 開機時間: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
⏰ 運行時間: {str(uptime).split('.')[0]}
📊 {load_avg}
🔄 CPU核心數: {psutil.cpu_count()}"""
        
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "result": f"❌ 系統資訊錯誤: {str(e)}"}

def get_network_info():
    """獲取網路資訊"""
    try:
        network_io = psutil.net_io_counters()
        result = f"""🌐 網路資訊:
📤 傳送: {network_io.bytes_sent // 1024 // 1024}MB
📥 接收: {network_io.bytes_recv // 1024 // 1024}MB
📦 封包傳送: {network_io.packets_sent}
📦 封包接收: {network_io.packets_recv}"""
        
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "result": f"❌ 網路資訊錯誤: {str(e)}"}

def handle_monitoring_command(cmd):
    """處理監控指令的統一入口"""
    if "cpu" in cmd.lower():
        if "info" in cmd.lower():
            return get_system_info()
        else:
            return get_cpu_usage()
    elif "mem" in cmd.lower() or "memory" in cmd.lower():
        return get_memory_usage()
    elif "disk" in cmd.lower():
        return get_disk_usage()
    elif "network" in cmd.lower() or "net" in cmd.lower():
        return get_network_info()
    elif "system" in cmd.lower() or "info" in cmd.lower():
        return get_system_info()
    else:
        return {"success": False, "result": f"❌ 未知監控指令: {cmd}"}