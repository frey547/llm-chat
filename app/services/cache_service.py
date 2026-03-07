import json
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)


async def check_redis_connection() -> bool:
    """检查 Redis 连通性"""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return False


async def close_redis():
    """优雅关闭 Redis 连接池"""
    await redis_client.aclose()


# 会话上下文缓存

CONTEXT_MAX_MESSAGES = 10   # 最多缓存最近 10 条消息
CONTEXT_TTL = 3600          # 缓存有效期 1 小时


def _context_key(user_id: int, conversation_id: int) -> str:
    return f"session:{user_id}:{conversation_id}"


async def get_context(user_id: int, conversation_id: int) -> list[dict]:
    """
    从 Redis 获取对话上下文。
    返回格式：[{"role": "user", "content": "..."}, ...]
    """
    key = _context_key(user_id, conversation_id)
    try:
        raw = await redis_client.get(key)
        if raw:
            logger.info("context_cache_hit", user_id=user_id, conversation_id=conversation_id)
            return json.loads(raw)
    except Exception as e:
        logger.error("context_cache_get_failed", error=str(e))
    return []


async def set_context(user_id: int, conversation_id: int, messages: list[dict]) -> None:
    """
    将对话上下文写入 Redis，只保留最近 N 条。
    """
    key = _context_key(user_id, conversation_id)
    # 只保留最近 CONTEXT_MAX_MESSAGES 条，避免 token 超限
    trimmed = messages[-CONTEXT_MAX_MESSAGES:]
    try:
        await redis_client.set(key, json.dumps(trimmed), ex=CONTEXT_TTL)
        logger.info(
            "context_cache_set",
            user_id=user_id,
            conversation_id=conversation_id,
            messages_count=len(trimmed),
        )
    except Exception as e:
        logger.error("context_cache_set_failed", error=str(e))


async def append_context(
    user_id: int,
    conversation_id: int,
    role: str,
    content: str,
) -> list[dict]:
    """
    追加一条消息到上下文缓存，返回最新的完整上下文。
    如果缓存不存在则创建。
    """
    messages = await get_context(user_id, conversation_id)
    messages.append({"role": role, "content": content})
    await set_context(user_id, conversation_id, messages)
    return messages


async def delete_context(user_id: int, conversation_id: int) -> None:
    """删除某个会话的上下文缓存（会话关闭时调用）"""
    key = _context_key(user_id, conversation_id)
    await redis_client.delete(key)


# 滑动窗口限流

RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

-- 清理窗口外的旧记录
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- 当前窗口内的请求数
local count = redis.call('ZCARD', key)

if count < limit then
    -- 未超限，记录本次请求
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
    return 0  -- 0 表示允许
else
    return 1  -- 1 表示拒绝
end
"""


async def is_rate_limited(user_id: int) -> bool:
    """
    滑动窗口限流检查。
    窗口：60秒，上限：settings.rate_limit_per_minute 次。
    返回 True 表示已超限需要拒绝，False 表示允许通过。
    """
    import time
    key = f"ratelimit:{user_id}"
    now = int(time.time() * 1000)   # 毫秒时间戳，精度更高
    window_ms = 60 * 1000           # 60 秒窗口
    limit = settings.rate_limit_per_minute

    try:
        result = await redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,          # key 的数量
            key,        # KEYS[1]
            now,        # ARGV[1]
            window_ms,  # ARGV[2]
            limit,      # ARGV[3]
        )
        return bool(result)
    except Exception as e:
        logger.error("rate_limit_check_failed", error=str(e))
        return False    # Redis 故障时放行，避免影响正常用户
