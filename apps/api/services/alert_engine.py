import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from config import get_settings
from db.session import SessionLocal
from db.models import AlertDeliveryRecord, AlertSubscriptionRecord, SignalRecord, UserRecord
from models.schemas import AlertsMeResponse
from services.email_alert_service import format_email_alert_message, send_email_message
from services.plans import can_receive_alerts, normalize_plan
from services.telegram_service import format_signal_alert_message, send_telegram_message

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


def upsert_telegram_subscription(
    user: UserRecord,
    *,
    telegram_chat_id: str,
    is_active: bool | None = True,
) -> AlertsMeResponse:
    with SessionLocal() as db:
        persistent_user = _load_user_with_alerts(db, user.id)
        subscription = _get_or_create_subscription(db, user=persistent_user, channel=CHANNEL_TELEGRAM)
        subscription.telegram_chat_id = telegram_chat_id.strip()
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
                            format_signal_alert_message(signal, snapshot),
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


def process_alert_pipeline(
    db: Session,
    new_signals: list[SignalRecord],
    *,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    return dispatch_new_signals(db, new_signals, market_snapshots=market_snapshots)
