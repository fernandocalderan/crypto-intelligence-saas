from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


CONFIG_PATH = Path(__file__).resolve()


def resolve_env_file() -> Path:
    candidates = [CONFIG_PATH.parent, *CONFIG_PATH.parents]
    for candidate in candidates:
        env_file = candidate / ".env"
        if env_file.exists():
            return env_file
    return CONFIG_PATH.parent / ".env"


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/crypto_intelligence"
    redis_url: str = "redis://localhost:6379/0"
    binance_api_key: str = "your-binance-api-key"
    binance_api_secret: str = "your-binance-api-secret"
    bybit_api_key: str = "your-bybit-api-key"
    bybit_api_secret: str = "your-bybit-api-secret"
    auth_secret: str = "replace-with-a-long-random-secret"
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_price_starter: str = "price_starter_placeholder"
    stripe_price_pro: str = "price_pro_placeholder"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=str(resolve_env_file()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
