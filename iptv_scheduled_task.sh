#!/bin/bash

# IPTV定时采集任务

LOG_FILE="iptv_scheduled.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "开始IPTV定时采集"

# 设置工作目录
cd "$(dirname "$0")" || exit 1

# 检测Python环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    log "错误：未检测到Python环境"
    exit 1
fi

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 运行采集脚本
$PYTHON_CMD .github/workflows/iptv.py

log "IPTV定时采集完成"
