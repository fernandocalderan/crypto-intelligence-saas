import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from config import get_settings
from db.session import SessionLocal
from db.models import AlertDeliveryRecord, AlertSubscriptionRecord, SignalRecord, UserRecord
from models.schemas import (
    AlertDeliveryDebugEntry,
    AlertsDebugResponse,
    AlertsMeResponse,
    TelegramConnectInstructionsResponse,
    TelegramTestResponse,
)
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
DEBUG_LOOKBACK_HOURS = 24
ALERT_KIND_SETUP = "setup_pro"
ALERT_KIND_EARLY_SIGNAL = "early_signal"


def _coerce_threshold_confidence(value: float | None) -> float:
    # User-configured confidence is stored as a ratio (0.55 = 55%), while the
    # runtime setup/signal confidence values are compared on a 0-100 scale.
    resolved = get_settings().alert_min_confidence if value is None else float(value)
    return resolved * 100.0 if resolved <= 1.0 else resolved


def _normalize_configured_confidence(value: float | None) -> float:
    if value is None:
        return float(get_settings().alert_min_confidence)

    resolved = max(float(value), 0.0)
    return resolved / 100.0 if resolved > 1.0 else resolved


def _resolve_configured_thresholds(subscription: AlertSubscriptionRecord | None) -> tuple[float, float]:
    settings = get_settings()
    min_score = (
        float(subscription.min_score)
        if subscription is not None and subscription.min_score is not None
        else float(settings.alert_min_score)
    )
    min_confidence = (
        _normalize_configured_confidence(subscription.min_confidence)
        if subscription is not None and subscription.min_confidence is not None
        else float(settings.alert_min_confidence)
    )
    return min_score, min_confidence


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


def _signal_priority_key(signal: SignalRecord) -> tuple[str, str]:
    return (
        str(signal.asset_symbol).upper(),
        str(signal.direction or "neutral"),
    )


def _setup_priority_key(setup_view: Any) -> tuple[str, str]:
    return (
        str(_get_value(setup_view, "asset_symbol", "")).upper(),
        str(_get_value(setup_view, "direction", "neutral")),
    )


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


def _configured_min_setup_score(settings: Any) -> float:
    return float(getattr(settings, "min_setup_score", getattr(settings, "alert_min_score", 6.5)))


def _configured_min_setup_confidence(settings: Any) -> float:
    return float(getattr(settings, "min_setup_confidence", _coerce_threshold_confidence(getattr(settings, "alert_min_confidence", 0.55))))


def _configured_early_signal_min_score(settings: Any) -> float:
    return float(getattr(settings, "early_signal_min_score", 7.2))


def _configured_early_signal_min_confidence(settings: Any) -> float:
    configured = float(getattr(settings, "early_signal_min_confidence", 0.65))
    return _coerce_threshold_confidence(configured)


def _resolve_early_signal_thresholds(subscription: AlertSubscriptionRecord | None) -> tuple[float, float]:
    settings = get_settings()
    subscription_min_score, subscription_min_confidence = _resolve_configured_thresholds(subscription)
    return (
        max(_configured_early_signal_min_score(settings), float(subscription_min_score)),
        max(_configured_early_signal_min_confidence(settings), _coerce_threshold_confidence(subscription_min_confidence)),
    )


def _mask_chat_id(chat_id: str | None) -> str | None:
    if not chat_id:
        return None
    if len(chat_id) <= 4:
        return chat_id
    return f"{chat_id[:2]}***{chat_id[-2:]}"


def _build_dispatch_result(candidate_count: int = 0) -> dict[str, Any]:
    return {
        "candidates": candidate_count,
        "deliveries_created": 0,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "skip_reasons": {},
        "setups_detected": 0,
        "individual_signals_detected": 0,
        "setups_sent": 0,
        "individual_signals_sent": 0,
    }


def _register_skip(result: dict[str, Any], reason: str, *, count: int = 1, **context: Any) -> None:
    result["skipped"] += count
    skip_reasons = result.setdefault("skip_reasons", {})
    skip_reasons[reason] = int(skip_reasons.get(reason, 0)) + count
    serialized_context = " ".join(f"{key}={value}" for key, value in context.items())
    if serialized_context:
        logger.info("alert_delivery_skipped reason=%s count=%s %s", reason, count, serialized_context)
    else:
        logger.info("alert_delivery_skipped reason=%s count=%s", reason, count)


def _register_sent(result: dict[str, Any], alert_kind: str) -> None:
    result["sent"] += 1
    if alert_kind == ALERT_KIND_SETUP:
        result["setups_sent"] += 1
    elif alert_kind == ALERT_KIND_EARLY_SIGNAL:
        result["individual_signals_sent"] += 1


def _build_setup_priority_maps(eligible_setups: list[dict[str, Any]]) -> tuple[set[tuple[str, str]], set[str]]:
    setup_keys: set[tuple[str, str]] = set()
    component_hashes: set[str] = set()

    for candidate in eligible_setups:
        setup_keys.add(_setup_priority_key(candidate["setup_view"]))
        for component in list(_get_value(candidate["setup_payload"], "signals", [])):
            signal_hash = str(_get_value(component, "signal_hash", "")).strip()
            if signal_hash:
                component_hashes.add(signal_hash)

    return setup_keys, component_hashes


def _signal_shadowed_by_setup(
    signal: SignalRecord,
    *,
    setup_priority_keys: set[tuple[str, str]],
    setup_component_hashes: set[str],
) -> bool:
    if signal.signal_hash in setup_component_hashes:
        return True
    return _signal_priority_key(signal) in setup_priority_keys


def _recently_delivered_assets_for_user(
    db: Session,
    *,
    user_id: int,
    channel: str,
    lookback_hours: int,
) -> set[str]:
    if lookback_hours <= 0:
        return set()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    rows = db.execute(
        select(SignalRecord.asset_symbol)
        .join(AlertDeliveryRecord, AlertDeliveryRecord.signal_id == SignalRecord.id)
        .where(
            AlertDeliveryRecord.user_id == user_id,
            AlertDeliveryRecord.channel == channel,
            AlertDeliveryRecord.delivery_status == DELIVERY_SENT,
            AlertDeliveryRecord.sent_at.is_not(None),
            AlertDeliveryRecord.sent_at >= cutoff,
        )
    ).all()
    return {str(row[0]).upper() for row in rows if row and row[0]}


def _delivery_debug_entry(delivery: AlertDeliveryRecord | None) -> AlertDeliveryDebugEntry | None:
    if delivery is None:
        return None
    return AlertDeliveryDebugEntry(
        channel=delivery.channel,
        delivery_status=delivery.delivery_status,
        provider_message_id=delivery.provider_message_id,
        error_code=delivery.error_code,
        error_message=delivery.error_message,
        created_at=delivery.created_at,
        sent_at=delivery.sent_at,
    )


def _build_settings_response(user: UserRecord, subscriptions: list[AlertSubscriptionRecord]) -> AlertsMeResponse:
    settings = get_settings()
    by_channel = {subscription.channel: subscription for subscription in subscriptions}
    telegram = by_channel.get(CHANNEL_TELEGRAM)
    email = by_channel.get(CHANNEL_EMAIL)

    threshold_owner = telegram or email
    min_score, min_confidence = _resolve_configured_thresholds(threshold_owner)
    effective_min_score, effective_min_confidence_pct = _resolve_setup_thresholds(telegram or email)
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
        effective_min_score=float(effective_min_score),
        effective_min_confidence_pct=float(effective_min_confidence_pct),
        setup_min_score=_configured_min_setup_score(settings),
        setup_min_confidence_pct=_configured_min_setup_confidence(settings),
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


def get_alert_debug_for_user(user: UserRecord) -> AlertsDebugResponse:
    settings = get_settings()
    with SessionLocal() as db:
        persistent_user = _load_user_with_alerts(db, user.id)
        normalized_plan = normalize_plan(persistent_user.plan)
        telegram_subscription = next(
            (item for item in persistent_user.alert_subscriptions if item.channel == CHANNEL_TELEGRAM),
            None,
        )
        threshold_owner = telegram_subscription
        min_score, min_confidence = _resolve_configured_thresholds(threshold_owner)
        effective_min_score, effective_min_confidence_pct = _resolve_setup_thresholds(telegram_subscription)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=DEBUG_LOOKBACK_HOURS)
        recent_signals = db.scalars(
            select(SignalRecord).where(SignalRecord.created_at >= recent_cutoff).order_by(SignalRecord.created_at.desc())
        ).all()
        recent_eligible_signal_count = 0
        if telegram_subscription is not None:
            recent_eligible_signal_count = len(
                get_eligible_signals_for_user(telegram_subscription, recent_signals)
            )

        recent_deliveries = db.scalars(
            select(AlertDeliveryRecord)
            .where(
                AlertDeliveryRecord.user_id == persistent_user.id,
                AlertDeliveryRecord.created_at >= recent_cutoff,
            )
            .order_by(AlertDeliveryRecord.created_at.desc())
        ).all()
        latest_sent = next((delivery for delivery in recent_deliveries if delivery.delivery_status == DELIVERY_SENT), None)
        latest_failed = next((delivery for delivery in recent_deliveries if delivery.delivery_status == DELIVERY_FAILED), None)

        return AlertsDebugResponse(
            plan=normalized_plan,
            can_receive_alerts=can_receive_alerts(normalized_plan),
            alerts_globally_enabled=settings.enable_alerts,
            telegram_available=_telegram_system_ready(),
            bot_configured=bool(settings.telegram_bot_token.strip()),
            telegram_subscription_active=bool(telegram_subscription and telegram_subscription.is_active),
            telegram_enabled=bool(telegram_subscription and telegram_subscription.is_active),
            telegram_chat_id_present=bool(telegram_subscription and telegram_subscription.telegram_chat_id),
            telegram_chat_id_masked=_mask_chat_id(telegram_subscription.telegram_chat_id if telegram_subscription else None),
            min_score=min_score,
            min_confidence=min_confidence,
            effective_min_score=effective_min_score,
            effective_min_confidence_pct=effective_min_confidence_pct,
            setup_min_score=_configured_min_setup_score(settings),
            setup_min_confidence_pct=_configured_min_setup_confidence(settings),
            alerts_process_on_scheduler=settings.alerts_process_on_scheduler,
            recent_deliveries_count=len(recent_deliveries),
            recent_eligible_signal_count=recent_eligible_signal_count,
            latest_sent=_delivery_debug_entry(latest_sent),
            latest_failed=_delivery_debug_entry(latest_failed),
            last_error_code=latest_failed.error_code if latest_failed else None,
            last_error_known=latest_failed.error_message if latest_failed else None,
        )


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
            resolved_min_confidence = _normalize_configured_confidence(min_confidence)
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
            logger.info("telegram_manual_test_skipped user_id=%s reason=skipped_no_chat_id", persistent_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conecta Telegram antes de enviar una prueba.",
            )

        logger.info(
            "telegram_manual_test_requested user_id=%s plan=%s telegram_enabled=%s chat_id_present=%s bot_configured=%s",
            persistent_user.id,
            normalized_plan,
            bool(subscription.is_active),
            bool(subscription.telegram_chat_id),
            bool(settings.telegram_bot_token.strip()),
        )

        try:
            payload = send_telegram_test_message(
                subscription.telegram_chat_id,
                persistent_user.email,
                normalized_plan,
            )
        except TelegramServiceError as exc:
            logger.warning(
                "telegram_manual_test_failed user_id=%s code=%s detail=%s",
                persistent_user.id,
                exc.code,
                exc.detail,
            )
            raise HTTPException(status_code=exc.status_code, detail=exc.user_message) from exc

        logger.info(
            "telegram_manual_test_sent user_id=%s provider_message_id=%s",
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
    *,
    result: dict[str, Any] | None = None,
) -> list[SignalRecord]:
    settings = get_settings()
    min_score = subscription.min_score if subscription.min_score is not None else settings.alert_min_score
    min_confidence = (
        subscription.min_confidence
        if subscription.min_confidence is not None
        else settings.alert_min_confidence
    )

    eligible_signals: list[SignalRecord] = []
    for signal in signals:
        if signal_passes_thresholds(
            score=signal.score,
            confidence=signal.confidence,
            min_score=float(min_score),
            min_confidence=float(min_confidence),
        ):
            eligible_signals.append(signal)
            continue
        if result is not None:
            _register_skip(
                result,
                "skipped_threshold",
                signal_id=signal.id,
                asset_symbol=signal.asset_symbol,
                channel=subscription.channel,
                score=signal.score,
                confidence=signal.confidence,
                min_score=float(min_score),
                min_confidence=float(min_confidence),
            )
    return eligible_signals


def get_eligible_early_signals_for_user(
    subscription: AlertSubscriptionRecord,
    signals: list[SignalRecord],
    *,
    result: dict[str, Any] | None = None,
) -> list[SignalRecord]:
    min_score, min_confidence = _resolve_early_signal_thresholds(subscription)
    eligible_signals: list[SignalRecord] = []

    ranked_signals = sorted(
        signals,
        key=lambda signal: (float(signal.score), float(signal.confidence)),
        reverse=True,
    )

    for signal in ranked_signals:
        if signal_passes_thresholds(
            score=signal.score,
            confidence=signal.confidence,
            min_score=min_score,
            min_confidence=min_confidence,
        ):
            eligible_signals.append(signal)
            continue

        logger.info(
            "early_signal_filtered_by_threshold user_id=%s channel=%s signal_id=%s asset=%s signal_key=%s actual_score=%s actual_confidence=%s effective_min_score=%s effective_min_confidence=%s",
            subscription.user_id,
            subscription.channel,
            signal.id,
            signal.asset_symbol,
            signal.signal_key,
            signal.score,
            signal.confidence,
            min_score,
            min_confidence,
        )
        if result is not None:
            _register_skip(
                result,
                "skipped_threshold",
                user_id=subscription.user_id,
                channel=subscription.channel,
                signal_id=signal.id,
                asset_symbol=signal.asset_symbol,
                signal_key=signal.signal_key,
                reason_detail="early_signal_threshold",
                effective_min_score=min_score,
                effective_min_confidence=min_confidence,
            )

    return eligible_signals


def _resolve_setup_thresholds(subscription: AlertSubscriptionRecord | None) -> tuple[float, float]:
    settings = get_settings()
    subscription_min_score = (
        float(subscription.min_score)
        if subscription is not None and subscription.min_score is not None
        else float(settings.alert_min_score)
    )
    subscription_min_confidence = (
        _coerce_threshold_confidence(float(subscription.min_confidence))
        if subscription is not None and subscription.min_confidence is not None
        else _coerce_threshold_confidence(settings.alert_min_confidence)
    )
    return (
        max(_configured_min_setup_score(settings), subscription_min_score),
        max(_configured_min_setup_confidence(settings), subscription_min_confidence),
    )


def get_eligible_setups_for_user(
    subscription: AlertSubscriptionRecord,
    setup_candidates: list[dict[str, Any]],
    *,
    result: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    min_score, min_confidence = _resolve_setup_thresholds(subscription)
    eligible: list[dict[str, Any]] = []

    for candidate in setup_candidates:
        setup_view = candidate["setup_view"]
        if _get_value(setup_view, "execution_state") not in {"EXECUTABLE", "WATCHLIST"}:
            if result is not None:
                _register_skip(
                    result,
                    "skipped_threshold",
                    user_id=subscription.user_id,
                    channel=subscription.channel,
                    setup_key=_get_value(setup_view, "setup_key"),
                    reason_detail="execution_state",
                    state=_get_value(setup_view, "execution_state"),
                )
            else:
                logger.info(
                    "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=execution_state state=%s",
                    subscription.user_id,
                    subscription.channel,
                    _get_value(setup_view, "setup_key"),
                    _get_value(setup_view, "execution_state"),
                )
            continue
        if bool(_get_value(setup_view, "is_mock_contaminated")):
            if result is not None:
                _register_skip(
                    result,
                    "skipped_threshold",
                    user_id=subscription.user_id,
                    channel=subscription.channel,
                    setup_key=_get_value(setup_view, "setup_key"),
                    reason_detail="mock_contamination",
                )
            else:
                logger.info(
                    "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=mock_contamination",
                    subscription.user_id,
                    subscription.channel,
                    _get_value(setup_view, "setup_key"),
                )
            continue
        if not _setup_trigger_is_usable(setup_view):
            if result is not None:
                _register_skip(
                    result,
                    "skipped_threshold",
                    user_id=subscription.user_id,
                    channel=subscription.channel,
                    setup_key=_get_value(setup_view, "setup_key"),
                    reason_detail="missing_levels",
                )
            else:
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
                "setup_threshold_not_met user_id=%s channel=%s setup_key=%s asset=%s actual_score=%s actual_confidence=%s effective_min_score=%s effective_min_confidence=%s reason=threshold_not_met",
                subscription.user_id,
                subscription.channel,
                _get_value(setup_view, "setup_key"),
                _get_value(setup_view, "asset_symbol"),
                _get_value(setup_view, "score"),
                _get_value(setup_view, "confidence"),
                min_score,
                min_confidence,
            )
            if result is not None:
                _register_skip(
                    result,
                    "skipped_threshold",
                    user_id=subscription.user_id,
                    channel=subscription.channel,
                    setup_key=_get_value(setup_view, "setup_key"),
                    reason_detail="threshold_not_met",
                    score=_get_value(setup_view, "score"),
                    confidence=_get_value(setup_view, "confidence"),
                    effective_min_score=min_score,
                    effective_min_confidence=min_confidence,
                )
            else:
                logger.info(
                    "Confluence setup filtered user_id=%s channel=%s setup_key=%s reason=threshold_not_met score=%s confidence=%s effective_min_score=%s effective_min_confidence=%s",
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
    delivery.error_code = None
    delivery.error_message = None
    delivery.sent_at = datetime.now(timezone.utc)
    db.commit()


def _mark_delivery_failed(
    db: Session,
    delivery: AlertDeliveryRecord,
    *,
    error_message: str,
    error_code: str | None = None,
) -> None:
    delivery.delivery_status = DELIVERY_FAILED
    delivery.error_code = error_code
    delivery.error_message = error_message[:2000]
    db.commit()


def _dispatch_delivery(
    db: Session,
    *,
    delivery: AlertDeliveryRecord,
    subscription: AlertSubscriptionRecord,
    user: UserRecord,
    text: str,
    email_subject: str,
    email_body: str | None = None,
    alert_kind: str,
    success_context: dict[str, Any],
) -> bool:
    try:
        if subscription.channel == CHANNEL_TELEGRAM:
            payload = send_telegram_message(
                subscription.telegram_chat_id or "",
                text,
            )
        else:
            payload = send_email_message(
                subscription.email or user.email,
                email_subject,
                email_body or text,
            )
        _mark_delivery_sent(db, delivery, payload.get("message_id"))
        logger.info(
            "alert_sent channel=%s alert_kind=%s user_id=%s %s",
            subscription.channel,
            alert_kind,
            user.id,
            " ".join(f"{key}={value}" for key, value in success_context.items()),
        )
        return True
    except TelegramServiceError as exc:
        _mark_delivery_failed(
            db,
            delivery,
            error_message=exc.detail,
            error_code=exc.code,
        )
        logger.warning(
            "alert_failed channel=%s alert_kind=%s user_id=%s code=%s error=%s %s",
            subscription.channel,
            alert_kind,
            user.id,
            exc.code,
            exc.detail,
            " ".join(f"{key}={value}" for key, value in success_context.items()),
        )
        return False
    except Exception as exc:
        _mark_delivery_failed(db, delivery, error_message=str(exc), error_code="dispatch_error")
        logger.warning(
            "alert_failed channel=%s alert_kind=%s user_id=%s code=dispatch_error error=%s %s",
            subscription.channel,
            alert_kind,
            user.id,
            exc,
            " ".join(f"{key}={value}" for key, value in success_context.items()),
        )
        return False


def dispatch_new_signals(
    db: Session,
    signals: list[SignalRecord],
    *,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    result = _build_dispatch_result()
    if not settings.enable_alerts:
        logger.info("Alert dispatch skipped because ENABLE_ALERTS=false")
        _register_skip(result, "skipped_alerts_disabled", count=len(signals))
        return result

    if not signals:
        return result

    limited_signals = signals[: settings.alert_max_per_run]
    result["candidates"] = len(limited_signals)
    result["individual_signals_detected"] = len(limited_signals)
    logger.info("individual_signals_detected count=%s", len(limited_signals))
    if len(signals) > len(limited_signals):
        logger.info(
            "Alert dispatch capped to %s signals for this run",
            settings.alert_max_per_run,
        )

    snapshots_by_symbol = _snapshot_index(market_snapshots)
    for user in get_eligible_users_for_alerts(db):
        if not can_receive_alerts(user.plan):
            _register_skip(result, "skipped_plan", count=len(limited_signals), user_id=user.id, plan=user.plan)
            continue

        if not user.alert_subscriptions:
            _register_skip(result, "skipped_no_active_subscription", count=len(limited_signals), user_id=user.id)
            continue

        for subscription in user.alert_subscriptions:
            if not subscription.is_active:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="subscription_inactive",
                )
                continue
            if subscription.channel == CHANNEL_TELEGRAM and not subscription.telegram_chat_id:
                _register_skip(
                    result,
                    "skipped_no_chat_id",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                )
                continue
            if not _delivery_ready_for_subscription(subscription):
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="no_delivery_target",
                )
                continue

            if subscription.channel == CHANNEL_TELEGRAM and not settings.enable_telegram_alerts:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="telegram_disabled_by_config",
                )
                continue
            if subscription.channel == CHANNEL_EMAIL and not settings.enable_email_alerts:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="email_disabled_by_config",
                )
                continue

            eligible_signals = get_eligible_signals_for_user(subscription, limited_signals, result=result)
            for signal in eligible_signals:
                delivery = create_pending_delivery(
                    db,
                    signal=signal,
                    user=user,
                    channel=subscription.channel,
                )
                if delivery is None:
                    _register_skip(
                        result,
                        "skipped_duplicate",
                        user_id=user.id,
                        channel=subscription.channel,
                        signal_id=signal.id,
                        asset_symbol=signal.asset_symbol,
                        alert_kind=ALERT_KIND_EARLY_SIGNAL,
                    )
                    continue
                result["deliveries_created"] += 1

                snapshot = snapshots_by_symbol.get(signal.asset_symbol.upper())
                success = _dispatch_delivery(
                    db,
                    delivery=delivery,
                    subscription=subscription,
                    user=user,
                    text=format_signal_alert_message(signal, snapshot, plan=user.plan),
                    email_subject=f"Crypto Intelligence Early Signal - {signal.asset_symbol}",
                    email_body=format_email_alert_message(signal, snapshot),
                    alert_kind=ALERT_KIND_EARLY_SIGNAL,
                    success_context={
                        "signal_id": signal.id,
                        "asset_symbol": signal.asset_symbol,
                        "signal_key": signal.signal_key,
                    },
                )
                if success:
                    _register_sent(result, ALERT_KIND_EARLY_SIGNAL)
                else:
                    result["failed"] += 1

    result["alert_deliveries_created_count"] = result["deliveries_created"]
    result["alert_deliveries_sent_count"] = result["sent"]
    result["alert_deliveries_failed_count"] = result["failed"]
    return result


def dispatch_new_setups(
    db: Session,
    new_signals: list[SignalRecord],
    *,
    detected_signals: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    result = _build_dispatch_result()
    if not settings.enable_alerts:
        logger.info("Confluence alert dispatch skipped because ENABLE_ALERTS=false")
        _register_skip(result, "skipped_alerts_disabled", count=len(new_signals))
        return result

    if not new_signals:
        return result

    candidates = _build_setup_candidates(
        new_signals=new_signals,
        detected_signals=detected_signals,
        market_snapshots=market_snapshots,
    )
    if not candidates:
        _register_skip(result, "skipped_no_setup_candidates", count=len(new_signals))
        return result

    limited_candidates = candidates[: settings.alert_max_per_run]
    result["candidates"] = len(limited_candidates)
    result["setups_detected"] = len(limited_candidates)
    logger.info("setups_detected count=%s", len(limited_candidates))
    if len(candidates) > len(limited_candidates):
        logger.info(
            "Confluence alert dispatch capped to %s setups for this run",
            settings.alert_max_per_run,
        )

    for user in get_eligible_users_for_alerts(db):
        if not can_receive_alerts(user.plan):
            _register_skip(result, "skipped_plan", count=len(limited_candidates), user_id=user.id, plan=user.plan)
            continue

        if not user.alert_subscriptions:
            _register_skip(result, "skipped_no_active_subscription", count=len(limited_candidates), user_id=user.id)
            continue

        for subscription in user.alert_subscriptions:
            if not subscription.is_active:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_candidates),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="subscription_inactive",
                )
                continue
            if subscription.channel == CHANNEL_TELEGRAM and not subscription.telegram_chat_id:
                _register_skip(
                    result,
                    "skipped_no_chat_id",
                    count=len(limited_candidates),
                    user_id=user.id,
                    channel=subscription.channel,
                )
                continue
            if not _delivery_ready_for_subscription(subscription):
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_candidates),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="no_delivery_target",
                )
                continue

            if subscription.channel == CHANNEL_TELEGRAM and not settings.enable_telegram_alerts:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_candidates),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="telegram_disabled_by_config",
                )
                continue
            if subscription.channel == CHANNEL_EMAIL and not settings.enable_email_alerts:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_candidates),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="email_disabled_by_config",
                )
                continue

            eligible_setups = get_eligible_setups_for_user(subscription, limited_candidates, result=result)
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
                    _register_skip(
                        result,
                        "skipped_duplicate",
                        user_id=user.id,
                        channel=subscription.channel,
                        setup_key=_get_value(setup_view, "setup_key"),
                        asset_symbol=_get_value(setup_view, "asset_symbol"),
                        anchor_signal_id=anchor_signal.id,
                        alert_kind=ALERT_KIND_SETUP,
                    )
                    continue
                result["deliveries_created"] += 1

                success = _dispatch_delivery(
                    db,
                    delivery=delivery,
                    subscription=subscription,
                    user=user,
                    text=format_confluence_setup_alert(setup_view, plan=user.plan),
                    email_subject=(
                        f"Crypto Intelligence Setup - {_get_value(setup_view, 'asset_symbol')} - "
                        f"{_get_value(setup_view, 'setup_type')}"
                    ),
                    alert_kind=ALERT_KIND_SETUP,
                    success_context={
                        "setup_key": _get_value(setup_view, "setup_key"),
                        "asset_symbol": _get_value(setup_view, "asset_symbol"),
                        "anchor_signal_id": anchor_signal.id,
                    },
                )
                if success:
                    _register_sent(result, ALERT_KIND_SETUP)
                else:
                    result["failed"] += 1

    result["alert_deliveries_created_count"] = result["deliveries_created"]
    result["alert_deliveries_sent_count"] = result["sent"]
    result["alert_deliveries_failed_count"] = result["failed"]
    return result


def dispatch_hybrid_alerts(
    db: Session,
    new_signals: list[SignalRecord],
    *,
    detected_signals: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    result = _build_dispatch_result()
    if not settings.enable_alerts:
        logger.info("Hybrid alert dispatch skipped because ENABLE_ALERTS=false")
        _register_skip(result, "skipped_alerts_disabled", count=len(new_signals))
        return result

    if not new_signals:
        return result

    limited_signals = new_signals[: settings.alert_max_per_run]
    setup_candidates = _build_setup_candidates(
        new_signals=limited_signals,
        detected_signals=detected_signals,
        market_snapshots=market_snapshots,
    )
    limited_setup_candidates = setup_candidates[: settings.alert_max_per_run]
    result["candidates"] = len(limited_setup_candidates) + len(limited_signals)
    result["setups_detected"] = len(limited_setup_candidates)
    result["individual_signals_detected"] = len(limited_signals)
    logger.info(
        "alert_pipeline_mode mode=hybrid setups_detected=%s individual_signals_detected=%s",
        len(limited_setup_candidates),
        len(limited_signals),
    )

    snapshots_by_symbol = _snapshot_index(market_snapshots)
    for user in get_eligible_users_for_alerts(db):
        if not can_receive_alerts(user.plan):
            _register_skip(result, "skipped_plan", count=len(limited_signals), user_id=user.id, plan=user.plan)
            continue

        if not user.alert_subscriptions:
            _register_skip(result, "skipped_no_active_subscription", count=len(limited_signals), user_id=user.id)
            continue

        for subscription in user.alert_subscriptions:
            if not subscription.is_active:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="subscription_inactive",
                )
                continue
            if subscription.channel == CHANNEL_TELEGRAM and not subscription.telegram_chat_id:
                _register_skip(
                    result,
                    "skipped_no_chat_id",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                )
                continue
            if not _delivery_ready_for_subscription(subscription):
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="no_delivery_target",
                )
                continue
            if subscription.channel == CHANNEL_TELEGRAM and not settings.enable_telegram_alerts:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="telegram_disabled_by_config",
                )
                continue
            if subscription.channel == CHANNEL_EMAIL and not settings.enable_email_alerts:
                _register_skip(
                    result,
                    "skipped_channel_disabled",
                    count=len(limited_signals),
                    user_id=user.id,
                    channel=subscription.channel,
                    reason_detail="email_disabled_by_config",
                )
                continue

            eligible_setups = get_eligible_setups_for_user(subscription, limited_setup_candidates, result=result)
            setup_priority_keys, setup_component_hashes = _build_setup_priority_maps(eligible_setups)
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
                    _register_skip(
                        result,
                        "skipped_duplicate",
                        user_id=user.id,
                        channel=subscription.channel,
                        setup_key=_get_value(setup_view, "setup_key"),
                        asset_symbol=_get_value(setup_view, "asset_symbol"),
                        anchor_signal_id=anchor_signal.id,
                        alert_kind=ALERT_KIND_SETUP,
                    )
                    continue
                result["deliveries_created"] += 1
                success = _dispatch_delivery(
                    db,
                    delivery=delivery,
                    subscription=subscription,
                    user=user,
                    text=format_confluence_setup_alert(setup_view, plan=user.plan),
                    email_subject=(
                        f"Crypto Intelligence Setup - {_get_value(setup_view, 'asset_symbol')} - "
                        f"{_get_value(setup_view, 'setup_type')}"
                    ),
                    alert_kind=ALERT_KIND_SETUP,
                    success_context={
                        "setup_key": _get_value(setup_view, "setup_key"),
                        "asset_symbol": _get_value(setup_view, "asset_symbol"),
                        "anchor_signal_id": anchor_signal.id,
                    },
                )
                if success:
                    _register_sent(result, ALERT_KIND_SETUP)
                else:
                    result["failed"] += 1

            if eligible_setups:
                logger.info(
                    "setup_priority_active user_id=%s channel=%s eligible_setups=%s",
                    user.id,
                    subscription.channel,
                    len(eligible_setups),
                )

            cooldown_assets = _recently_delivered_assets_for_user(
                db,
                user_id=user.id,
                channel=subscription.channel,
                lookback_hours=int(settings.early_signal_cooldown_hours),
            )
            ranked_early_signals = get_eligible_early_signals_for_user(subscription, limited_signals, result=result)
            filtered_early_signals: list[SignalRecord] = []
            for signal in ranked_early_signals:
                if _signal_shadowed_by_setup(
                    signal,
                    setup_priority_keys=setup_priority_keys,
                    setup_component_hashes=setup_component_hashes,
                ):
                    _register_skip(
                        result,
                        "skipped_due_to_setup_priority",
                        user_id=user.id,
                        channel=subscription.channel,
                        signal_id=signal.id,
                        asset_symbol=signal.asset_symbol,
                        signal_key=signal.signal_key,
                    )
                    logger.info(
                        "individual_signal_skipped_due_to_setup_priority user_id=%s channel=%s signal_id=%s asset=%s signal_key=%s",
                        user.id,
                        subscription.channel,
                        signal.id,
                        signal.asset_symbol,
                        signal.signal_key,
                    )
                    continue

                if signal.asset_symbol.upper() in cooldown_assets:
                    _register_skip(
                        result,
                        "skipped_early_signal_cooldown",
                        user_id=user.id,
                        channel=subscription.channel,
                        signal_id=signal.id,
                        asset_symbol=signal.asset_symbol,
                        signal_key=signal.signal_key,
                        cooldown_hours=settings.early_signal_cooldown_hours,
                    )
                    logger.info(
                        "early_signal_skipped_by_cooldown user_id=%s channel=%s signal_id=%s asset=%s signal_key=%s cooldown_hours=%s",
                        user.id,
                        subscription.channel,
                        signal.id,
                        signal.asset_symbol,
                        signal.signal_key,
                        settings.early_signal_cooldown_hours,
                    )
                    continue

                filtered_early_signals.append(signal)

            selected_early_signals = filtered_early_signals[: settings.early_signal_max_per_run]
            for signal in filtered_early_signals[settings.early_signal_max_per_run :]:
                _register_skip(
                    result,
                    "skipped_early_signal_cap",
                    user_id=user.id,
                    channel=subscription.channel,
                    signal_id=signal.id,
                    asset_symbol=signal.asset_symbol,
                    signal_key=signal.signal_key,
                    early_signal_max_per_run=settings.early_signal_max_per_run,
                )
                logger.info(
                    "early_signal_skipped_by_cap user_id=%s channel=%s signal_id=%s asset=%s signal_key=%s early_signal_max_per_run=%s",
                    user.id,
                    subscription.channel,
                    signal.id,
                    signal.asset_symbol,
                    signal.signal_key,
                    settings.early_signal_max_per_run,
                )

            for signal in selected_early_signals:

                delivery = create_pending_delivery(
                    db,
                    signal=signal,
                    user=user,
                    channel=subscription.channel,
                )
                if delivery is None:
                    _register_skip(
                        result,
                        "skipped_duplicate",
                        user_id=user.id,
                        channel=subscription.channel,
                        signal_id=signal.id,
                        asset_symbol=signal.asset_symbol,
                        signal_key=signal.signal_key,
                        alert_kind=ALERT_KIND_EARLY_SIGNAL,
                    )
                    continue
                result["deliveries_created"] += 1

                snapshot = snapshots_by_symbol.get(signal.asset_symbol.upper())
                success = _dispatch_delivery(
                    db,
                    delivery=delivery,
                    subscription=subscription,
                    user=user,
                    text=format_signal_alert_message(signal, snapshot, plan=user.plan),
                    email_subject=f"Crypto Intelligence Early Signal - {signal.asset_symbol}",
                    email_body=format_email_alert_message(signal, snapshot),
                    alert_kind=ALERT_KIND_EARLY_SIGNAL,
                    success_context={
                        "signal_id": signal.id,
                        "asset_symbol": signal.asset_symbol,
                        "signal_key": signal.signal_key,
                    },
                )
                if success:
                    _register_sent(result, ALERT_KIND_EARLY_SIGNAL)
                else:
                    result["failed"] += 1

    result["alert_deliveries_created_count"] = result["deliveries_created"]
    result["alert_deliveries_sent_count"] = result["sent"]
    result["alert_deliveries_failed_count"] = result["failed"]
    return result


def process_alert_pipeline(
    db: Session,
    new_signals: list[SignalRecord],
    *,
    detected_signals: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if settings.enable_confluence_engine and settings.alert_on_individual_signals:
        return dispatch_hybrid_alerts(
            db,
            new_signals,
            detected_signals=detected_signals,
            market_snapshots=market_snapshots,
        )
    if settings.enable_confluence_engine and not settings.alert_on_individual_signals:
        logger.info("alert_pipeline_mode mode=confluence")
        return dispatch_new_setups(
            db,
            new_signals,
            detected_signals=detected_signals,
            market_snapshots=market_snapshots,
        )
    logger.info("alert_pipeline_mode mode=legacy_individual_signals")
    return dispatch_new_signals(db, new_signals, market_snapshots=market_snapshots)
