import subprocess
import json

def execute_shell_command(cmd):
    """
    從 control/op.py 抽取的 shell 指令執行邏輯
    統一處理 /op_exec, /op_stop, /op_port 指令
    """
    
    if "/op_stop" in cmd and "-p" in cmd:
        port = cmd.split("-p")[1].strip()
        try:
            pid = subprocess.check_output(f"lsof -ti tcp:{port}", shell=True).decode().strip()
            if pid:
                subprocess.run(f"kill -9 {pid}", shell=True)
                return {"success": True, "result": f"✅ 已關閉 port {port}（PID: {pid})"}
            else:
                return {"success": True, "result": f"⚠️ port {port} 無對應程序"}
        except Exception as e:
            return {"success": False, "result": f"❌ 無法關閉 port：{e}"}

    elif "/op_exec" in cmd:
        try:
            shell_cmd = cmd.replace("/op_exec", "").strip()
            # 安全檢查：禁止危險指令
            dangerous_commands = ['sudo', 'rm -rf', 'mkfs', 'dd if=', 'chmod 777', '> /dev/', 'format']
            if any(dangerous in shell_cmd.lower() for dangerous in dangerous_commands):
                return {"success": False, "result": f"❌ 安全限制：禁止執行危險指令"}
            
            output = subprocess.check_output(shell_cmd, shell=True, timeout=30).decode()
            return {"success": True, "result": f"✅ 執行結果：\n{output}"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "result": f"❌ 錯誤：{e.output.decode() if e.output else str(e)}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "result": f"❌ 指令執行超時"}
        except Exception as e:
            return {"success": False, "result": f"❌ 其他錯誤：{e}"}
    
    elif "/op_port" in cmd:
        try:
            output = subprocess.check_output("ss -tuln", shell=True).decode()
            ports = []
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    addr_port = parts[4]
                    port = addr_port.split(":")[-1]
                    if port.isdigit():
                        ports.append(port)
            ports = sorted(set(ports), key=int)
            
            if ports:
                message = "📡 目前系統有以下 port 正在監聽：\n"
                for port in ports:
                    message += f"- Port {port}\n"
            else:
                message = "⚠️ 沒有偵測到任何正在監聽的 port"

            return {"success": True, "result": message}
        except Exception as e:
            return {"success": False, "result": f"❌ 查詢錯誤：{e}"}

    return {"success": False, "result": "❓ 未知操作"}