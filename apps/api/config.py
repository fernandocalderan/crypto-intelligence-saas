import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


CONFIG_PATH = Path(__file__).resolve()
logger = logging.getLogger(__name__)


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
    early_signal_min_score: float = 7.2
    early_signal_min_confidence: float = 0.65
    early_signal_max_per_run: int = 2
    early_signal_cooldown_hours: int = 8
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


def _redact_secret(secret: str) -> dict[str, object]:
    normalized = secret.strip()
    return {
        "present": bool(normalized),
        "prefix": normalized[:6] if normalized else "",
        "length": len(normalized),
    }


def build_alert_runtime_snapshot(settings: Settings | None = None) -> dict[str, object]:
    resolved = settings or get_settings()
    return {
        "enable_alerts": resolved.enable_alerts,
        "enable_telegram_alerts": resolved.enable_telegram_alerts,
        "enable_email_alerts": resolved.enable_email_alerts,
        "enable_market_data_scheduler": resolved.enable_market_data_scheduler,
        "alerts_process_on_scheduler": resolved.alerts_process_on_scheduler,
        "enable_confluence_engine": resolved.enable_confluence_engine,
        "alert_on_individual_signals": resolved.alert_on_individual_signals,
        "alert_min_score": resolved.alert_min_score,
        "alert_min_confidence": resolved.alert_min_confidence,
        "alert_dedupe_window_minutes": resolved.alert_dedupe_window_minutes,
        "alert_max_per_run": resolved.alert_max_per_run,
        "min_setup_score": resolved.min_setup_score,
        "min_setup_confidence": resolved.min_setup_confidence,
        "early_signal_min_score": resolved.early_signal_min_score,
        "early_signal_min_confidence": resolved.early_signal_min_confidence,
        "early_signal_max_per_run": resolved.early_signal_max_per_run,
        "early_signal_cooldown_hours": resolved.early_signal_cooldown_hours,
        "telegram_bot_token": _redact_secret(resolved.telegram_bot_token),
    }


def validate_alert_runtime_configuration(settings: Settings | None = None) -> list[str]:
    resolved = settings or get_settings()
    issues: list[str] = []

    if resolved.enable_alerts and resolved.enable_telegram_alerts and not resolved.telegram_bot_token.strip():
        issues.append("telegram_enabled_without_token")

    if resolved.alerts_process_on_scheduler and not resolved.enable_market_data_scheduler:
        issues.append("alerts_on_scheduler_without_market_scheduler")

    if resolved.alerts_process_on_scheduler and not resolved.enable_alerts:
        issues.append("alerts_process_on_scheduler_but_alerts_disabled")

    if resolved.enable_telegram_alerts and not resolved.enable_alerts:
        issues.append("telegram_channel_enabled_but_alerts_disabled")

    if resolved.enable_email_alerts and not resolved.enable_alerts:
        issues.append("email_channel_enabled_but_alerts_disabled")

    if resolved.alert_dedupe_window_minutes <= 0:
        issues.append("invalid_alert_dedupe_window")

    if resolved.alert_max_per_run <= 0:
        issues.append("invalid_alert_max_per_run")

    if resolved.early_signal_max_per_run <= 0:
        issues.append("invalid_early_signal_max_per_run")

    if resolved.early_signal_cooldown_hours < 0:
        issues.append("invalid_early_signal_cooldown_hours")

    return issues


def log_alert_runtime_configuration(settings: Settings | None = None) -> None:
    resolved = settings or get_settings()
    snapshot = build_alert_runtime_snapshot(resolved)
    issues = validate_alert_runtime_configuration(resolved)
    logger.info("alert_runtime_configuration %s", snapshot)

    if not issues:
        logger.info("alert_runtime_configuration_valid")
        return

    for issue in issues:
        logger.warning("alert_runtime_configuration_invalid reason=%s", issue)


@lru_cache
def get_settings() -> Settings:
    return Settings()
