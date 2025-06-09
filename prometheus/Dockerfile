# prometheus/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 複製 alert.py 和 requirements.txt（如果有）
COPY alert.py . 
COPY requirements.txt .  
# 包含 python-telegram-bot、requests、python-dotenv

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "alert.py"]
