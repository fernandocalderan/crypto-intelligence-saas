import logging
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)


def format_email_alert_message(signal: Any, asset: dict[str, Any] | None = None) -> str:
    asset_symbol = getattr(signal, "asset_symbol", None) or signal.get("asset_symbol", "UNKNOWN")
    signal_name = getattr(signal, "signal_type", None) or signal.get("signal_type", "Signal")
    thesis = getattr(signal, "thesis", None) or signal.get("thesis", "Sin tesis disponible")
    snapshot = asset or {}

    return "\n".join(
        [
            f"Alerta Crypto Intelligence: {asset_symbol} - {signal_name}",
            "",
            thesis,
            "",
            f"Precio: {snapshot.get('price_usd', 'n/d')}",
            f"Cambio 24h: {snapshot.get('change_24h', 'n/d')}",
            f"Funding: {snapshot.get('funding_rate', 'n/d')}",
            f"OI: {snapshot.get('oi_change_24h', 'n/d')}",
        ]
    )


def send_email_message(email: str, subject: str, body: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.enable_email_alerts:
        raise RuntimeError("Email alerts disabled by config")

    logger.warning("Email alert requested for %s but no provider is configured yet", email)
    raise RuntimeError("Email delivery provider not configured")
