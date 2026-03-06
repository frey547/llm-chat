from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "llm-chat"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "1.0.0"
    secret_key: str = "change-me-in-production"

    # Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "llm_chat"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "123456"
    redis_db: int = 0

    # LLM
    llm_provider: str = "deepseek"
    deepseek_api_key: str = "sk-25046fee399c4b0ebeacf9510881d526"
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"

    # Rate Limit
    rate_limit_per_minute: int = 20

    # JWT
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    单例模式返回配置，lru_cache 保证全局只读取一次 .env
    """
    return Settings()


settings = get_settings()

