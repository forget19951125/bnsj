"""
配置文件
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库配置
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "bnsj")
    
    # Redis配置
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # JWT配置
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-to-a-secure-random-string")
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    
    # 管理员Token（用于后台管理）
    admin_token: str = os.getenv("ADMIN_TOKEN", "admin-secret-token")
    
    # 服务配置
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Telegram 推送（可选，不配置则不发；PM2 需用 ecosystem.config.js 的 env 并 pm2 start 而非仅 restart 才注入）
    tg_bot_token: Optional[str] = os.getenv("TG_BOT_TOKEN", "")
    tg_chat_id: Optional[str] = os.getenv("TG_CHAT_ID", "")
    # TradingView 信号额外推送的群（多个群时用逗号分隔，如 "-5134594313,-123456"）
    tg_chat_id_webhook: Optional[str] = os.getenv("TG_CHAT_ID_WEBHOOK", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()

