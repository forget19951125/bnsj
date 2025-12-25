#!/usr/bin/env python3
"""
客户端启动脚本
"""
import sys
import os
import traceback
import warnings

# 设置环境变量，尝试绕过Playwright的版本检查
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'

# 忽略警告
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
    except Exception as e:
        print(f"\n启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

