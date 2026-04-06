from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import AlertDeliveryRecord, AlertSubscriptionRecord, AssetRecord, SignalRecord, UserRecord
from services.alert_engine import get_alert_debug_for_user, process_alert_pipeline
from services.signal_persistence import build_signal_hash
from services.telegram_service import TelegramServiceError, send_telegram_message


def build_test_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    return testing_session


def make_settings(**overrides):
    defaults = {
        "alert_min_score": 7.0,
        "alert_min_confidence": 0.6,
        "enable_alerts": True,
        "enable_telegram_alerts": True,
        "enable_email_alerts": False,
        "telegram_bot_token": "test-token-123456",
        "telegram_bot_username": "Crypto_Intelligence_SaaS_bot",
        "alert_max_per_run": 50,
        "alerts_process_on_scheduler": True,
        "enable_confluence_engine": False,
        "alert_on_individual_signals": True,
        "min_setup_score": 7.5,
        "min_setup_confidence": 70.0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def create_user(session_factory, *, plan: str = "pro") -> UserRecord:
    with session_factory() as session:
        user = UserRecord(
            email=f"{plan}@example.com",
            password_hash="hash",
            plan=plan,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.expunge(user)
        return user


def create_signal(session: Session, *, asset: AssetRecord, created_at: datetime | None = None) -> SignalRecord:
    signal_time = created_at or datetime.now(timezone.utc)
    signal_hash = build_signal_hash(
        asset_symbol=asset.symbol,
        signal_key="volume_spike",
        timeframe="4H",
        direction="bullish",
        source_snapshot_time=signal_time,
        dedupe_window_minutes=5,
    )
    signal = SignalRecord(
        public_id=signal_hash,
        asset_id=asset.id,
        user_id=None,
        asset_symbol=asset.symbol,
        signal_key="volume_spike",
        signal_type="Volume Spike",
        timeframe="4H",
        direction="bullish",
        confidence=82.0,
        score=8.3,
        thesis="BTC imprime un spike de volumen",
        evidence_json=["volume ratio 1.8x"],
        source="binance+bybit",
        source_snapshot_time=signal_time,
        signal_hash=signal_hash,
        is_active=True,
        created_at=signal_time,
    )
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal


def test_telegram_service_retries_once_on_timeout(monkeypatch) -> None:
    monkeypatch.setattr("services.telegram_service.get_settings", lambda: make_settings())

    calls = {"count": 0}

    class SuccessfulResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": True, "result": {"message_id": 42}}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.TimeoutException("timeout")
        return SuccessfulResponse()

    monkeypatch.setattr("services.telegram_service.httpx.post", fake_post)

    payload = send_telegram_message("123456789", "hola")

    assert calls["count"] == 2
    assert payload["message_id"] == "42"


def test_telegram_service_classifies_unauthorized_bot_token(monkeypatch) -> None:
    monkeypatch.setattr("services.telegram_service.get_settings", lambda: make_settings())

    class UnauthorizedResponse:
        status_code = 401

        @staticmethod
        def json():
            return {"ok": False, "description": "Unauthorized"}

    monkeypatch.setattr("services.telegram_service.httpx.post", lambda *args, **kwargs: UnauthorizedResponse())

    with pytest.raises(TelegramServiceError) as exc_info:
        send_telegram_message("123456789", "hola")

    assert exc_info.value.code == "unauthorized_bot_token"


def test_alert_debug_summary_reports_latest_sent_and_failed(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="pro")

    with session_factory() as session:
        asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
        session.add(asset)
        session.commit()
        session.refresh(asset)
        signal = create_signal(session, asset=asset)
        second_signal = create_signal(
            session,
            asset=asset,
            created_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=10),
        )

        session.add(
            AlertSubscriptionRecord(
                user_id=user.id,
                channel="telegram",
                is_active=True,
                telegram_chat_id="123456789",
                min_score=7.0,
                min_confidence=0.6,
            )
        )
        session.add(
            AlertDeliveryRecord(
                signal_id=signal.id,
                user_id=user.id,
                channel="telegram",
                delivery_status="sent",
                provider_message_id="77",
                sent_at=datetime.now(timezone.utc),
            )
        )
        session.add(
            AlertDeliveryRecord(
                signal_id=second_signal.id,
                user_id=user.id,
                channel="telegram",
                delivery_status="failed",
                error_code="bot_not_started",
                error_message="Bad Request: chat not found",
            )
        )
        session.commit()

    monkeypatch.setattr("services.alert_engine.SessionLocal", session_factory)
    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())

    debug = get_alert_debug_for_user(user)

    assert debug.plan == "pro"
    assert debug.telegram_chat_id_present is True
    assert debug.bot_configured is True
    assert debug.recent_deliveries_count == 2
    assert debug.recent_eligible_signal_count == 2
    assert debug.latest_sent is not None
    assert debug.latest_failed is not None
    assert debug.last_error_code == "bot_not_started"


def test_alert_pipeline_marks_delivery_sent(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="pro")

    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())
    monkeypatch.setattr(
        "services.alert_engine.send_telegram_message",
        lambda chat_id, text: {"message_id": "99"},
    )

    with session_factory() as session:
        asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
        session.add_all(
            [
                asset,
                AlertSubscriptionRecord(
                    user_id=user.id,
                    channel="telegram",
                    is_active=True,
                    telegram_chat_id="123456789",
                    min_score=7.0,
                    min_confidence=0.6,
                ),
            ]
        )
        session.commit()
        session.refresh(asset)
        signal = create_signal(session, asset=asset)

        result = process_alert_pipeline(session, [signal], market_snapshots=[])

        delivery = session.scalar(select(AlertDeliveryRecord))

    assert result["sent"] == 1
    assert result["failed"] == 0
    assert delivery is not None
    assert delivery.delivery_status == "sent"
    assert delivery.provider_message_id == "99"
    assert delivery.error_code is None


def test_alert_pipeline_marks_delivery_failed_with_code(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="pro")

    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())

    def fail_send(chat_id, text):
        raise TelegramServiceError(
            "Bad Request: chat not found",
            user_message="Abre Telegram y pulsa Start.",
            code="bot_not_started",
            status_code=400,
        )

    monkeypatch.setattr("services.alert_engine.send_telegram_message", fail_send)

    with session_factory() as session:
        asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
        session.add_all(
            [
                asset,
                AlertSubscriptionRecord(
                    user_id=user.id,
                    channel="telegram",
                    is_active=True,
                    telegram_chat_id="123456789",
                    min_score=7.0,
                    min_confidence=0.6,
                ),
            ]
        )
        session.commit()
        session.refresh(asset)
        signal = create_signal(session, asset=asset)

        result = process_alert_pipeline(session, [signal], market_snapshots=[])

        delivery = session.scalar(select(AlertDeliveryRecord))

    assert result["sent"] == 0
    assert result["failed"] == 1
    assert delivery is not None
    assert delivery.delivery_status == "failed"
    assert delivery.error_code == "bot_not_started"
    assert "chat not found" in (delivery.error_message or "")
