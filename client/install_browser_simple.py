"""
最简单的浏览器安装脚本（直接输出到控制台）
"""
import sys
import os
import subprocess

# 设置控制台编码
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 代理设置
PROXY = "http://127.0.0.1:7890"

print("=" * 60)
print("Playwright浏览器安装工具")
print("=" * 60)
print(f"\n代理: {PROXY}")
print("\n开始安装...")
print("=" * 60)
sys.stdout.flush()

# 设置环境变量
env = os.environ.copy()
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY
env['https_proxy'] = PROXY

# 直接调用，输出到控制台
print("\n执行命令: python -m playwright install chromium\n")
sys.stdout.flush()

try:
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env,
        check=False  # 不抛出异常，手动检查返回码
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("[OK] 安装成功！")
    else:
        print(f"[ERROR] 安装失败，退出码: {result.returncode}")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

