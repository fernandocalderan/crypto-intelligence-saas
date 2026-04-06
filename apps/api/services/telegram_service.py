import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from config import get_settings
from services.pro_signal_view import build_pro_signal_view

logger = logging.getLogger(__name__)
TELEGRAM_TIMEOUT_SECONDS = 10.0
TELEGRAM_MAX_ATTEMPTS = 2


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


def _state_emoji(execution_state: str, direction: str) -> str:
    if execution_state == "EXECUTABLE":
        return "🟢" if direction == "bullish" else "🔴"
    if execution_state == "WATCHLIST":
        return "🟡"
    if execution_state == "WAIT_CONFIRMATION":
        return "🟠"
    return "⛔"


def _severity_emoji(severity: str) -> str:
    if severity == "positive":
        return "✅"
    if severity == "negative":
        return "⛔"
    return "⚠"


def _format_plan_level(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/d"
    return _format_currency(numeric)


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


def _sanitize_telegram_text(value: str | None, *, max_chars: int = 240) -> str:
    normalized = (value or "").strip().replace("\n", " ")
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3]}..."


def _normalize_telegram_failure(description: str | None, status_code: int) -> TelegramServiceError:
    detail = (description or "Telegram API error").strip()
    lowered = detail.lower()

    if status_code == 401 or "unauthorized" in lowered:
        return TelegramServiceError(
            detail,
            user_message="El bot de Telegram no está autorizado en este entorno. Revisa TELEGRAM_BOT_TOKEN.",
            code="unauthorized_bot_token",
            status_code=503,
        )

    if "chat not found" in lowered or "bot was blocked" in lowered or "user is deactivated" in lowered:
        return TelegramServiceError(
            detail,
            user_message="Abre Telegram, busca el bot y pulsa Start antes de volver a intentarlo. Si ya lo hiciste, revisa el chat ID.",
            code="bot_not_started",
            status_code=400,
        )

    if "chat_id is empty" in lowered or "chat_id is invalid" in lowered or "chat id is empty" in lowered:
        return TelegramServiceError(
            detail,
            user_message="El chat ID de Telegram no es válido. Revisa el valor y vuelve a intentarlo.",
            code="invalid_chat_id",
            status_code=400,
        )

    if status_code >= 500:
        return TelegramServiceError(
            detail,
            user_message="Telegram no respondió correctamente. Vuelve a intentarlo en unos minutos.",
            code="telegram_http_error",
            status_code=502,
        )

    return TelegramServiceError(
        detail,
        user_message="No pudimos enviar el mensaje a Telegram. Revisa la configuración del bot y vuelve a intentarlo.",
        code="telegram_http_error",
        status_code=400,
    )


def _telegram_send_url(token: str) -> str:
    return f"https://api.telegram.org/bot{token}/sendMessage"


def format_pro_telegram_alert(signal_view: Any, plan: str = "pro") -> str:
    headline = str(_get_value(signal_view, "headline", "Signal"))
    execution_state = str(_get_value(signal_view, "execution_state", "WAIT_CONFIRMATION"))
    direction = str(_get_value(signal_view, "direction", "neutral"))
    summary = str(_get_value(signal_view, "summary", _get_value(signal_view, "thesis_short", "Sin resumen")))
    model_score = float(_get_value(signal_view, "model_score", _get_value(signal_view, "score", 0.0)))
    confidence_pct = float(_get_value(signal_view, "confidence_pct", _get_value(signal_view, "confidence", 0.0)))
    thesis_short = str(_get_value(signal_view, "thesis_short", _get_value(signal_view, "thesis", "Sin tesis disponible")))
    key_data = _get_value(signal_view, "key_data", {}) or {}
    confirmations = list(_get_value(signal_view, "confirmations", []))
    action_plan = _get_value(signal_view, "action_plan", {}) or {}
    data_quality_warnings = list(_get_value(signal_view, "data_quality_warnings", []))

    confirmation_lines = [
        f"{_severity_emoji(_get_value(item, 'severity', 'warning'))} {_get_value(item, 'label', '')}"
        for item in confirmations[:4]
    ] or ["⚠ Confirmaciones limitadas en este entorno"]

    warning_lines = [
        f"{_severity_emoji(_get_value(item, 'severity', 'warning'))} {_get_value(item, 'message', '')}"
        for item in data_quality_warnings[:3]
    ] or ["✅ Sin warnings críticos de calidad de dato en esta lectura"]

    plan_lines = [
        f"• Acción: {_get_value(action_plan, 'action_now', 'wait')}",
        f"• Bias: {_get_value(action_plan, 'bias', direction)}",
        f"• Trigger: {_format_plan_level(_get_value(action_plan, 'trigger_level'))}",
        f"• Invalidación: {_format_plan_level(_get_value(action_plan, 'invalidation_level'))}",
        f"• TP1 / TP2: {_format_plan_level(_get_value(action_plan, 'tp1'))} / {_format_plan_level(_get_value(action_plan, 'tp2'))}",
    ]

    return "\n".join(
        [
            f"{_state_emoji(execution_state, direction)} {headline}",
            f"{execution_state} · {direction.upper()} · {plan.upper()}",
            "",
            summary,
            "",
            f"Score: {model_score:.1f}/10",
            f"Confianza: {_confidence_label(confidence_pct)} ({confidence_pct:.1f}%)",
            f"Estado: {execution_state}",
            "",
            "Tesis:",
            thesis_short,
            "",
            "Datos clave:",
            f"• Precio: {_format_currency(_get_value(key_data, 'price'))}",
            f"• Cambio 24h: {_format_signed_percent(_get_value(key_data, 'change_24h'))}",
            f"• Volumen 24h: {_format_compact_number(_get_value(key_data, 'volume_24h'))}",
            f"• Funding: {_format_funding(_get_value(key_data, 'funding'))}",
            f"• OI: {_format_signed_percent(_get_value(key_data, 'oi_change_24h'))}",
            f"• Base: {_get_value(key_data, 'timeframe_base', 'n/d')} · {_get_value(key_data, 'source', 'n/d')}",
            "",
            "Confirmaciones:",
            *confirmation_lines,
            "",
            "Plan:",
            *plan_lines,
            "",
            "Riesgo / calidad del dato:",
            *warning_lines,
        ]
    )


def format_confluence_setup_alert(setup_view: Any, plan: str = "pro") -> str:
    headline = str(_get_value(setup_view, "headline", "Setup"))
    execution_state = str(_get_value(setup_view, "execution_state", "WAIT_CONFIRMATION"))
    direction = str(_get_value(setup_view, "direction", "neutral"))
    summary = str(_get_value(setup_view, "summary", _get_value(setup_view, "thesis_short", "Sin resumen")))
    score = float(_get_value(setup_view, "score", _get_value(setup_view, "model_score", 0.0)))
    confidence_pct = float(_get_value(setup_view, "confidence", _get_value(setup_view, "confidence_pct", 0.0)))
    thesis_short = str(_get_value(setup_view, "thesis_short", _get_value(setup_view, "thesis", "Sin tesis disponible")))
    signal_keys = [str(item) for item in list(_get_value(setup_view, "signal_keys", []))]
    key_data = _get_value(setup_view, "key_data", {}) or {}
    confirmations = list(_get_value(setup_view, "confirmations", []))
    action_plan = _get_value(setup_view, "action_plan", {}) or {}
    data_quality_warnings = list(_get_value(setup_view, "data_quality_warnings", []))

    confluence_line = " + ".join(signal_keys) if signal_keys else "n/d"
    confirmation_lines = [
        f"{_severity_emoji(_get_value(item, 'severity', 'warning'))} {_get_value(item, 'label', '')}"
        for item in confirmations[:4]
    ] or ["⚠ Confirmaciones limitadas en este entorno"]

    warning_lines = [
        f"{_severity_emoji(_get_value(item, 'severity', 'warning'))} {_get_value(item, 'message', '')}"
        for item in data_quality_warnings[:3]
    ] or ["✅ Sin warnings críticos de calidad de dato en esta lectura"]

    plan_lines = [
        f"• Acción: {_get_value(action_plan, 'action_now', 'wait')}",
        f"• Bias: {_get_value(action_plan, 'bias', direction)}",
        f"• Trigger: {_format_plan_level(_get_value(action_plan, 'trigger_level'))}",
        f"• Invalidación: {_format_plan_level(_get_value(action_plan, 'invalidation_level'))}",
        f"• TP1 / TP2: {_format_plan_level(_get_value(action_plan, 'tp1'))} / {_format_plan_level(_get_value(action_plan, 'tp2'))}",
    ]

    return "\n".join(
        [
            f"{_state_emoji(execution_state, direction)} {headline}",
            f"SETUP PRO · {execution_state} · {direction.upper()} · {plan.upper()}",
            "",
            summary,
            "",
            f"Confluencia: {confluence_line}",
            f"Score: {score:.1f}/10 | Confianza: {confidence_pct:.1f}%",
            "",
            "Tesis:",
            thesis_short,
            "",
            "Datos clave:",
            f"• Precio: {_format_currency(_get_value(key_data, 'price'))}",
            f"• Cambio 24h: {_format_signed_percent(_get_value(key_data, 'change_24h'))}",
            f"• Volumen 24h: {_format_compact_number(_get_value(key_data, 'volume_24h'))}",
            f"• Funding: {_format_funding(_get_value(key_data, 'funding'))}",
            f"• OI: {_format_signed_percent(_get_value(key_data, 'oi_change_24h'))}",
            f"• Base: {_get_value(key_data, 'timeframe_base', 'n/d')} · {_get_value(key_data, 'source', 'n/d')}",
            "",
            "Confirmaciones:",
            *confirmation_lines,
            "",
            "Plan:",
            *plan_lines,
            "",
            "Riesgo / calidad del dato:",
            *warning_lines,
        ]
    )


def format_early_signal_alert(signal: Any, asset: dict[str, Any] | None = None, plan: str = "pro") -> str:
    signal_view = build_pro_signal_view(signal, asset, plan=plan)
    headline = str(_get_value(signal_view, "headline", "Signal"))
    direction = str(_get_value(signal_view, "direction", "neutral"))
    summary = str(_get_value(signal_view, "summary", _get_value(signal_view, "thesis_short", "Sin resumen")))
    signal_type = str(_get_value(signal, "signal_type", _get_value(signal_view, "signal_type", "Signal")))
    model_score = float(_get_value(signal_view, "model_score", _get_value(signal_view, "score", 0.0)))
    confidence_pct = float(_get_value(signal_view, "confidence_pct", _get_value(signal_view, "confidence", 0.0)))
    thesis_short = str(_get_value(signal_view, "thesis_short", _get_value(signal_view, "thesis", "Sin tesis disponible")))
    key_data = _get_value(signal_view, "key_data", {}) or {}
    action_plan = _get_value(signal_view, "action_plan", {}) or {}
    data_quality_warnings = list(_get_value(signal_view, "data_quality_warnings", []))

    warning_lines = [
        f"{_severity_emoji(_get_value(item, 'severity', 'warning'))} {_get_value(item, 'message', '')}"
        for item in data_quality_warnings[:2]
    ] or ["⚠ Requiere confirmación adicional antes de ejecutar."]

    return "\n".join(
        [
            f"🟡 {headline}",
            f"SEÑAL TEMPRANA · {direction.upper()} · {plan.upper()}",
            "",
            f"{signal_type}: {summary}",
            "No es un setup de confluencia. Requiere confirmación adicional.",
            "",
            f"Score: {model_score:.1f}/10 | Confianza: {confidence_pct:.1f}%",
            "",
            "Tesis:",
            thesis_short,
            "",
            "Plan base:",
            f"• Bias: {_get_value(action_plan, 'bias', direction)}",
            f"• Trigger: {_format_plan_level(_get_value(action_plan, 'trigger_level'))}",
            f"• Invalidación: {_format_plan_level(_get_value(action_plan, 'invalidation_level'))}",
            "",
            "Datos clave:",
            f"• Precio: {_format_currency(_get_value(key_data, 'price'))}",
            f"• Cambio 24h: {_format_signed_percent(_get_value(key_data, 'change_24h'))}",
            f"• Volumen 24h: {_format_compact_number(_get_value(key_data, 'volume_24h'))}",
            "",
            "Warnings:",
            *warning_lines,
        ]
    )


def format_signal_alert_message(signal: Any, asset: dict[str, Any] | None = None, plan: str = "pro") -> str:
    return format_early_signal_alert(signal, asset, plan=plan)


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
    token_prefix = token[:6] if token else ""

    if not token:
        logger.warning("telegram_send_unavailable reason=missing_bot_token")
        raise TelegramServiceError(
            "Telegram bot token not configured",
            user_message="Telegram no está disponible temporalmente. Falta la configuración del bot.",
            code="telegram_unavailable",
            status_code=503,
        )

    url = _telegram_send_url(token)
    payload_body = {
        "chat_id": normalized_chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    last_error: TelegramServiceError | None = None
    for attempt in range(1, TELEGRAM_MAX_ATTEMPTS + 1):
        logger.info(
            "telegram_send_attempt chat_id=%s attempt=%s token_prefix=%s token_length=%s text_length=%s",
            normalized_chat_id,
            attempt,
            token_prefix,
            len(token),
            len(text),
        )
        try:
            response = httpx.post(
                url,
                json=payload_body,
                timeout=TELEGRAM_TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException as exc:
            logger.warning(
                "telegram_send_timeout chat_id=%s attempt=%s error=%s",
                normalized_chat_id,
                attempt,
                _sanitize_telegram_text(str(exc)),
            )
            last_error = TelegramServiceError(
                f"Telegram timeout: {exc}",
                user_message="Telegram tardó demasiado en responder. Vuelve a intentarlo.",
                code="timeout",
                status_code=504,
            )
            if attempt < TELEGRAM_MAX_ATTEMPTS:
                logger.info("telegram_send_retry chat_id=%s reason=timeout next_attempt=%s", normalized_chat_id, attempt + 1)
                continue
            raise last_error from exc
        except httpx.TransportError as exc:
            logger.warning(
                "telegram_send_transport_error chat_id=%s attempt=%s error=%s",
                normalized_chat_id,
                attempt,
                _sanitize_telegram_text(str(exc)),
            )
            last_error = TelegramServiceError(
                f"Telegram HTTP transport error: {exc}",
                user_message="No pudimos contactar con Telegram. Vuelve a intentarlo en unos minutos.",
                code="telegram_http_error",
                status_code=502,
            )
            if attempt < TELEGRAM_MAX_ATTEMPTS:
                logger.info(
                    "telegram_send_retry chat_id=%s reason=transport_error next_attempt=%s",
                    normalized_chat_id,
                    attempt + 1,
                )
                continue
            raise last_error from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        description = payload.get("description") if isinstance(payload, dict) else response.text
        logger.info(
            "telegram_send_response chat_id=%s attempt=%s status_code=%s ok=%s description=%s",
            normalized_chat_id,
            attempt,
            response.status_code,
            payload.get("ok", True) if isinstance(payload, dict) else response.status_code < 400,
            _sanitize_telegram_text(str(description)),
        )

        if response.status_code >= 400 or not payload.get("ok", True):
            error = _normalize_telegram_failure(str(description), response.status_code)
            logger.warning(
                "telegram_send_failed chat_id=%s attempt=%s code=%s status_code=%s detail=%s",
                normalized_chat_id,
                attempt,
                error.code,
                error.status_code,
                _sanitize_telegram_text(error.detail),
            )
            raise error

        result = payload.get("result", {})
        return {
            "provider": "telegram",
            "message_id": str(result.get("message_id")) if result.get("message_id") is not None else None,
            "payload": payload,
        }

    if last_error is not None:
        raise last_error

    raise TelegramServiceError(
        "Telegram send failed without classified error",
        user_message="No pudimos enviar el mensaje a Telegram.",
        code="telegram_http_error",
        status_code=502,
    )


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
