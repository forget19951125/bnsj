# 客户端使用说明

## 安装依赖

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装Qt环境（重要！）

客户端使用PyQt5作为GUI框架，需要确保Qt运行环境正确安装。

#### Windows系统

**方法1：使用自动安装脚本（推荐）**
```bash
# 双击运行或在命令行执行
install_qt_env.bat
```

**方法2：手动安装**
```bash
pip install PyQt5>=5.15.0
# 如果遇到问题，可以尝试安装额外的Qt5库
pip install PyQt5-Qt5
```

**验证安装**
```bash
python check_qt_env.py
```

#### Linux系统

**Ubuntu/Debian:**
```bash
# 使用自动安装脚本
bash install_qt_env.sh

# 或手动安装
sudo apt-get update
sudo apt-get install python3-pyqt5
pip install PyQt5>=5.15.0
```

**CentOS/RHEL:**
```bash
sudo yum install python3-qt5
pip install PyQt5>=5.15.0
```

#### macOS系统

```bash
# 使用自动安装脚本
bash install_qt_env.sh

# 或使用Homebrew
brew install pyqt5
pip install PyQt5>=5.15.0
```

**如果遇到Qt环境问题：**
1. 运行 `python check_qt_env.py` 诊断问题
2. 查看错误信息，按照提示解决
3. 确保Python版本 >= 3.7
4. 如果使用虚拟环境，确保已激活虚拟环境

### 3. 安装 Playwright 浏览器驱动

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

### 方法1：使用带环境检查的启动脚本（推荐）

```bash
# Windows
python start_with_check.py

# Linux/Mac
python3 start_with_check.py
```

这个脚本会在启动前自动检查Qt环境，如果环境有问题会给出提示。

### 方法2：直接启动

```bash
python -m app.main
# 或
python run_client.py
```

**注意**: 如果遇到Qt环境错误，请先运行 `python check_qt_env.py` 诊断问题。

## 使用流程

1. **登录账号**：输入用户名和密码登录
2. **绑定币安账号**：点击"扫码登录币安"，使用币安App扫描二维码
3. **设置下单金额**：输入每次下单的金额（5-200 USDT）
4. **开始自动下单**：点击"开始自动下单"按钮
5. **查看日志**：在日志区域查看订单执行情况

## 故障排除

### Qt环境问题

**问题1：提示"no Qt platform plugin could be initialized"（Qt平台插件无法初始化）**

这是Windows系统上常见的Qt平台插件初始化失败错误。

**快速解决方案：**
```bash
# Windows系统 - 使用修复脚本（推荐）
fix_qt_plugin.bat

# 或手动修复
pip install PyQt5-Qt5
python check_qt_env.py
```

**问题2：提示缺少Qt运行环境或无法启动GUI**

**解决方案：**

1. **检查Qt环境**
   ```bash
   python check_qt_env.py
   ```

2. **重新安装PyQt5**
   ```bash
   pip uninstall PyQt5 PyQt5-Qt5
   pip install PyQt5>=5.15.0
   pip install PyQt5-Qt5
   ```

3. **Windows系统额外步骤**
   - 确保已安装Visual C++ Redistributable
     - 下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - 尝试安装PyQt5-Qt5: `pip install PyQt5-Qt5`
   - 如果问题仍然存在，运行 `fix_qt_plugin.bat` 修复脚本

4. **Linux系统额外步骤**
   - 安装系统Qt库: `sudo apt-get install python3-pyqt5` (Ubuntu/Debian)
   - 或: `sudo yum install python3-qt5` (CentOS/RHEL)

5. **如果问题仍然存在**
   - 检查Python版本: `python --version` (需要 >= 3.7)
   - 检查pip版本: `pip --version`
   - 尝试使用虚拟环境重新安装
   - 查看详细文档: `QT_ENV_SETUP.md`

### 其他常见问题

- **无法连接到服务器**: 检查网络连接和服务器地址配置
- **Playwright错误**: 运行 `playwright install chromium` 重新安装浏览器驱动
- **登录失败**: 检查用户名密码是否正确，账号是否过期

## 注意事项

- 每次登录有效期为24小时，过期后需要重新登录
- 币安Token过期后需要重新扫码登录
- 订单金额范围：5-200 USDT
- 客户端每秒拉取一次订单
- **首次运行前必须正确安装Qt环境**

