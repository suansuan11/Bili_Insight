#!/bin/bash

# Bili Insight One-Click Start Script
# Defines colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Bili Insight Project...${NC}"

# Function to kill process on a port
kill_port() {
    PORT=$1
    NAME=$2
    PID=$(lsof -t -i:$PORT)
    if [ -n "$PID" ]; then
        echo -e "${RED}Stopping existing $NAME (Port $PORT, PID: $PID)...${NC}"
        kill -9 $PID
    fi
}

# 1. Cleanup existing processes
echo -e "${GREEN}1. Cleaning up ports...${NC}"
kill_port 8001 "Python Service"
kill_port 8080 "Java Backend"
# Frontend often uses 5173, but vite might switch. We try to kill 5173 to be safe.
kill_port 5173 "Frontend"

# 2. Start Python Service
echo -e "${GREEN}2. Starting Python Service (Port 8001)...${NC}"
cd python_service
# Using nohup to run in background, output to log file
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > ../python_service.log 2>&1 &
PYTHON_PID=$!
cd ..
echo "Python Service started (PID: $PYTHON_PID). Logs: python_service.log"

# 3. Start Java Backend
echo -e "${GREEN}3. Starting Java Backend (Port 8080)...${NC}"

# Check java version - Should be system default (Java 8)
java -version 2>&1 | head -n 1

# Clean previous build artifacts to prevent version mismatch errors
# then run spring-boot
nohup sh -c 'mvn clean && mvn spring-boot:run' > java_backend.log 2>&1 &
JAVA_PID=$!
echo "Java Backend started (PID: $JAVA_PID). Logs: java_backend.log"

# 4. Start Frontend
echo -e "${GREEN}4. Starting Frontend...${NC}"
cd bili-insight-frontend
# Force port 5173 to avoid confusion
nohup npm run dev -- --port 5173 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend started (PID: $FRONTEND_PID). Logs: frontend.log"

echo -e "${GREEN}All services started!${NC}"
echo -e "Python API: http://localhost:8001"
echo -e "Java API:   http://localhost:8080"
echo -e "Frontend:   http://localhost:5173"
echo ""
echo -e "${RED}Press CTRL+C to stop all services...${NC}"

# Trap SIGINT (Ctrl+C) to kill child processes
cleanup() {
    echo -e "${RED}\nStopping all services...${NC}"
    kill $PYTHON_PID
    kill $JAVA_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup SIGINT

# Keep script running to maintain trap
wait
