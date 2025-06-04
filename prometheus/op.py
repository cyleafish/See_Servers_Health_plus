from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/exec", methods=["POST"])
def exec_cmd():
    data = request.json
    cmd = data.get("cmd", "")
    
    if "/op_stop" in cmd and "-p" in cmd:
        port = cmd.split("-p")[1].strip()
        try:
            pid = subprocess.check_output(f"lsof -ti tcp:{port}", shell=True).decode().strip()
            if pid:
                subprocess.run(f"kill -9 {pid}", shell=True)
                return f"✅ 已關閉 port {port}（PID: {pid})"
            else:
                return f"⚠️ port {port} 無對應程序"
        except:
            return "❌ 無法關閉 port"
    
    elif "/op_exec" in cmd:
        try:
            shell_cmd = cmd.replace("/op_exec", "").strip()
            output = subprocess.check_output(shell_cmd, shell=True).decode()
            return f"✅ 執行結果：\n{output}"
        except subprocess.CalledProcessError as e:
            return f"❌ 錯誤：{e.output.decode()}"
    
    return "未知操作"

app.run(port=8000)
