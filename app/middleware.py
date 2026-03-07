import time
import uuid
import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件，注入 request_id 并记录请求信息"""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        structlog.get_logger(__name__).info(
            "request_finished",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    滑动窗口限流中间件。
    只对需要登录的接口限流（带 Authorization header 的请求）。
    未登录请求直接放行（由接口本身的 JWT 校验处理）。
    """

    # 不限流的路径前缀
    EXEMPT_PATHS = {"/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # 豁免路径直接放行
        if any(request.url.path.startswith(p) for p in self.EXEMPT_PATHS):
            return await call_next(request)

        # 从 JWT 中取 user_id（不做完整验证，只取 sub 字段用于限流 key）
        user_id = self._extract_user_id(request)
        if user_id is None:
            return await call_next(request)

        # 限流检查
        from app.services.cache_service import is_rate_limited
        limited = await is_rate_limited(user_id)
        if limited:
            logger.warning("rate_limit_exceeded", user_id=user_id, path=request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "data": None,
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)

    @staticmethod
    def _extract_user_id(request: Request) -> int | None:
        """从 Authorization header 中提取 user_id，不做签名验证"""
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        try:
            from jose import jwt
            from app.core.config import settings
            token = auth.split(" ")[1]
            payload = jwt.decode(
                token, settings.secret_key, algorithms=["HS256"]
            )
            return int(payload.get("sub", 0)) or None
        except Exception:
            return None
