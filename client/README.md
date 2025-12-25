# 客户端使用说明

## 安装依赖

```bash
pip install -r requirements.txt
```

## 安装 Playwright 浏览器驱动

```bash
playwright install chromium
playwright install-deps
```

## 配置

创建 `.env` 文件（可选）：
```
SERVER_URL=http://localhost:8000
DEFAULT_ORDER_AMOUNT=5.0
MIN_ORDER_AMOUNT=5.0
MAX_ORDER_AMOUNT=200.0
ORDER_PULL_INTERVAL=1
SESSION_EXPIRE_HOURS=24
```

## 启动客户端

```bash
python -m app.main
```

## 使用流程

1. **登录账号**：输入用户名和密码登录
2. **绑定币安账号**：点击"扫码登录币安"，使用币安App扫描二维码
3. **设置下单金额**：输入每次下单的金额（5-200 USDT）
4. **开始自动下单**：点击"开始自动下单"按钮
5. **查看日志**：在日志区域查看订单执行情况

## 注意事项

- 每次登录有效期为24小时，过期后需要重新登录
- 币安Token过期后需要重新扫码登录
- 订单金额范围：5-200 USDT
- 客户端每秒拉取一次订单

