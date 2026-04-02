import logging
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_currency(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/d"
    return f"${numeric:,.2f}"


def _format_compact_number(value: Any) -> str:
    try:
        numeric = abs(float(value))
    except (TypeError, ValueError):
        return "n/d"

    for suffix, threshold in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if numeric >= threshold:
            return f"${numeric / threshold:.1f}{suffix}"
    return f"${numeric:,.0f}"


def _format_signed_percent(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/d"
    return f"{numeric:+.1f}%"


def _format_funding(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/d"
    return f"{numeric:+.4f}"


def _confidence_label(confidence: Any) -> str:
    try:
        numeric = float(confidence)
    except (TypeError, ValueError):
        return "media"
    if numeric >= 80:
        return "alta"
    if numeric >= 60:
        return "media"
    return "baja"


def _risk_context(signal: Any, snapshot: dict[str, Any] | None = None) -> str:
    source = str(_get_value(signal, "source", "runtime"))
    snapshot_source = str((snapshot or {}).get("source", ""))
    if "mock" in source or "mock" in snapshot_source:
        return "Parte del contexto puede venir de fallback mock. Valida ejecucion y liquidez antes de actuar."
    if float(_get_value(signal, "score", 0.0)) >= 8.5:
        return "Senal fuerte, pero sigue siendo tactica. No sustituye gestion de riesgo ni confirmacion propia."
    return "Conviccion media. Requiere validar estructura y timing antes de ejecutar."


def format_signal_alert_message(signal: Any, asset: dict[str, Any] | None = None) -> str:
    asset_symbol = str(_get_value(signal, "asset_symbol", "UNKNOWN"))
    signal_name = str(_get_value(signal, "signal_type", _get_value(signal, "signal_key", "Signal"))).replace("_", " ")
    score = float(_get_value(signal, "score", 0.0))
    confidence = float(_get_value(signal, "confidence", 0.0))
    direction = str(_get_value(signal, "direction", "neutral"))
    thesis = str(_get_value(signal, "thesis", "Sin tesis disponible"))
    snapshot = asset or {}

    return "\n".join(
        [
            f"🚨 {asset_symbol} — {signal_name}",
            "",
            f"Score: {score:.1f}/10",
            f"Confianza: {_confidence_label(confidence)} ({confidence:.1f}%)",
            "",
            f"Direccion: {direction}",
            "",
            "Tesis:",
            thesis,
            "",
            "Datos clave:",
            f"• Precio: {_format_currency(snapshot.get('price_usd'))}",
            f"• Cambio 24h: {_format_signed_percent(snapshot.get('change_24h'))}",
            f"• Volumen 24h: {_format_compact_number(snapshot.get('volume_24h'))}",
            f"• Funding: {_format_funding(snapshot.get('funding_rate'))}",
            f"• OI: {_format_signed_percent(snapshot.get('oi_change_24h'))}",
            "",
            "Riesgo:",
            _risk_context(signal, snapshot),
        ]
    )


def send_telegram_message(chat_id: str, text: str) -> dict[str, Any]:
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    if not token:
        logger.warning("Telegram alerts enabled but TELEGRAM_BOT_TOKEN is missing")
        raise RuntimeError("Telegram bot token not configured")

    response = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Telegram API error"))

    result = payload.get("result", {})
    return {
        "provider": "telegram",
        "message_id": str(result.get("message_id")) if result.get("message_id") is not None else None,
        "payload": payload,
    }
