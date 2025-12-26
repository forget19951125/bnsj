#!/bin/bash

# 部署脚本 - 将服务器部署到远程服务器
# 使用方法: ./deploy.sh

set -e

SERVER_IP="45.61.148.208"
SERVER_USER="root"
SERVER_PASSWORD="5Dw97H1zmtZNwX"
PROJECT_DIR="/opt/bnsj"
REPO_URL="git@github.com:forget19951125/bnsj.git"

echo "=========================================="
echo "开始部署到服务器: $SERVER_IP"
echo "=========================================="

# 使用sshpass执行远程命令
ssh_exec() {
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@$SERVER_IP "$@"
}

# 使用sshpass复制文件
scp_exec() {
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$@"
}

echo ""
echo "1. 检查服务器环境..."
ssh_exec "echo '✓ SSH连接成功'"

# 检查Python
echo "检查Python..."
PYTHON_VERSION=$(ssh_exec "python3 --version 2>&1 || echo '未安装'")
echo "  $PYTHON_VERSION"

# 检查Git
echo "检查Git..."
GIT_VERSION=$(ssh_exec "git --version 2>&1 || echo '未安装'")
echo "  $GIT_VERSION"

# 检查MySQL
echo "检查MySQL..."
MYSQL_STATUS=$(ssh_exec "systemctl status mysql 2>&1 | head -1 || echo 'MySQL未运行'")
echo "  $MYSQL_STATUS"

# 检查Redis
echo "检查Redis..."
REDIS_STATUS=$(ssh_exec "systemctl status redis 2>&1 | head -1 || redis-cli ping 2>&1 || echo 'Redis未运行'")
echo "  $REDIS_STATUS"

echo ""
echo "2. 准备部署目录..."
ssh_exec "mkdir -p $PROJECT_DIR"
ssh_exec "cd $PROJECT_DIR && pwd"

echo ""
echo "3. 上传代码..."
# 检查是否已存在代码
if ssh_exec "test -d $PROJECT_DIR/bn_auto"; then
    echo "  代码目录已存在，备份旧版本..."
    ssh_exec "cd $PROJECT_DIR && mv bn_auto bn_auto.backup.\$(date +%Y%m%d_%H%M%S) 2>&1 || true"
fi

# 打包并上传代码
echo "  打包代码..."
cd /Users/forget/Desktop/projects/bn事件
tar -czf /tmp/bnsj.tar.gz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='*.pyc' --exclude='*.log' bn_auto/ 2>/dev/null || {
    echo "  打包失败，尝试直接上传目录..."
    scp_exec -r bn_auto root@$SERVER_IP:$PROJECT_DIR/
}

if [ -f /tmp/bnsj.tar.gz ]; then
    echo "  上传代码包..."
    scp_exec /tmp/bnsj.tar.gz root@$SERVER_IP:/tmp/
    ssh_exec "cd $PROJECT_DIR && tar -xzf /tmp/bnsj.tar.gz && rm /tmp/bnsj.tar.gz"
    rm /tmp/bnsj.tar.gz
    echo "  ✓ 代码上传完成"
fi

echo ""
echo "4. 安装Python依赖..."
ssh_exec "cd $PROJECT_DIR/bn_auto/server && pip3 install -r requirements.txt --quiet"

echo ""
echo "5. 检查并配置MySQL数据库..."
# 检查数据库是否存在
DB_EXISTS=$(ssh_exec "mysql -u root -e 'SHOW DATABASES LIKE \"bnsj\"' 2>&1 | grep -q bnsj && echo 'exists' || echo 'not_exists'")
if [ "$DB_EXISTS" = "not_exists" ]; then
    echo "  创建数据库..."
    ssh_exec "mysql -u root -e 'CREATE DATABASE IF NOT EXISTS bnsj CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;' 2>&1"
    echo "  导入数据库结构..."
    ssh_exec "cd $PROJECT_DIR/bn_auto/server && mysql -u root bnsj < migrations/init.sql 2>&1 || echo '数据库表可能已存在'"
else
    echo "  数据库已存在，跳过创建"
fi

echo ""
echo "6. 检查Redis服务..."
REDIS_RUNNING=$(ssh_exec "redis-cli ping 2>&1 | grep -q PONG && echo 'running' || echo 'not_running'")
if [ "$REDIS_RUNNING" = "not_running" ]; then
    echo "  警告: Redis未运行，请手动启动: systemctl start redis"
else
    echo "  ✓ Redis正在运行"
fi

echo ""
echo "7. 创建启动脚本..."
ssh_exec "cat > $PROJECT_DIR/start_server.sh << 'EOF'
#!/bin/bash
cd $PROJECT_DIR/bn_auto/server

# 设置环境变量
export MYSQL_DATABASE=bnsj
export MYSQL_PASSWORD=\"\"
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root

export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=\"\"
export REDIS_DB=0

export JWT_SECRET=bn-auto-secret-key-2024
export ADMIN_TOKEN=admin-secret-token

export HOST=0.0.0.0
export PORT=8000
export DEBUG=False

# 启动服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF
"
ssh_exec "chmod +x $PROJECT_DIR/start_server.sh"

echo ""
echo "8. 创建systemd服务文件..."
ssh_exec "cat > /etc/systemd/system/bnsj.service << 'EOF'
[Unit]
Description=BNSJ Trading System Server
After=network.target mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR/bn_auto/server
Environment=\"MYSQL_DATABASE=bnsj\"
Environment=\"MYSQL_PASSWORD=\"
Environment=\"MYSQL_HOST=localhost\"
Environment=\"MYSQL_PORT=3306\"
Environment=\"MYSQL_USER=root\"
Environment=\"REDIS_HOST=localhost\"
Environment=\"REDIS_PORT=6379\"
Environment=\"REDIS_PASSWORD=\"
Environment=\"REDIS_DB=0\"
Environment=\"JWT_SECRET=bn-auto-secret-key-2024\"
Environment=\"ADMIN_TOKEN=admin-secret-token\"
Environment=\"HOST=0.0.0.0\"
Environment=\"PORT=8000\"
Environment=\"DEBUG=False\"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
"

echo ""
echo "9. 重启服务..."
ssh_exec "systemctl daemon-reload"
ssh_exec "systemctl stop bnsj 2>&1 || true"
ssh_exec "systemctl enable bnsj"
ssh_exec "systemctl start bnsj"

echo ""
echo "10. 检查服务状态..."
sleep 3
SERVICE_STATUS=$(ssh_exec "systemctl status bnsj --no-pager | head -5")
echo "$SERVICE_STATUS"

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服务地址: http://$SERVER_IP:8000"
echo "管理后台: http://$SERVER_IP:8000/admin"
echo "API文档: http://$SERVER_IP:8000/docs"
echo ""
echo "服务管理命令:"
echo "  查看状态: ssh root@$SERVER_IP 'systemctl status bnsj'"
echo "  查看日志: ssh root@$SERVER_IP 'journalctl -u bnsj -f'"
echo "  重启服务: ssh root@$SERVER_IP 'systemctl restart bnsj'"
echo "  停止服务: ssh root@$SERVER_IP 'systemctl stop bnsj'"
echo ""

