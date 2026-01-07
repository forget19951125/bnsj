# 打包说明

## 前置要求

1. 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

2. 确保 `google_web` 目录存在且包含浏览器文件（chrome.exe等）

## 打包步骤

### 方法1：使用打包脚本（推荐）

```bash
cd client
python build_exe.py
```

打包脚本会自动：
- 检查依赖
- 清理之前的构建文件
- 执行打包
- 显示结果

### 方法2：直接使用PyInstaller

```bash
cd client
pyinstaller build_exe.spec --clean --noconfirm
```

## 打包输出

打包完成后，exe文件位于：
```
client/dist/BNSJ客户端.exe
```

## 注意事项

1. **浏览器文件**：打包后的exe需要 `google_web` 目录在同一目录下才能正常运行。如果打包时包含了浏览器文件，它们会被打包到exe中，但浏览器文件较大（约250MB），建议：
   - 将 `google_web` 目录放在exe同级目录
   - 或者修改代码，让程序自动下载浏览器

2. **首次运行**：首次运行exe可能需要一些时间解压文件

3. **调试模式**：如果遇到问题，可以修改 `build_exe.spec` 中的 `console=True` 来显示控制台窗口查看错误信息

4. **文件大小**：包含浏览器文件的exe会很大（可能超过300MB），这是正常的

## 分发建议

1. 创建一个发布目录，包含：
   - `BNSJ客户端.exe`
   - `google_web/` 目录（如果未打包进exe）
   - `README.txt` 使用说明

2. 或者创建一个安装程序，自动解压这些文件

