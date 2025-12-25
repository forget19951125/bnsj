"""
Web3签名验证工具
"""
from eth_account.messages import encode_defunct
from eth_account import Account
from typing import Optional, Tuple
import time


def verify_signature(address: str, message: str, signature: str) -> bool:
    """
    验证以太坊签名
    
    Args:
        address: 以太坊地址
        message: 原始消息
        signature: 签名（hex字符串，0x开头）
    
    Returns:
        bool: 验证是否通过
    """
    try:
        address = address.lower()
        
        # 编码消息
        message_encoded = encode_defunct(text=message)
        
        # 恢复签名者地址
        signer_address = Account.recover_message(message_encoded, signature=signature)
        
        # 比较地址（不区分大小写）
        return signer_address.lower() == address.lower()
    except Exception as e:
        print(f"签名验证错误: {e}")
        return False


def generate_auth_message(address: str, timestamp: int) -> str:
    """
    生成认证消息
    
    Args:
        address: 以太坊地址
        timestamp: 时间戳
    
    Returns:
        str: 认证消息
    """
    return f"币安事件合约群控交易系统\n\n请签名以登录后台管理系统\n\n地址: {address}\n时间戳: {timestamp}"


def verify_auth_message(address: str, message: str, signature: str, timestamp: int, expire_seconds: int = 300) -> bool:
    """
    验证认证消息（包含时间戳验证）
    
    Args:
        address: 以太坊地址
        message: 消息
        signature: 签名
        timestamp: 时间戳
        expire_seconds: 过期时间（秒），默认5分钟
    
    Returns:
        bool: 验证是否通过
    """
    # 检查时间戳是否过期
    current_time = int(time.time())
    if abs(current_time - timestamp) > expire_seconds:
        return False
    
    # 验证签名
    return verify_signature(address, message, signature)

