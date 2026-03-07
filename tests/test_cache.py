import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_set_and_get_context():
    """写入上下文后能正确读取"""
    from app.services.cache_service import set_context, get_context, delete_context

    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]
    await set_context(user_id=1, conversation_id=1, messages=messages)
    result = await get_context(user_id=1, conversation_id=1)
    assert result == messages
    await delete_context(user_id=1, conversation_id=1)


@pytest.mark.asyncio
async def test_context_trimmed_to_max():
    """超过最大条数时，只保留最近 N 条"""
    from app.services.cache_service import set_context, get_context, delete_context, CONTEXT_MAX_MESSAGES

    # 写入超过最大条数的消息
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    await set_context(user_id=1, conversation_id=2, messages=messages)
    result = await get_context(user_id=1, conversation_id=2)

    assert len(result) == CONTEXT_MAX_MESSAGES
    # 保留的是最新的那些
    assert result[-1]["content"] == "msg 19"
    await delete_context(user_id=1, conversation_id=2)


@pytest.mark.asyncio
async def test_append_context():
    """追加消息后上下文正确更新"""
    from app.services.cache_service import append_context, get_context, delete_context

    await append_context(1, 3, "user", "第一条消息")
    await append_context(1, 3, "assistant", "第一条回复")
    result = await get_context(1, 3)

    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"
    await delete_context(1, 3)


@pytest.mark.asyncio
async def test_rate_limit_allows_normal_requests():
    """正常请求不应被限流"""
    from app.services.cache_service import is_rate_limited, redis_client

    # 清理测试用的限流 key
    await redis_client.delete("ratelimit:999")
    result = await is_rate_limited(user_id=999)
    assert result is False


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive_requests():
    """超过限制后应被拦截"""
    from app.services.cache_service import is_rate_limited, redis_client
    from app.core.config import settings

    await redis_client.delete("ratelimit:888")
    # 连续发送超过限制的请求
    for _ in range(settings.rate_limit_per_minute):
        await is_rate_limited(user_id=888)

    # 第 limit+1 次应该被拒绝
    result = await is_rate_limited(user_id=888)
    assert result is True
    await redis_client.delete("ratelimit:888")
