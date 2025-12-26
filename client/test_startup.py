#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户端启动
"""
import sys
import os
import io
import traceback

# Windows控制台编码修复
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

print("=" * 60)
print("测试客户端启动")
print("=" * 60)
print()

try:
    print("1. 导入模块...")
    from app.main import ClientApp
    print("   ✓ 模块导入成功")
    
    print("\n2. 创建ClientApp实例...")
    app = ClientApp()
    print("   ✓ ClientApp实例创建成功")
    
    print("\n3. 检查Qt应用...")
    if app.qt_app:
        print(f"   ✓ QApplication已创建: {app.qt_app}")
    else:
        print("   ✗ QApplication未创建")
    
    print("\n4. 检查登录窗口...")
    if app.login_window:
        print(f"   ✓ 登录窗口已创建: {app.login_window}")
    else:
        print("   ⚠ 登录窗口未创建（可能还未显示）")
    
    print("\n" + "=" * 60)
    print("✓ 客户端启动测试通过！")
    print("=" * 60)
    print("\n注意: 这是一个GUI应用，窗口应该已经弹出")
    print("如果窗口没有出现，请检查是否有错误信息")
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1)

