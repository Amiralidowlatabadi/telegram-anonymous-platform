from functools import lru_cache
from typing import List, Union
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    bot_token: str = Field(..., description="Telegram Bot API Token")
    bot_username: str = Field(..., description="Telegram Bot Username without @")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "anon_user"
    postgres_password: str = "UltraSecurePassword123!"
    postgres_db: str = "anon_platform_db"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "UltraSecureRedisPass123!"
    redis_db: int = 0

    admin_telegram_ids: Union[List[int], str] = Field(default_factory=list)
    default_rate_limit_per_minute: int = 15
    default_rate_limit_per_hour: int = 100
    max_message_length: int = 4096
    reply_target_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("admin_telegram_ids", mode="after")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            clean_val = v.strip()
            if not clean_val:
                return []
            if clean_val.startswith("[") and clean_val.endswith("]"):
                try:
                    return [int(x) for x in json.loads(clean_val)]
                except Exception:
                    pass
            return [int(x.strip()) for x in clean_val.split(",") if x.strip()]
        if isinstance(v, list):
            return [int(x) for x in v]
        return []

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

@lru_cache
def get_settings() -> Settings:
    return Settings()