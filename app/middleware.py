import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    每个请求自动注入 request_id，并在请求结束后输出结构化日志。
    request_id 会跟随整个请求链路出现在所有日志里（通过 structlog contextvars）。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        
        # 把 request_id 注入到当前请求的 structlog 上下文
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger = structlog.get_logger(__name__)
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "request_finished",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # 把 request_id 透传给客户端，方便排查问题
        response.headers["X-Request-ID"] = request_id
        return response
