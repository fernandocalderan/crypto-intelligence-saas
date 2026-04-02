from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import AssetRecord, SignalRecord, UserRecord
from services.alert_engine import create_pending_delivery, signal_passes_thresholds
from services.plans import can_receive_alerts
from services.signal_persistence import build_signal_hash
from services.telegram_service import format_signal_alert_message


def build_test_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    return TestingSession()


def test_signal_hash_dedupes_within_same_bucket() -> None:
    timestamp_a = datetime(2026, 4, 2, 10, 2, tzinfo=timezone.utc)
    timestamp_b = datetime(2026, 4, 2, 10, 4, tzinfo=timezone.utc)

    hash_a = build_signal_hash(
        asset_symbol="BTC",
        signal_key="volume_spike",
        timeframe="4H",
        direction="bullish",
        source_snapshot_time=timestamp_a,
        dedupe_window_minutes=5,
    )
    hash_b = build_signal_hash(
        asset_symbol="BTC",
        signal_key="volume_spike",
        timeframe="4H",
        direction="bullish",
        source_snapshot_time=timestamp_b,
        dedupe_window_minutes=5,
    )

    assert hash_a == hash_b


def test_signal_hash_changes_across_buckets() -> None:
    timestamp_a = datetime(2026, 4, 2, 10, 2, tzinfo=timezone.utc)
    timestamp_b = datetime(2026, 4, 2, 10, 7, tzinfo=timezone.utc)

    hash_a = build_signal_hash(
        asset_symbol="BTC",
        signal_key="volume_spike",
        timeframe="4H",
        direction="bullish",
        source_snapshot_time=timestamp_a,
        dedupe_window_minutes=5,
    )
    hash_b = build_signal_hash(
        asset_symbol="BTC",
        signal_key="volume_spike",
        timeframe="4H",
        direction="bullish",
        source_snapshot_time=timestamp_b,
        dedupe_window_minutes=5,
    )

    assert hash_a != hash_b


def test_signal_thresholds_accept_ratio_confidence() -> None:
    assert signal_passes_thresholds(
        score=7.5,
        confidence=78.0,
        min_score=7.0,
        min_confidence=0.6,
    )
    assert not signal_passes_thresholds(
        score=7.5,
        confidence=55.0,
        min_score=7.0,
        min_confidence=0.6,
    )


def test_only_pro_and_higher_can_receive_alerts() -> None:
    assert not can_receive_alerts("free")
    assert can_receive_alerts("pro")
    assert can_receive_alerts("pro_plus")


def test_pending_delivery_is_not_duplicated_for_same_signal_user_channel() -> None:
    session = build_test_session()
    created_at = datetime(2026, 4, 2, 10, 2, tzinfo=timezone.utc)

    user = UserRecord(
        email="pro@example.com",
        password_hash="hash",
        plan="pro",
        is_active=True,
    )
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal_hash = build_signal_hash(
        asset_symbol="BTC",
        signal_key="volume_spike",
        timeframe="4H",
        direction="bullish",
        source_snapshot_time=created_at,
        dedupe_window_minutes=5,
    )
    signal = SignalRecord(
        public_id=signal_hash,
        asset_id=asset.id,
        user_id=None,
        asset_symbol="BTC",
        signal_key="volume_spike",
        signal_type="Volume Spike",
        timeframe="4H",
        direction="bullish",
        confidence=78.0,
        score=8.1,
        thesis="BTC imprime un spike de volumen",
        evidence_json=["volume ratio 1.8x"],
        source="mock",
        source_snapshot_time=created_at,
        signal_hash=signal_hash,
        is_active=True,
        created_at=created_at,
    )
    session.add(signal)
    session.commit()
    session.refresh(signal)

    first = create_pending_delivery(session, signal=signal, user=user, channel="telegram")
    second = create_pending_delivery(session, signal=signal, user=user, channel="telegram")

    assert first is not None
    assert second is None


def test_telegram_formatter_contains_core_signal_fields() -> None:
    message = format_signal_alert_message(
        {
            "asset_symbol": "BTC",
            "signal_type": "Volume Spike",
            "score": 8.1,
            "confidence": 78.0,
            "direction": "bullish",
            "thesis": "BTC imprime flujo nuevo y expansión direccional.",
            "source": "binance+bybit",
        },
        {
            "price_usd": 68420.45,
            "change_24h": 3.4,
            "volume_24h": 31200000000,
            "funding_rate": 0.009,
            "oi_change_24h": 4.2,
            "source": "binance+bybit",
        },
    )

    assert "BTC" in message
    assert "Volume Spike" in message
    assert "Score: 8.1/10" in message
    assert "Direccion: bullish" in message
    assert "Precio:" in message
