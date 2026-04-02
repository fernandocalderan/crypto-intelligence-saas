from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import AlertSubscriptionRecord, UserRecord
from services.alert_engine import send_telegram_test_for_user, upsert_telegram_subscription
from services.telegram_service import TelegramServiceError, send_telegram_message


def build_test_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    return TestingSession


def make_settings(**overrides):
    defaults = {
        "alert_min_score": 7.0,
        "alert_min_confidence": 0.6,
        "enable_alerts": True,
        "enable_telegram_alerts": True,
        "enable_email_alerts": False,
        "telegram_bot_token": "test-token",
        "telegram_bot_username": "Crypto_Intelligence_SaaS_bot",
        "alert_max_per_run": 50,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def create_user(session_factory, *, plan: str) -> UserRecord:
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


def test_free_user_cannot_send_telegram_test(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="free")

    monkeypatch.setattr("services.alert_engine.SessionLocal", session_factory)
    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())

    with pytest.raises(HTTPException) as exc_info:
        send_telegram_test_for_user(user)

    assert exc_info.value.status_code == 403
    assert "Actualiza a Pro" in exc_info.value.detail


def test_pro_user_with_connected_chat_can_send_manual_test(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="pro")

    with session_factory() as session:
        session.add(
            AlertSubscriptionRecord(
                user_id=user.id,
                channel="telegram",
                is_active=False,
                telegram_chat_id="123456789",
                min_score=7.0,
                min_confidence=0.6,
            )
        )
        session.commit()

    calls: list[tuple[str, str, str]] = []

    def fake_send_test(chat_id: str, user_identifier: str, plan: str):
        calls.append((chat_id, user_identifier, plan))
        return {"message_id": "42"}

    monkeypatch.setattr("services.alert_engine.SessionLocal", session_factory)
    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())
    monkeypatch.setattr("services.alert_engine.send_telegram_test_message", fake_send_test)

    result = send_telegram_test_for_user(user)

    assert result.ok is True
    assert result.detail == "Mensaje de prueba enviado"
    assert result.telegram_chat_id == "123456789"
    assert result.provider_message_id == "42"
    assert calls == [("123456789", "pro@example.com", "pro")]


def test_missing_telegram_token_returns_controlled_error(monkeypatch) -> None:
    monkeypatch.setattr("services.telegram_service.get_settings", lambda: make_settings(telegram_bot_token=""))

    with pytest.raises(TelegramServiceError) as exc_info:
        send_telegram_message("123456789", "hola")

    assert exc_info.value.status_code == 503
    assert "temporalmente" in exc_info.value.user_message


def test_invalid_chat_error_is_controlled(monkeypatch) -> None:
    monkeypatch.setattr("services.telegram_service.get_settings", lambda: make_settings())

    with pytest.raises(TelegramServiceError) as exc_info:
        send_telegram_message("chat-invalido", "hola")

    assert exc_info.value.status_code == 400
    assert "chat ID de Telegram no es válido" in exc_info.value.user_message


def test_connect_telegram_persists_chat_id(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="pro")

    monkeypatch.setattr("services.alert_engine.SessionLocal", session_factory)
    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())

    response = upsert_telegram_subscription(user, telegram_chat_id=123456789, is_active=True)

    with session_factory() as session:
        subscription = session.scalar(
            select(AlertSubscriptionRecord).where(
                AlertSubscriptionRecord.user_id == user.id,
                AlertSubscriptionRecord.channel == "telegram",
            )
        )

    assert subscription is not None
    assert subscription.telegram_chat_id == "123456789"
    assert response.telegram_chat_id == "123456789"
    assert response.telegram_configured is True
    assert response.telegram_enabled is True


def test_provider_error_from_telegram_test_is_returned_cleanly(monkeypatch) -> None:
    session_factory = build_test_session_factory()
    user = create_user(session_factory, plan="pro")

    with session_factory() as session:
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
        session.commit()

    monkeypatch.setattr("services.alert_engine.SessionLocal", session_factory)
    monkeypatch.setattr("services.alert_engine.get_settings", lambda: make_settings())

    def failing_send_test(chat_id: str, user_identifier: str, plan: str):
        raise TelegramServiceError(
            "Bad Request: chat not found",
            user_message="Abre Telegram, busca el bot y pulsa Start antes de volver a intentarlo. Si ya lo hiciste, revisa el chat ID.",
            code="telegram_chat_not_ready",
            status_code=400,
        )

    monkeypatch.setattr("services.alert_engine.send_telegram_test_message", failing_send_test)

    with pytest.raises(HTTPException) as exc_info:
        send_telegram_test_for_user(user)

    assert exc_info.value.status_code == 400
    assert "pulsa Start" in exc_info.value.detail
