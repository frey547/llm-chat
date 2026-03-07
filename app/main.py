from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1 import router as api_v1_router
from app.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.services.cache_service import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )
    yield
    await close_redis()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI 聊天机器人",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 中间件注册（后注册先执行）
    app.add_middleware(RateLimitMiddleware)       # 第二层：限流
    app.add_middleware(RequestLoggingMiddleware)  # 第一层：日志
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix="/api/v1")

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        inprogress_labels=True,
    ).instrument(app).expose(app, include_in_schema=False)

    return app


app = create_app()
