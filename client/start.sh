#!/bin/bash
cd "$(dirname "$0")"

# 设置环境变量
export PYTHONUNBUFFERED=1

# 启动客户端
python3 -m app.main 2>&1 | tee client.log

