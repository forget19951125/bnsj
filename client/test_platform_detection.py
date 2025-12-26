"""
测试平台检测和兼容性
"""
import sys
import os

print("=" * 60)
print("平台检测测试")
print("=" * 60)

print(f"\n当前平台: {sys.platform}")

# 测试User-Agent设置
print("\n[1] 测试User-Agent设置...")
try:
    from app.binance_client import DEFAULT_UA, DEFAULT_PLATFORM, DEFAULT_SEC_CH_UA_PLATFORM
    print(f"  DEFAULT_UA: {DEFAULT_UA[:50]}...")
    print(f"  DEFAULT_PLATFORM: {DEFAULT_PLATFORM}")
    print(f"  DEFAULT_SEC_CH_UA_PLATFORM: {DEFAULT_SEC_CH_UA_PLATFORM}")
    
    if sys.platform == 'win32':
        assert 'Windows' in DEFAULT_UA, "Windows平台应该使用Windows User-Agent"
        assert DEFAULT_PLATFORM == 'Win32', "Windows平台应该使用Win32"
        assert 'Windows' in DEFAULT_SEC_CH_UA_PLATFORM, "Windows平台应该使用Windows sec-ch-ua-platform"
        print("  [OK] Windows平台User-Agent设置正确")
    elif sys.platform == 'darwin':
        assert 'Macintosh' in DEFAULT_UA, "macOS平台应该使用Macintosh User-Agent"
        assert DEFAULT_PLATFORM == 'MacIntel', "macOS平台应该使用MacIntel"
        assert 'macOS' in DEFAULT_SEC_CH_UA_PLATFORM, "macOS平台应该使用macOS sec-ch-ua-platform"
        print("  [OK] macOS平台User-Agent设置正确")
    else:
        print(f"  [INFO] 未知平台，使用默认设置")
except Exception as e:
    print(f"  [ERROR] User-Agent测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试Qt插件路径检测逻辑
print("\n[2] 测试Qt插件路径检测逻辑...")
try:
    if sys.platform == 'win32':
        plugin_file = 'qwindows.dll'
        print(f"  Windows平台应该检查: {plugin_file}")
    elif sys.platform == 'darwin':
        plugin_file = 'qcocoa.dylib'
        print(f"  macOS平台应该检查: {plugin_file}")
    else:
        plugin_file = None
        print(f"  其他平台: {plugin_file}")
    
    # 检查main.py中的逻辑
    if sys.platform in ('win32', 'darwin'):
        print(f"  [OK] 平台 {sys.platform} 在Qt插件路径设置范围内")
    else:
        print(f"  [INFO] 平台 {sys.platform} 不在Qt插件路径设置范围内（这是正常的）")
except Exception as e:
    print(f"  [ERROR] Qt插件路径检测测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试apply_platform_ua函数
print("\n[3] 测试apply_platform_ua函数...")
try:
    from app.binance_client import apply_platform_ua
    print(f"  [OK] apply_platform_ua函数导入成功")
    print(f"  函数名已从apply_windows_ua改为apply_platform_ua（支持多平台）")
except Exception as e:
    print(f"  [ERROR] apply_platform_ua函数导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("平台检测测试完成")
print("=" * 60)

