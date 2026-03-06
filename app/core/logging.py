import logging
import sys
import structlog
from app.core.config import settings


def setup_logging() -> None:
    """
    配置 structlog，开发环境输出彩色人类可读格式，
    生产环境输出 JSON 格式供 Filebeat 采集。
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,        # 合并请求级上下文（request_id 等）
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
    ]

    if settings.is_production:
        # 生产：JSON 格式写文件，供 ELK 采集
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    else:
        # 开发：彩色终端输出
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    return structlog.get_logger(name)
