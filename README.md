# 币安事件合约群控交易系统

## 项目简介

币安事件合约群控交易系统是一个分布式交易管理系统，分为后台管理系统和客户端程序两部分。系统允许管理员在后台配置交易订单，客户端自动拉取订单并执行交易。

## 项目结构

```
bn_auto/
├── server/          # 后台服务端
│   ├── app/        # 应用代码
│   ├── migrations/ # 数据库迁移脚本
│   └── requirements.txt
├── client/         # 客户端程序
│   ├── app/        # 应用代码
│   └── requirements.txt
└── doc/            # 项目文档
    ├── 产品文档.md
    └── 开发文档.md
```

## 快速开始

### 1. 服务端部署

```bash
cd server
pip install -r requirements.txt
mysql -u root -p < migrations/init.sql
python -m app.main
```

### 2. 客户端部署

```bash
cd client
pip install -r requirements.txt
playwright install chromium
python -m app.main
```

## 功能特性

### 服务端
- 订单管理（创建、分配、去重）
- 用户管理（注册、有效期管理）
- RESTful API接口
- Redis缓存和去重机制

### 客户端
- 用户登录（24小时有效期）
- 币安账号绑定（扫码登录）
- 自动订单拉取和执行
- 图形化界面（tkinter）
- 实时日志显示

## 详细文档

- [产品文档](doc/产品文档.md)
- [开发文档](doc/开发文档.md)
- [服务端README](server/README.md)
- [客户端README](client/README.md)

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy
- **数据库**: MySQL
- **缓存**: Redis
- **客户端GUI**: tkinter
- **浏览器自动化**: Playwright

## 注意事项

1. 本项目仅供学习交流使用，请勿用于非法用途
2. 使用前请确保已配置好MySQL和Redis
3. 币安账号登录需要网络连接
4. 订单执行有风险，请谨慎使用
