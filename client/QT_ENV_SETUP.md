# Qt环境安装指南

## 问题说明

客户端使用PyQt5作为GUI框架，需要Qt运行时库才能正常运行。如果遇到以下错误，说明Qt环境未正确安装：

- `缺少Qt运行环境`
- `无法导入PyQt5`
- `QApplication创建失败`
- `DLL加载失败` (Windows)

## 快速解决方案

### Windows系统

1. **使用自动安装脚本（最简单）**
   ```cmd
   install_qt_env.bat
   ```
   双击运行或在命令行执行，脚本会自动安装并验证Qt环境。

2. **手动安装**
   ```cmd
   pip install PyQt5>=5.15.0
   pip install PyQt5-Qt5
   ```

3. **验证安装**
   ```cmd
   python check_qt_env.py
   ```

### Linux系统

1. **Ubuntu/Debian**
   ```bash
   # 安装系统Qt库
   sudo apt-get update
   sudo apt-get install python3-pyqt5
   
   # 安装PyQt5 Python包
   pip3 install PyQt5>=5.15.0
   ```

2. **CentOS/RHEL**
   ```bash
   sudo yum install python3-qt5
   pip3 install PyQt5>=5.15.0
   ```

3. **使用自动安装脚本**
   ```bash
   bash install_qt_env.sh
   ```

### macOS系统

1. **使用Homebrew（推荐）**
   ```bash
   brew install pyqt5
   pip3 install PyQt5>=5.15.0
   ```

2. **使用自动安装脚本**
   ```bash
   bash install_qt_env.sh
   ```

## 详细诊断步骤

如果安装后仍然有问题，运行诊断脚本：

```bash
python check_qt_env.py
```

诊断脚本会检查：
1. PyQt5是否安装
2. Qt核心模块是否可用
3. 能否创建QApplication
4. Qt插件路径是否正确
5. Qt库文件是否存在

根据诊断结果，按照提示解决问题。

## 常见问题

### Q1: 提示"无法找到Qt5Core.dll" (Windows)

**原因**: Qt运行时库缺失或路径不正确

**解决方案**:
```cmd
pip uninstall PyQt5 PyQt5-Qt5
pip install PyQt5>=5.15.0
pip install PyQt5-Qt5
```

### Q2: 提示"ImportError: DLL load failed" (Windows)

**原因**: 缺少Visual C++运行库

**解决方案**:
1. 下载并安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. 重新安装PyQt5

### Q3: Linux系统提示"libQt5Core.so.5: cannot open shared object file"

**原因**: 系统Qt库未安装

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5 qtbase5-dev

# CentOS/RHEL
sudo yum install python3-qt5 qt5-qtbase-devel
```

### Q4: macOS提示"Library not loaded: @rpath/QtCore.framework"

**原因**: Qt框架路径不正确

**解决方案**:
```bash
brew uninstall pyqt5
brew install pyqt5
pip3 install --force-reinstall PyQt5>=5.15.0
```

### Q5: 虚拟环境中Qt无法工作

**原因**: 虚拟环境可能缺少系统依赖

**解决方案**:
1. 确保系统已安装Qt库（见上面Linux/macOS说明）
2. 在虚拟环境中重新安装PyQt5:
   ```bash
   pip install --force-reinstall PyQt5>=5.15.0
   ```

## 验证安装

安装完成后，运行以下命令验证：

```bash
python check_qt_env.py
```

如果看到所有检查项都显示 ✓，说明Qt环境已正确安装。

## 仍然无法解决？

如果按照以上步骤仍然无法解决问题，请：

1. 运行 `python check_qt_env.py` 获取详细诊断信息
2. 检查Python版本: `python --version` (需要 >= 3.7)
3. 检查pip版本: `pip --version`
4. 尝试在全新的虚拟环境中重新安装

## 相关文件

- `check_qt_env.py` - Qt环境诊断脚本
- `install_qt_env.bat` - Windows自动安装脚本
- `install_qt_env.sh` - Linux/Mac自动安装脚本
- `start_with_check.py` - 带环境检查的启动脚本

