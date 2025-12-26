"""
日志工具模块
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# 日志文件路径
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "client.log"

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)

class FileLogger:
    """文件日志记录器"""
    
    def __init__(self, log_file=None):
        self.log_file = log_file or LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message, level="INFO"):
        """记录日志"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] [{level}] {message}\n"
            
            # 写入文件
            with open(self.log_file, 'a', encoding='utf-8', errors='replace') as f:
                f.write(log_message)
                f.flush()
            
            # 同时输出到控制台（如果可用）
            try:
                print(log_message.strip())
            except:
                pass
        except Exception as e:
            # 如果日志写入失败，尝试输出到控制台
            try:
                print(f"[日志写入失败] {e}")
                print(f"[原始消息] {message}")
            except:
                pass
    
    def debug(self, message):
        """记录调试信息"""
        self.log(message, "DEBUG")
    
    def info(self, message):
        """记录信息"""
        self.log(message, "INFO")
    
    def warning(self, message):
        """记录警告"""
        self.log(message, "WARN")
    
    def error(self, message):
        """记录错误"""
        self.log(message, "ERROR")
    
    def exception(self, message):
        """记录异常"""
        import traceback
        self.error(f"{message}\n{traceback.format_exc()}")

# 全局日志实例
_logger = FileLogger()

def log(message, level="INFO"):
    """记录日志（便捷函数）"""
    _logger.log(message, level)

def debug(message):
    """记录调试信息"""
    _logger.debug(message)

def info(message):
    """记录信息"""
    _logger.info(message)

def warning(message):
    """记录警告"""
    _logger.warning(message)

def error(message):
    """记录错误"""
    _logger.error(message)

def exception(message):
    """记录异常"""
    _logger.exception(message)

def get_log_file():
    """获取日志文件路径"""
    return str(LOG_FILE)

