#!/usr/bin/env python3
"""最简单的测试脚本"""
import sys
import os

# Patch platform BEFORE anything else
import platform
_original_mac_ver = platform.mac_ver
platform.mac_ver = lambda: ('26.0', '', 'arm64')

os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'

print("Testing simple GUI...")

try:
    import tkinter as tk
    print("✓ tkinter imported")
    
    root = tk.Tk()
    root.title("测试窗口")
    root.geometry("400x250")
    
    label = tk.Label(root, text="如果看到这个窗口，说明GUI正常")
    label.pack(pady=50)
    
    print("✓ Window created, showing for 5 seconds...")
    root.after(5000, root.destroy)
    root.mainloop()
    
    print("✓ Test completed")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    platform.mac_ver = _original_mac_ver

