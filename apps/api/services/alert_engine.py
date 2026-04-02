import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from config import get_settings
from db.session import SessionLocal
from db.models import AlertDeliveryRecord, AlertSubscriptionRecord, SignalRecord, UserRecord
from models.schemas import AlertsMeResponse, TelegramConnectInstructionsResponse, TelegramTestResponse
from services.confluence_engine import compute_confluence_setup_payloads
from services.email_alert_service import format_email_alert_message, send_email_message
from services.plans import can_receive_alerts, normalize_plan
from services.setup_view import build_setup_views
from services.telegram_service import (
    TelegramServiceError,
    format_confluence_setup_alert,
    format_signal_alert_message,
    get_telegram_connect_instructions,
    send_telegram_message,
    send_telegram_test_message,
    validate_telegram_chat_id,
)

logger = logging.getLogger(__name__)

CHANNEL_TELEGRAM = "telegram"
CHANNEL_EMAIL = "email"
DELIVERY_PENDING = "pending"
DELIVERY_SENT = "sent"
DELIVERY_FAILED = "failed"


def _coerce_threshold_confidence(value: float | None) -> float:
    resolved = get_settings().alert_min_confidence if value is None else float(value)
    return resolved * 100.0 if resolved <= 1.0 else resolved


def signal_passes_thresholds(
    *,
    score: float,
    confidence: float,
    min_score: float,
    min_confidence: float,
) -> bool:
    return float(score) >= float(min_score) and float(confidence) >= _coerce_threshold_confidence(min_confidence)


def setup_passes_thresholds(
    *,
    score: float,
    confidence: float,
    min_score: float,
    min_confidence: float,
) -> bool:
    return float(score) >= float(min_score) and float(confidence) >= _coerce_threshold_confidence(min_confidence)


def _snapshot_index(market_snapshots: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {
        str(snapshot["symbol"]).upper(): snapshot
        for snapshot in (market_snapshots or [])
    }


def _delivery_ready_for_subscription(subscription: AlertSubscriptionRecord) -> bool:
    if subscription.channel == CHANNEL_TELEGRAM:
        return bool(subscription.telegram_chat_id)
    if subscription.channel == CHANNEL_EMAIL:
        return bool(subscription.email)
    return False


def _setup_trigger_is_usable(setup_view: Any) -> bool:
    action_plan = _get_value(setup_view, "action_plan", {}) or {}
    trigger_level = _get_value(action_plan, "trigger_level")
    invalidation_level = _get_value(action_plan, "invalidation_level")
    return trigger_level is not None and invalidation_level is not None


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _telegram_system_ready() -> bool:
    settings = get_settings()
    return settings.enable_alerts and settings.enable_telegram_alerts and bool(settings.telegram_bot_token.strip())


def _email_system_ready() -> bool:
    settings = get_settings()
    return settings.enable_alerts and settings.enable_email_alerts


def _build_settings_response(user: UserRecord, subscriptions: list[AlertSubscriptionRecord]) -> AlertsMeResponse:
    settings = get_settings()
    by_channel = {subscription.channel: subscription for subscription in subscriptions}
    telegram = by_channel.get(CHANNEL_TELEGRAM)
    email = by_channel.get(CHANNEL_EMAIL)

    threshold_owner = telegram or email
    min_score = threshold_owner.min_score if threshold_owner and threshold_owner.min_score is not None else settings.alert_min_score
    min_confidence = (
        threshold_owner.min_confidence
        if threshold_owner and threshold_owner.min_confidence is not None
        else settings.alert_min_confidence
    )
    normalized_plan = normalize_plan(user.plan)

    return AlertsMeResponse(
        plan=normalized_plan,
        can_receive_alerts=can_receive_alerts(normalized_plan),
        alerts_globally_enabled=settings.enable_alerts,
        telegram_available=_telegram_system_ready(),
        email_available=_email_system_ready(),
        telegram_enabled=bool(telegram and telegram.is_active),
        email_enabled=bool(email and email.is_active),
        telegram_chat_id=telegram.telegram_chat_id if telegram else None,
        telegram_configured=bool(telegram and telegram.telegram_chat_id),
        email=email.email if email else None,
        email_configured=bool(email and email.email),
        min_score=float(min_score),
        min_confidence=float(min_confidence),
    )


def _require_alerts_plan(user: UserRecord, *, action_label: str) -> str:
    normalized_plan = normalize_plan(user.plan)
    if not can_receive_alerts(normalized_plan):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"El plan {normalized_plan} no puede {action_label}. Actualiza a Pro o Pro+.",
        )
    return normalized_plan


def _load_user_with_alerts(db: Session, user_id: int) -> UserRecord:
    user = db.scalar(
        select(UserRecord)
        .options(selectinload(UserRecord.alert_subscriptions))
        .where(UserRecord.id == user_id)
    )
    if user is None:
        raise ValueError("User not found")
    return user


def _get_or_create_subscription(
    db: Session,
    *,
    user: UserRecord,
    channel: str,
) -> AlertSubscriptionRecord:
    existing = next((item for item in user.alert_subscriptions if item.channel == channel), None)
    if existing is not None:
        return existing

    subscription = AlertSubscriptionRecord(
        user_id=user.id,
        channel=channel,
        is_active=False,
        email=user.email if channel == CHANNEL_EMAIL else None,
    )
    subscription.user = user
    db.add(subscription)
    db.flush()
    return subscription


def get_alert_settings_for_user(user: UserRecord) -> AlertsMeResponse:
    with SessionLocal() as db:
        persistent_user = _load_user_with_alerts(db, user.id)
        return _build_settings_response(persistent_user, persistent_user.alert_subscriptions)


def get_telegram_connect_instructions_for_user(user: UserRecord) -> TelegramConnectInstructionsResponse:
    return TelegramConnectInstructionsResponse(**get_telegram_connect_instructions())


def upsert_telegram_subscription(
    user: UserRecord,
    *,
    telegram_chat_id: str | int,
    is_active: bool | None = True,
) -> AlertsMeResponse:
    with SessionLocal() as db:
        persistent_user = _load_user_with_alerts(db, user.id)
        _require_alerts_plan(persistent_user, action_label="conectar Telegram")
        subscription = _get_or_create_subscription(db, user=persistent_user, channel=CHANNEL_TELEGRAM)
        subscription.telegram_chat_id = validate_telegram_chat_id(telegram_chat_id)
        if is_active is not None:
            subscription.is_active = bool(is_active)
        if subscription.min_score is None:
            subscription.min_score = get_settings().alert_min_score
        if subscription.min_confidence is None:
            subscription.min_confidence = get_settings().alert_min_confidence
        db.commit()
        db.refresh(subscription)
        return _build_settings_response(persistent_user, persistent_user.alert_subscriptions)


def update_user_alert_preferences(
    user: UserRecord,
    *,
    min_score: float | None = None,
    min_confidence: float | None = None,
    telegram_enabled: bool | None = None,
    email_enabled: bool | None = None,
) -> AlertsMeResponse:
    with SessionLocal() as db:
        persistent_user = _load_user_with_alerts(db, user.id)
        if any(value is not None for value in (min_score, min_confidence, telegram_enabled, email_enabled)):
            _require_alerts_plan(persistent_user, action_label="editar alertas push")
        telegram_subscription = _get_or_create_subscription(db, user=persistent_user, channel=CHANNEL_TELEGRAM)
        email_subscription = _get_or_create_subscription(db, user=persistent_user, channel=CHANNEL_EMAIL)

        if min_score is not None:
            resolved_min_score = max(float(min_score), 0.0)
            telegram_subscription.min_score = resolved_min_score
            email_subscription.min_score = resolved_min_score
        if min_confidence is not None:
            resolved_min_confidence = max(float(min_confidence), 0.0)
            telegram_subscription.min_confidence = resolved_min_confidence
            email_subscription.min_confidence = resolved_min_confidence
        if telegram_enabled is not None:
            telegram_subscription.is_active = bool(telegram_enabled)
        if email_enabled is not None:
            email_subscription.is_active = bool(email_enabled)

        if not email_subscription.email:
            email_subscription.email = persistent_user.email

        db.commit()
        db.refresh(telegram_subscription)
        db.refresh(email_subscription)
        return _build_settings_response(persistent_user, persistent_user.alert_subscriptions)


def send_telegram_test_for_user(user: UserRecord) -> TelegramTestResponse:
    settings = get_settings()
    if not settings.enable_alerts or not settings.enable_telegram_alerts:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram no está disponible temporalmente en este entorno.",
        )

    with SessionLocal() as db:
        persistent_user = _load_user_with_alerts(db, user.id)
        normalized_plan = _require_alerts_plan(persistent_user, action_label="enviar una prueba de Telegram")
        subscription = next(
            (item for item in persistent_user.alert_subscriptions if item.channel == CHANNEL_TELEGRAM),
            None,
        )

        if subscription is None or not subscription.telegram_chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conecta Telegram antes de enviar una prueba.",
            )

        logger.info(
            "Telegram manual test requested user_id=%s plan=%s telegram_enabled=%s",
            persistent_user.id,
            normalized_plan,
            bool(subscription.is_active),
        )

        try:
            payload = send_telegram_test_message(
                subscription.telegram_chat_id,
                persistent_user.email,
                normalized_plan,
            )
        except TelegramServiceError as exc:
            logger.warning(
                "Telegram manual test failed user_id=%s error=%s code=%s",
                persistent_user.id,
                exc.detail,
                exc.code,
            )
            raise HTTPException(status_code=exc.status_code, detail=exc.user_message) from exc

        logger.info(
            "Telegram manual test sent user_id=%s provider_message_id=%s",
            persistent_user.id,
            payload.get("message_id"),
        )
        return TelegramTestResponse(
            detail="Mensaje de prueba enviado",
            telegram_chat_id=subscription.telegram_chat_id,
            telegram_enabled=bool(subscription.is_active),
            provider_message_id=payload.get("message_id"),
        )


def get_eligible_users_for_alerts(db: Session) -> list[UserRecord]:
    users = db.scalars(
        select(UserRecord)
        .options(selectinload(UserRecord.alert_subscriptions))
        .where(
            UserRecord.is_active.is_(True),
            UserRecord.plan.in_(["pro", "pro_plus"]),
        )
    ).all()
    logger.info("Alert engine found %s pro users eligible for push processing", len(users))
    return users


def get_eligible_signals_for_user(
    subscription: AlertSubscriptionRecord,
    signals: list[SignalRecord],
) -> list[SignalRecord]:
    settings = get_settings()
    min_score = subscription.min_score if subscription.min_score is not None else settings.alert_min_score
    min_confidence = (
        subscription.min_confidence
        if subscription.min_confidence is not None
        else settings.alert_min_confidence
    )

    eligible_signals = [
        signal
        for signal in signals
        if signal_passes_thresholds(
            score=signal.score,
            confidence=signal.confidence,
            min_score=float(min_score),
            min_confidence=float(min_confidence),
        )
    ]
    return eligible_signals


def _resolve_setup_thresholds(subscription: AlertSubscriptionRecord) -> tuple[float, float]:
    settings = get_settings()
    subscription_min_score = (
        float(subscription.min_score) if subscription.min_score is not None else float(settings.alert_min_score)
    )
    subscription_min_confidence = (
        _coerce_threshold_confidence(float(subscription.min_confidence))
        if subscription.min_confidence is not None
        else _coerce_threshold_confidence(settings.alert_min_confidence)
    )
    return (
        max(float(settings.min_setup_score), subscription_min_score),
        max(float(settings.min_setup_confidence), subscription_min_confidence),
    )


def get_eligible_setups_for_user(
    subscription: AlertSubscriptionRecord,
    setup_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    min_score, min_confidence = _resolve_setup_thresholds(subscription)
    eligible: list[dict[str, Any]] = []

    for candidate in setup_candidates:
        setup_view = candidate["setup_view"]
        if _get_value(setup_view, "execution_state") not in {"EXECUTABLE", "WATCHLIST"}:
            logger.info(
                "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=execution_state state=%s",
                subscription.user_id,
                subscription.channel,
                _get_value(setup_view, "setup_key"),
                _get_value(setup_view, "execution_state"),
            )
            continue
        if bool(_get_value(setup_view, "is_mock_contaminated")):
            logger.info(
                "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=mock_contamination",
                subscription.user_id,
                subscription.channel,
                _get_value(setup_view, "setup_key"),
            )
            continue
        if not _setup_trigger_is_usable(setup_view):
            logger.info(
                "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=missing_levels",
                subscription.user_id,
                subscription.channel,
                _get_value(setup_view, "setup_key"),
            )
            continue
        if not setup_passes_thresholds(
            score=float(_get_value(setup_view, "score", 0.0)),
            confidence=float(_get_value(setup_view, "confidence", 0.0)),
            min_score=min_score,
            min_confidence=min_confidence,
        ):
            logger.info(
                "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=thresholds score=%s confidence=%s min_score=%s min_confidence=%s",
                subscription.user_id,
                subscription.channel,
                _get_value(setup_view, "setup_key"),
                _get_value(setup_view, "score"),
                _get_value(setup_view, "confidence"),
                min_score,
                min_confidence,
            )
            continue
        eligible.append(candidate)

    return eligible


SETUP_ANCHOR_PRIORITY: dict[str, list[str]] = {
    "trend_continuation": ["range_breakout", "volume_spike"],
    "squeeze_reversal": ["liquidation_cluster", "funding_extreme"],
    "positioning_trap": ["oi_divergence", "funding_extreme", "range_breakout"],
}


def _select_setup_anchor_signal(
    setup_payload: dict[str, Any],
    new_signals: list[SignalRecord],
) -> SignalRecord | None:
    by_hash = {signal.signal_hash: signal for signal in new_signals}
    component_signals = list(_get_value(setup_payload, "signals", []))
    preferred_keys = SETUP_ANCHOR_PRIORITY.get(str(_get_value(setup_payload, "setup_key", "")), [])

    for preferred_key in preferred_keys:
        for component in component_signals:
            if str(_get_value(component, "signal_key", "")) != preferred_key:
                continue
            signal_hash = str(_get_value(component, "signal_hash", ""))
            if signal_hash in by_hash:
                return by_hash[signal_hash]

    for component in component_signals:
        signal_hash = str(_get_value(component, "signal_hash", ""))
        if signal_hash in by_hash:
            return by_hash[signal_hash]

    return None


def _build_setup_candidates(
    *,
    new_signals: list[SignalRecord],
    detected_signals: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    resolved_detected_signals = detected_signals or [
        {
            "id": signal.public_id or signal.signal_hash,
            "signal_key": signal.signal_key,
            "asset_symbol": signal.asset_symbol,
            "signal_type": signal.signal_type,
            "timeframe": signal.timeframe,
            "direction": signal.direction or "neutral",
            "score": signal.score,
            "confidence": signal.confidence,
            "thesis": signal.thesis,
            "evidence": list(signal.evidence_json or []),
            "source": signal.source,
            "generated_at": signal.created_at,
            "signal_hash": signal.signal_hash,
            "source_snapshot_time": signal.source_snapshot_time,
        }
        for signal in new_signals
    ]
    if not resolved_detected_signals:
        return []

    setup_payloads = compute_confluence_setup_payloads(
        signal_payloads=resolved_detected_signals,
        market_snapshots=market_snapshots,
    )
    if not setup_payloads:
        return []

    setup_views = build_setup_views(setup_payloads, market_snapshots, plan="pro")
    candidates: list[dict[str, Any]] = []
    for setup_payload, setup_view in zip(setup_payloads, setup_views, strict=False):
        anchor_signal = _select_setup_anchor_signal(setup_payload, new_signals)
        if anchor_signal is None:
            logger.info(
                "Confluence setup skipped setup_key=%s asset=%s reason=no_new_anchor_signal",
                _get_value(setup_payload, "setup_key"),
                _get_value(setup_payload, "asset_symbol"),
            )
            continue
        logger.info(
            "Confluence setup generated setup_key=%s asset=%s score=%s confidence=%s anchor_signal_id=%s",
            _get_value(setup_payload, "setup_key"),
            _get_value(setup_payload, "asset_symbol"),
            _get_value(setup_view, "score"),
            _get_value(setup_view, "confidence"),
            anchor_signal.id,
        )
        candidates.append(
            {
                "setup_payload": setup_payload,
                "setup_view": setup_view,
                "anchor_signal": anchor_signal,
            }
        )

    candidates.sort(
        key=lambda candidate: (
            float(_get_value(candidate["setup_view"], "score", 0.0)),
            float(_get_value(candidate["setup_view"], "confidence", 0.0)),
        ),
        reverse=True,
    )
    return candidates


def create_pending_delivery(
    db: Session,
    *,
    signal: SignalRecord,
    user: UserRecord,
    channel: str,
) -> AlertDeliveryRecord | None:
    existing = db.scalar(
        select(AlertDeliveryRecord).where(
            AlertDeliveryRecord.signal_id == signal.id,
            AlertDeliveryRecord.user_id == user.id,
            AlertDeliveryRecord.channel == channel,
        )
    )
    if existing is not None:
        return None

    delivery = AlertDeliveryRecord(
        signal_id=signal.id,
        user_id=user.id,
        channel=channel,
        delivery_status=DELIVERY_PENDING,
    )
    db.add(delivery)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(delivery)
    return delivery


def _mark_delivery_sent(db: Session, delivery: AlertDeliveryRecord, provider_message_id: str | None) -> None:
    delivery.delivery_status = DELIVERY_SENT
    delivery.provider_message_id = provider_message_id
    delivery.sent_at = datetime.now(timezone.utc)
    db.commit()


def _mark_delivery_failed(db: Session, delivery: AlertDeliveryRecord, error_message: str) -> None:
    delivery.delivery_status = DELIVERY_FAILED
    delivery.error_message = error_message[:2000]
    db.commit()


def dispatch_new_signals(
    db: Session,
    signals: list[SignalRecord],
    *,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    settings = get_settings()
    if not settings.enable_alerts:
        logger.info("Alert dispatch skipped because ENABLE_ALERTS=false")
        return {"sent": 0, "failed": 0, "skipped": len(signals)}

    if not signals:
        return {"sent": 0, "failed": 0, "skipped": 0}

    limited_signals = signals[: settings.alert_max_per_run]
    if len(signals) > len(limited_signals):
        logger.info(
            "Alert dispatch capped to %s signals for this run",
            settings.alert_max_per_run,
        )

    snapshots_by_symbol = _snapshot_index(market_snapshots)
    sent_count = 0
    failed_count = 0
    skipped_count = 0

    for user in get_eligible_users_for_alerts(db):
        if not can_receive_alerts(user.plan):
            skipped_count += len(limited_signals)
            continue

        for subscription in user.alert_subscriptions:
            if not subscription.is_active:
                continue
            if not _delivery_ready_for_subscription(subscription):
                continue

            if subscription.channel == CHANNEL_TELEGRAM and not settings.enable_telegram_alerts:
                logger.info("Telegram channel disabled by config")
                continue
            if subscription.channel == CHANNEL_EMAIL and not settings.enable_email_alerts:
                logger.info("Email channel disabled by config")
                continue

            eligible_signals = get_eligible_signals_for_user(subscription, limited_signals)
            for signal in eligible_signals:
                delivery = create_pending_delivery(
                    db,
                    signal=signal,
                    user=user,
                    channel=subscription.channel,
                )
                if delivery is None:
                    skipped_count += 1
                    continue

                snapshot = snapshots_by_symbol.get(signal.asset_symbol.upper())
                try:
                    if subscription.channel == CHANNEL_TELEGRAM:
                        payload = send_telegram_message(
                            subscription.telegram_chat_id or "",
                            format_signal_alert_message(signal, snapshot, plan=user.plan),
                        )
                    else:
                        payload = send_email_message(
                            subscription.email or user.email,
                            f"Crypto Intelligence Alert - {signal.asset_symbol}",
                            format_email_alert_message(signal, snapshot),
                        )
                    _mark_delivery_sent(db, delivery, payload.get("message_id"))
                    sent_count += 1
                    logger.info(
                        "Alert sent channel=%s signal_id=%s user_id=%s",
                        subscription.channel,
                        signal.id,
                        user.id,
                    )
                except Exception as exc:
                    _mark_delivery_failed(db, delivery, str(exc))
                    failed_count += 1
                    logger.warning(
                        "Alert failed channel=%s signal_id=%s user_id=%s error=%s",
                        subscription.channel,
                        signal.id,
                        user.id,
                        exc,
                    )

    return {"sent": sent_count, "failed": failed_count, "skipped": skipped_count}


def dispatch_new_setups(
    db: Session,
    new_signals: list[SignalRecord],
    *,
    detected_signals: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    settings = get_settings()
    if not settings.enable_alerts:
        logger.info("Confluence alert dispatch skipped because ENABLE_ALERTS=false")
        return {"sent": 0, "failed": 0, "skipped": len(new_signals)}

    if not new_signals:
        return {"sent": 0, "failed": 0, "skipped": 0}

    candidates = _build_setup_candidates(
        new_signals=new_signals,
        detected_signals=detected_signals,
        market_snapshots=market_snapshots,
    )
    if not candidates:
        return {"sent": 0, "failed": 0, "skipped": len(new_signals)}

    limited_candidates = candidates[: settings.alert_max_per_run]
    if len(candidates) > len(limited_candidates):
        logger.info(
            "Confluence alert dispatch capped to %s setups for this run",
            settings.alert_max_per_run,
        )

    sent_count = 0
    failed_count = 0
    skipped_count = 0

    for user in get_eligible_users_for_alerts(db):
        if not can_receive_alerts(user.plan):
            skipped_count += len(limited_candidates)
            continue

        for subscription in user.alert_subscriptions:
            if not subscription.is_active:
                continue
            if not _delivery_ready_for_subscription(subscription):
                continue

            if subscription.channel == CHANNEL_TELEGRAM and not settings.enable_telegram_alerts:
                logger.info("Telegram channel disabled by config")
                continue
            if subscription.channel == CHANNEL_EMAIL and not settings.enable_email_alerts:
                logger.info("Email channel disabled by config")
                continue

            eligible_setups = get_eligible_setups_for_user(subscription, limited_candidates)
            for candidate in eligible_setups:
                anchor_signal = candidate["anchor_signal"]
                setup_view = candidate["setup_view"]
                delivery = create_pending_delivery(
                    db,
                    signal=anchor_signal,
                    user=user,
                    channel=subscription.channel,
                )
                if delivery is None:
                    skipped_count += 1
                    logger.info(
                        "Confluence alert skipped setup_key=%s asset=%s user_id=%s reason=duplicate_delivery",
                        _get_value(setup_view, "setup_key"),
                        _get_value(setup_view, "asset_symbol"),
                        user.id,
                    )
                    continue

                try:
                    if subscription.channel == CHANNEL_TELEGRAM:
                        payload = send_telegram_message(
                            subscription.telegram_chat_id or "",
                            format_confluence_setup_alert(setup_view, plan=user.plan),
                        )
                    else:
                        payload = send_email_message(
                            subscription.email or user.email,
                            f"Crypto Intelligence Setup - {_get_value(setup_view, 'asset_symbol')} - {_get_value(setup_view, 'setup_type')}",
                            format_confluence_setup_alert(setup_view, plan=user.plan),
                        )
                    _mark_delivery_sent(db, delivery, payload.get("message_id"))
                    sent_count += 1
                    logger.info(
                        "Confluence alert sent channel=%s setup_key=%s asset=%s user_id=%s anchor_signal_id=%s",
                        subscription.channel,
                        _get_value(setup_view, "setup_key"),
                        _get_value(setup_view, "asset_symbol"),
                        user.id,
                        anchor_signal.id,
                    )
                except Exception as exc:
                    _mark_delivery_failed(db, delivery, str(exc))
                    failed_count += 1
                    logger.warning(
                        "Confluence alert failed channel=%s setup_key=%s asset=%s user_id=%s error=%s",
                        subscription.channel,
                        _get_value(setup_view, "setup_key"),
                        _get_value(setup_view, "asset_symbol"),
                        user.id,
                        exc,
                    )

    return {"sent": sent_count, "failed": failed_count, "skipped": skipped_count}


def process_alert_pipeline(
    db: Session,
    new_signals: list[SignalRecord],
    *,
    detected_signals: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    settings = get_settings()
    if settings.enable_confluence_engine and not settings.alert_on_individual_signals:
        return dispatch_new_setups(
            db,
            new_signals,
            detected_signals=detected_signals,
            market_snapshots=market_snapshots,
        )
    return dispatch_new_signals(db, new_signals, market_snapshots=market_snapshots)
