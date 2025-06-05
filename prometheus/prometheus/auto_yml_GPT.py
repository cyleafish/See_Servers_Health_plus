import os
from dotenv import load_dotenv

# 載入 .env 檔案（如需預設 IP）
load_dotenv()

# Prometheus 基本設定（含預設 jobs）
base_config = """# my global config
global:
  scrape_interval:     15s
  evaluation_interval: 15s
  # scrape_timeout is set to the global default (10s).

  external_labels:
      monitor: 'my-project'

rule_files:
  - 'alert.rules'

alerting:
  alertmanagers:
  - scheme: http
    static_configs:
    - targets:
      - "alertmanager:9093"

scrape_configs:
  - job_name: 'prometheus'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cadvisor'
    scrape_interval: 15s
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'node-exporter'
    scrape_interval: 15s
    static_configs:
      - targets: ['node-exporter:9100']
"""

# 加入 agent list
agent_jobs = ""
agent_file = "agent_name_ip.txt"

if os.path.exists(agent_file):
    with open(agent_file, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                name, ip = line.strip().split()
                agent_jobs += f"""
  - job_name: '{name}'

    # Override the global default and scrape targets from this job every 5 seconds.
    scrape_interval: 15s

    static_configs:
      - targets: ['{ip}']"""
            except ValueError:
                print(f"⚠️ 格式錯誤：{line.strip()}")
else:
    print("❌ 找不到 agent_name_ip.txt")

# 合併內容
final_yml = base_config + agent_jobs

# 寫入 prometheus.yml
with open("prometheus.yml", "w") as f:
    f.write(final_yml)

print("✅ 已成功生成 prometheus.yml（含格式與註解）")

