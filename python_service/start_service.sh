#!/bin/bash
cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

UVICORN_BIN=".venv/bin/uvicorn"
if [ ! -x "$UVICORN_BIN" ] && [ -x "venv/bin/uvicorn" ]; then
  UVICORN_BIN="venv/bin/uvicorn"
fi

if [ ! -x "$UVICORN_BIN" ]; then
  echo "未找到 uvicorn 可执行文件，请先安装 Python 依赖。"
  exit 1
fi

mkdir -p logs
nohup "$UVICORN_BIN" app.main:app --host 0.0.0.0 --port 8001 --log-level info > logs/service.log 2>&1 &
SERVICE_PID=$!
echo "Python服务已启动，日志文件: logs/service.log"
echo "服务进程PID: ${SERVICE_PID}"
echo "查看日志: tail -f logs/service.log"
