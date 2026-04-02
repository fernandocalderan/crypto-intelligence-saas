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
    app_base_url: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/crypto_intelligence"
    redis_url: str = "redis://localhost:6379/0"
    binance_api_key: str = "your-binance-api-key"
    binance_api_secret: str = "your-binance-api-secret"
    bybit_api_key: str = "your-bybit-api-key"
    bybit_api_secret: str = "your-bybit-api-secret"
    auth_secret: str = "replace-with-a-long-random-secret"
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_publishable_key: str = "pk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_price_pro: str = "price_pro_placeholder"
    stripe_price_pro_plus: str = "price_pro_plus_placeholder"
    enable_stripe_mock_checkout: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    signal_engine_use_mock_data: bool = False
    market_data_symbols: str = "BTCUSDT,ETHUSDT,SOLUSDT,DOGEUSDT,XRPUSDT"
    market_data_schedule_minutes: int = 5
    market_data_use_mock_fallback: bool = True
    enable_market_data_scheduler: bool = True
    market_data_run_initial_sync: bool = True
    enable_binance_market_data: bool = True
    enable_bybit_market_data: bool = True
    enable_coinglass_market_data: bool = False
    coinglass_api_key: str = "your-coinglass-api-key"
    enable_volume_spike_signal: bool = True
    enable_range_breakout_signal: bool = True
    enable_funding_extreme_signal: bool = True
    enable_oi_divergence_signal: bool = True
    enable_liquidation_cluster_signal: bool = True
    enable_alerts: bool = True
    enable_telegram_alerts: bool = True
    enable_email_alerts: bool = False
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""
    alert_min_score: float = 7.0
    alert_min_confidence: float = 0.6
    alert_dedupe_window_minutes: int = 5
    alert_max_per_run: int = 50
    alerts_process_on_scheduler: bool = True
    enable_confluence_engine: bool = True
    alert_on_individual_signals: bool = False
    min_setup_score: float = 7.5
    min_setup_confidence: float = 70.0
    setup_require_no_mock_for_executable: bool = True

    model_config = SettingsConfigDict(
        env_file=str(resolve_env_file()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def parsed_market_data_symbols(self) -> list[str]:
        return [symbol.strip().upper() for symbol in self.market_data_symbols.split(",") if symbol.strip()]

    @property
    def signal_flags(self) -> dict[str, bool]:
        return {
            "volume_spike": self.enable_volume_spike_signal,
            "range_breakout": self.enable_range_breakout_signal,
            "funding_extreme": self.enable_funding_extreme_signal,
            "oi_divergence": self.enable_oi_divergence_signal,
            "liquidation_cluster": self.enable_liquidation_cluster_signal,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
