# Nginx 反向代理部署说明（80 端口转发到 8000）

## 目标

- 访问：`http://104.194.155.10/api/webhook/tradingview`（80 端口，无 :8000）
- Nginx 将请求转发到本机 `http://127.0.0.1:8000`

## 一、服务器上安装 Nginx（未安装时）

```bash
# CentOS / RHEL
sudo yum install -y nginx

# Ubuntu / Debian
sudo apt update && sudo apt install -y nginx
```

## 二、上传并启用配置

**方式 A：用项目里的配置**

1. 将本机 `bn_auto/server/nginx-bnsj.conf` 上传到服务器：
   ```bash
   scp bn_auto/server/nginx-bnsj.conf root@104.194.155.10:/etc/nginx/conf.d/bnsj.conf
   ```
2. 若使用 `sites-available`（Ubuntu）：
   ```bash
   scp bn_auto/server/nginx-bnsj.conf root@104.194.155.10:/etc/nginx/sites-available/bnsj.conf
   ssh root@104.194.155.10 'ln -sf /etc/nginx/sites-available/bnsj.conf /etc/nginx/sites-enabled/'
   ```

**方式 B：在服务器上直接创建**

```bash
sudo tee /etc/nginx/conf.d/bnsj.conf << 'EOF'
server {
    listen 80;
    server_name 104.194.155.10;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF
```

## 三、检查并重载 Nginx

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 四、确认

- 确保后端已运行：`pm2 list` 中 bnsj-server 为 online。
- 测试：
  ```bash
  curl -X POST http://104.194.155.10/api/webhook/tradingview \
    -H "Content-Type: application/json" \
    -d '{"test":1}'
  ```
  应返回 `{"ok":true,"message":"received"}`。

## TradingView 中填写的 URL

```
http://104.194.155.10/api/webhook/tradingview
```

（80 端口可省略不写）

## 防火墙

若 80 未开放：

```bash
# firewalld
sudo firewall-cmd --permanent --add-service=http && sudo firewall-cmd --reload

# ufw (Ubuntu)
sudo ufw allow 80 && sudo ufw reload
```
