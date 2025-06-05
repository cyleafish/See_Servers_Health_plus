# See_Servers_Health_plus
See_Server_Health 的進階版，改用成 Agent-Server-Client 架構

## 修改的地方與執行方法
### 需要先在每台 Agent 中下載 Node_exporter
```
wget https://github.com/prometheus/node_exporter/releases/latest/download/node_exporter-1.9.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.9.1.linux-amd64.tar.gz
cd node_exporter-1.9.1.linux-amd64
./node_exporter &
```
### 把每台 Agent 的 ip 加入 `prometheus.yml` 的 `scrape_configs:` 中，範例如下
```
scrape_configs:
  - job_name: '<Server name>'
    static_configs:
      - targets: ['<Server1 ip>:9100']
```
### app.py cpu.py ... 修改
- 更改判斷 `/mon_cpu` ... 等地方
- 詳情請直接去看檔案

### docker 重新起動
    - `sudo docker restart prometheus_prometheus_1`
    - `sudo docker-compose up -d`
### 執行 `app.py`
- `python3 app.py`
