import yaml

import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 讀取 token
instance = os.getenv("your_server_ip")

# Server job list（可依需求擴充）
custom_jobs = [
    {"job_name": "prometheus", "targets": ["localhost:9090"]},
    {"job_name": "cadvisor", "targets": ["cadvisor:8080"]},
    {"job_name": "node-exporter", "targets": ["node-exporter:9100"]},
    {"job_name": "Server", "targets": [instance]},
    {"job_name": "Agent1", "targets": ["192.168.1.209:9100"]},
    {"job_name": "Agent2", "targets": ["146.190.147.94:9100"]},
]

# Prometheus config
prom_config = {
    'global': {
        'scrape_interval': '15s',
        'evaluation_interval': '15s',
        'external_labels': {
            'monitor': 'my-project'
        }
    },
    'rule_files': [
        'alert.rules',
        # 'first.rules',
        # 'second.rules'
    ],
    'alerting': {
        'alertmanagers': [
            {
                'scheme': 'http',
                'static_configs': [
                    {'targets': ['alertmanager:9093']}
                ]
            }
        ]
    },
    'scrape_configs': []
}

# Add all jobs
for job in custom_jobs:
    prom_config['scrape_configs'].append({
        'job_name': job['job_name'],
        'scrape_interval': '15s',
        'static_configs': [
            {'targets': job['targets']}
        ]
    })

# 輸出為 prometheus.yml
with open("prometheus.yml", "w") as f:
    yaml.dump(prom_config, f, default_flow_style=False, sort_keys=False)

print("✅ 已成功生成 prometheus.yml")

