"""
Redis客户端
"""
import redis
from typing import Optional
from .config import settings

# 创建Redis连接
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password if settings.redis_password else None,
    db=settings.redis_db,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)


def get_redis() -> redis.Redis:
    """获取Redis客户端"""
    return redis_client


def check_redis_connection() -> bool:
    """检查Redis连接"""
    try:
        redis_client.ping()
        return True
    except Exception:
        return False

