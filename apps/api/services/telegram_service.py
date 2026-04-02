import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class TelegramServiceError(RuntimeError):
    def __init__(
        self,
        detail: str,
        *,
        user_message: str | None = None,
        code: str = "telegram_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.user_message = user_message or detail
        self.code = code
        self.status_code = status_code


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


def get_telegram_bot_username() -> str | None:
    username = get_settings().telegram_bot_username.strip().lstrip("@")
    return f"@{username}" if username else None


def validate_telegram_chat_id(value: str | int) -> str:
    if value is None:
        raise TelegramServiceError(
            "Telegram chat ID missing",
            user_message="Debes indicar un chat ID de Telegram.",
            code="telegram_chat_id_required",
            status_code=400,
        )

    normalized = str(value).strip()
    if not normalized:
        raise TelegramServiceError(
            "Telegram chat ID empty",
            user_message="Debes indicar un chat ID de Telegram.",
            code="telegram_chat_id_required",
            status_code=400,
        )

    signed_numeric = normalized[1:] if normalized.startswith("-") else normalized
    if not signed_numeric.isdigit():
        raise TelegramServiceError(
            f"Invalid telegram chat ID: {normalized}",
            user_message="El chat ID de Telegram no es válido. Usa un valor numérico como 123456789.",
            code="telegram_chat_id_invalid",
            status_code=400,
        )

    return normalized


def _normalize_telegram_failure(description: str | None, status_code: int) -> TelegramServiceError:
    detail = (description or "Telegram API error").strip()
    lowered = detail.lower()

    if "chat not found" in lowered or "bot was blocked" in lowered or "user is deactivated" in lowered:
        return TelegramServiceError(
            detail,
            user_message="Abre Telegram, busca el bot y pulsa Start antes de volver a intentarlo. Si ya lo hiciste, revisa el chat ID.",
            code="telegram_chat_not_ready",
            status_code=400,
        )

    if "chat_id is empty" in lowered or "chat_id is invalid" in lowered or "chat id is empty" in lowered:
        return TelegramServiceError(
            detail,
            user_message="El chat ID de Telegram no es válido. Revisa el valor y vuelve a intentarlo.",
            code="telegram_chat_id_invalid",
            status_code=400,
        )

    if status_code >= 500:
        return TelegramServiceError(
            detail,
            user_message="Telegram no respondió correctamente. Vuelve a intentarlo en unos minutos.",
            code="telegram_remote_error",
            status_code=502,
        )

    return TelegramServiceError(
        detail,
        user_message="No pudimos enviar el mensaje a Telegram. Revisa la configuración del bot y vuelve a intentarlo.",
        code="telegram_remote_error",
        status_code=400,
    )


def _telegram_send_url(token: str) -> str:
    return f"https://api.telegram.org/bot{token}/sendMessage"


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


def format_telegram_test_message(*, user_identifier: str, plan: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return "\n".join(
        [
            "✅ Crypto Intelligence",
            "",
            f"Tu conexion de Telegram ya responde para {user_identifier}.",
            f"Las alertas completas del plan {plan.upper()} llegaran a este chat cuando detectemos nuevas senales elegibles.",
            "",
            f"Comprobacion enviada: {timestamp}",
        ]
    )


def send_telegram_message(chat_id: str | int, text: str) -> dict[str, Any]:
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    normalized_chat_id = validate_telegram_chat_id(chat_id)

    if not token:
        logger.warning("Telegram alerts enabled but TELEGRAM_BOT_TOKEN is missing")
        raise TelegramServiceError(
            "Telegram bot token not configured",
            user_message="Telegram no está disponible temporalmente. Falta la configuración del bot.",
            code="telegram_unavailable",
            status_code=503,
        )

    try:
        response = httpx.post(
            _telegram_send_url(token),
            json={
                "chat_id": normalized_chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=10.0,
        )
    except httpx.TimeoutException as exc:
        raise TelegramServiceError(
            f"Telegram timeout: {exc}",
            user_message="Telegram tardó demasiado en responder. Vuelve a intentarlo.",
            code="telegram_timeout",
            status_code=504,
        ) from exc
    except httpx.HTTPError as exc:
        raise TelegramServiceError(
            f"Telegram HTTP error: {exc}",
            user_message="No pudimos contactar con Telegram. Vuelve a intentarlo en unos minutos.",
            code="telegram_network_error",
            status_code=502,
        ) from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400 or not payload.get("ok", True):
        description = payload.get("description") if isinstance(payload, dict) else response.text
        raise _normalize_telegram_failure(str(description), response.status_code)

    result = payload.get("result", {})
    return {
        "provider": "telegram",
        "message_id": str(result.get("message_id")) if result.get("message_id") is not None else None,
        "payload": payload,
    }


def send_telegram_test_message(chat_id: str | int, user_identifier: str, plan: str) -> dict[str, Any]:
    return send_telegram_message(
        chat_id,
        format_telegram_test_message(user_identifier=user_identifier, plan=plan),
    )


def get_telegram_connect_instructions() -> dict[str, Any]:
    bot_username = get_telegram_bot_username()
    bot_reference = bot_username or "el bot configurado para este entorno"

    return {
        "bot_username": bot_username,
        "start_command": "/start",
        "steps": [
            "1. Abre Telegram",
            f"2. Busca {bot_reference}",
            "3. Pulsa Start",
            "4. Copia tu chat ID y vuelve al dashboard para vincularlo",
        ],
        "note": "Después de vincular el chat puedes enviar una prueba manual antes de activar las alertas Telegram.",
    }
