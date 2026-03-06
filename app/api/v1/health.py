from fastapi import APIRouter
from app.schemas.common import HealthResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import check_db_connection
from app.services.cache_service import check_redis_connection

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse, summary="存活检查 liveness")
async def health_check():
    """进程存活就返回 200，不检查依赖"""
    logger.info("health_check called")
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get("/ready", summary="就绪检查 readiness")
async def readiness_check():
    """
    检查 DB + Redis 连通性。
    任意一个不通则返回 503，告知负载均衡器暂停分流。
    """
    db_ok = check_db_connection()
    redis_ok = await check_redis_connection()

    all_ready = db_ok and redis_ok
    status_code = 200 if all_ready else 503

    result = {
        "status": "ready" if all_ready else "not ready",
        "checks": {
            "database": "ok" if db_ok else "failed",
            "redis": "ok" if redis_ok else "failed",
        },
    }

    from fastapi.responses import JSONResponse
    return JSONResponse(content=result, status_code=status_code)
