#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
mkdir -p logs
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info > logs/service.log 2>&1 &
echo "Python服务已启动，日志文件: logs/service.log"
echo "查看日志: tail -f logs/service.log"
