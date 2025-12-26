"""
最简单的测试脚本
"""
import sys
import os

print("测试1: 基本输出")
print("测试2: 中文输出")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")

# 测试代理设置
proxy = "http://127.0.0.1:7890"
print(f"\n代理设置: {proxy}")

# 设置环境变量
os.environ['HTTP_PROXY'] = proxy
os.environ['HTTPS_PROXY'] = proxy

print("\n环境变量已设置")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not set')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'Not set')}")

print("\n测试完成")
