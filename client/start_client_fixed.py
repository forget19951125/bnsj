#!/usr/bin/env python3
"""
客户端启动脚本 - 修复Playwright版本检查问题
"""
import sys
import os

# 在导入任何模块之前，先设置环境变量
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'
os.environ['_PLAYWRIGHT_SKIP_VALIDATE'] = '1'

# Patch platform.mac_ver BEFORE importing platform
import platform
_original_mac_ver = platform.mac_ver

def patched_mac_ver():
    """返回假的macOS版本26.0"""
    return ('26.0', '', 'arm64')

# 替换platform.mac_ver
platform.mac_ver = patched_mac_ver

# 忽略警告
import warnings
warnings.filterwarnings('ignore')

def main():
    try:
        print("正在启动客户端...")
        from app.main import ClientApp
        
        app = ClientApp()
        print("客户端已初始化，显示登录窗口...")
        app.run()
    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
        sys.exit(0)
    except SystemExit as e:
        print(f"\nSystemExit: {e}")
        sys.exit(e.code if hasattr(e, 'code') else 0)
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 恢复原始函数
        platform.mac_ver = _original_mac_ver

if __name__ == "__main__":
    main()

