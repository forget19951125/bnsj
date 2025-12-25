# 服务端使用说明

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置数据库

1. 创建MySQL数据库：
```bash
mysql -u root -p < migrations/init.sql
```

2. 配置环境变量（可选，创建 `.env` 文件）：
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=bn_auto

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

JWT_SECRET=your-secret-key
ADMIN_TOKEN=admin-secret-token
```

## 启动服务

```bash
python -m app.main
```

或者使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API文档

启动服务后，访问 `http://localhost:8000/docs` 查看API文档。

## 管理员接口使用

创建订单示例：
```bash
curl -X POST "http://localhost:8000/api/orders/create" \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "time_increments": "TEN_MINUTE",
    "symbol_name": "BTCUSDT",
    "direction": "LONG",
    "valid_duration": 3600
  }'
```

创建用户示例：
```bash
curl -X POST "http://localhost:8000/api/admin/users/create" \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "expire_at": "2024-12-31T23:59:59"
  }'
```

