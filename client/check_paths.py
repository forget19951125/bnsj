# -*- coding: utf-8 -*-
import os
import sys

# 设置UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("当前目录:", os.getcwd())
print("google_web存在:", os.path.exists('google_web'))
print("run_client.py存在:", os.path.exists('run_client.py'))

try:
    import PyQt5
    from PyQt5 import QtCore
    qt_dir = os.path.dirname(QtCore.__file__)
    print("\nQtCore路径:", QtCore.__file__)
    print("Qt目录:", qt_dir)
    
    plugins1 = os.path.join(qt_dir, 'Qt5', 'plugins')
    plugins2 = os.path.join(qt_dir, 'plugins')
    print("\nplugins路径1存在:", os.path.exists(plugins1))
    if os.path.exists(plugins1):
        print("  ", plugins1)
    print("plugins路径2存在:", os.path.exists(plugins2))
    if os.path.exists(plugins2):
        print("  ", plugins2)
        
    # 查找platforms目录
    for path in [plugins1, plugins2]:
        if os.path.exists(path):
            platforms = os.path.join(path, 'platforms')
            if os.path.exists(platforms):
                print("\n找到platforms目录:", platforms)
                qwindows = os.path.join(platforms, 'qwindows.dll')
                print("qwindows.dll存在:", os.path.exists(qwindows))
except Exception as e:
    print("错误:", e)
    import traceback
    traceback.print_exc()

