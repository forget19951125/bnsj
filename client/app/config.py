"""
客户端配置
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """客户端配置"""
    
    # 服务器地址
    server_url: str = os.getenv("SERVER_URL", "http://104.194.155.10:8000")
    
    # 默认下单金额
    default_order_amount: float = float(os.getenv("DEFAULT_ORDER_AMOUNT", "5.0"))
    min_order_amount: float = float(os.getenv("MIN_ORDER_AMOUNT", "5.0"))
    max_order_amount: float = float(os.getenv("MAX_ORDER_AMOUNT", "200.0"))
    
    # 订单拉取间隔（秒）
    order_pull_interval: float = float(os.getenv("ORDER_PULL_INTERVAL", "0.1"))
    
    # 会话有效期（小时）
    session_expire_hours: int = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))
    
    # Token存储文件
    token_file: str = os.getenv("TOKEN_FILE", "token.json")
    binance_token_file: str = os.getenv("BINANCE_TOKEN_FILE", "binance_token.json")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()

