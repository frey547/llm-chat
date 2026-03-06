import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 全局 Redis 客户端（异步）
redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def check_redis_connection() -> bool:
    """检查 Redis 连通性，供 /ready 接口使用"""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return False


async def close_redis():
    """应用关闭时释放 Redis 连接"""
    await redis_client.aclose()
