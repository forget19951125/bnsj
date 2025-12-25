#!/bin/bash
cd "$(dirname "$0")"
export MYSQL_DATABASE=bnsj
export MYSQL_PASSWORD=""
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root

export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=""
export REDIS_DB=0

export JWT_SECRET=bn-auto-secret-key-2024
export ADMIN_TOKEN=admin-secret-token

export HOST=0.0.0.0
export PORT=8000
export DEBUG=True

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

