from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import AlertDeliveryRecord, AlertSubscriptionRecord, AssetRecord, SignalRecord, UserRecord
from services import alert_engine, setup_view
from services.alert_engine import process_alert_pipeline
from services.confluence_engine import compute_confluence_setup_payloads
from services.setup_view import build_setup_views
from services.signal_persistence import build_signal_hash
from services.telegram_service import format_confluence_setup_alert


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    return testing_session()


def base_snapshot(**overrides):
    payload = {
        "symbol": "BTC",
        "name": "Bitcoin",
        "category": "Layer 1",
        "source": "binance+bybit",
        "timeframe": "1D",
        "price_usd": 68420.45,
        "change_24h": 3.4,
        "volume_24h": 31_200_000_000,
        "avg_volume_24h": 16_800_000_000,
        "range_high_20d": 67_900.0,
        "range_low_20d": 61_200.0,
        "funding_rate": 0.009,
        "funding_zscore": 1.3,
        "open_interest": 14_800_000_000,
        "oi_change_24h": 5.2,
        "long_liquidations_1h": 8_400_000,
        "short_liquidations_1h": 5_200_000,
        "avg_liquidations_1h": 4_500_000,
        "momentum_score": 84.2,
        "captured_at": datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        "raw_payload": {
            "binance": {"open_interest": {"open_interest": 14_800_000_000}},
            "bybit": {"open_interest": {"open_interest": 14_700_000_000}},
            "coinglass": {"liquidations": {"long_liquidations_1h": 8_400_000}},
        },
    }
    payload.update(overrides)
    return payload


def build_signal_payload(signal_key: str, *, asset_symbol: str = "BTC", **overrides):
    defaults = {
        "volume_spike": {
            "signal_type": "Volume Spike",
            "direction": "bullish",
            "score": 8.8,
            "confidence": 83.0,
            "thesis": "BTC imprime un spike de volumen con expansión direccional y entrada de flujo nuevo.",
            "evidence": ["volume ratio 1.9x", "price change +3.4%"],
            "timeframe": "4H",
        },
        "range_breakout": {
            "signal_type": "Range Breakout",
            "direction": "bullish",
            "score": 8.6,
            "confidence": 80.0,
            "thesis": "BTC sale del rango de 20 días con confirmación de precio y volumen.",
            "evidence": ["breakout margin 0.8%", "volume ratio 1.4x"],
            "timeframe": "4H",
        },
        "funding_extreme": {
            "signal_type": "Funding Extreme",
            "direction": "bearish",
            "score": 8.5,
            "confidence": 79.0,
            "thesis": "BTC muestra un extremo de funding con crowd demasiado cargado en longs.",
            "evidence": ["funding rate +0.0310", "funding z-score 2.8"],
            "timeframe": "8H",
        },
        "liquidation_cluster": {
            "signal_type": "Liquidation Cluster",
            "direction": "bearish",
            "score": 8.1,
            "confidence": 76.0,
            "thesis": "BTC registra un barrido de shorts que deja setup de reversión táctica.",
            "evidence": ["liquidation ratio 3.1x", "dominant side shorts"],
            "timeframe": "1H",
        },
        "oi_divergence": {
            "signal_type": "OI Divergence",
            "direction": "bearish",
            "score": 7.7,
            "confidence": 72.0,
            "thesis": "BTC presenta divergencia entre precio y OI, señal de positioning failure.",
            "evidence": ["price change +2.6%", "OI change -6.8%"],
            "timeframe": "4H",
        },
    }
    payload = {
        "id": f"sig-{asset_symbol.lower()}-{signal_key}",
        "signal_key": signal_key,
        "asset_symbol": asset_symbol,
        "source": "binance+bybit",
        "generated_at": datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
    }
    payload.update(defaults[signal_key])
    if asset_symbol != "BTC":
        payload["thesis"] = str(payload["thesis"]).replace("BTC", asset_symbol)
    payload.update(overrides)
    return payload


def build_persisted_signal(
    signal_key: str,
    *,
    asset_symbol: str = "BTC",
    created_at: datetime | None = None,
    **overrides,
) -> SignalRecord:
    created_at = created_at or datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc)
    payload = build_signal_payload(signal_key, asset_symbol=asset_symbol, generated_at=created_at, **overrides)
    signal_hash = build_signal_hash(
        asset_symbol=asset_symbol,
        signal_key=signal_key,
        timeframe=str(payload["timeframe"]),
        direction=str(payload["direction"]),
        source_snapshot_time=created_at,
        created_at=created_at,
    )
    return SignalRecord(
        public_id=signal_hash,
        asset_symbol=asset_symbol,
        signal_key=signal_key,
        signal_type=str(payload["signal_type"]),
        timeframe=str(payload["timeframe"]),
        direction=str(payload["direction"]),
        confidence=float(payload["confidence"]),
        score=float(payload["score"]),
        thesis=str(payload["thesis"]),
        evidence_json=list(payload["evidence"]),
        source=str(payload["source"]),
        source_snapshot_time=created_at,
        signal_hash=signal_hash,
        is_active=True,
        created_at=created_at,
    )


def make_alert_settings(**overrides):
    settings = {
        "enable_alerts": True,
        "enable_telegram_alerts": True,
        "enable_email_alerts": False,
        "alert_min_score": 6.5,
        "alert_min_confidence": 0.55,
        "alert_max_per_run": 50,
        "enable_confluence_engine": True,
        "alert_on_individual_signals": False,
        "min_setup_score": 7.5,
        "min_setup_confidence": 70.0,
        "early_signal_min_score": 7.2,
        "early_signal_min_confidence": 0.65,
        "early_signal_max_per_run": 2,
        "early_signal_cooldown_hours": 8,
        "setup_require_no_mock_for_executable": True,
        "telegram_bot_token": "token",
    }
    settings.update(overrides)
    return SimpleNamespace(**settings)


def test_confluence_detection_builds_sorted_setups() -> None:
    snapshots = [base_snapshot()]
    signal_payloads = [
        build_signal_payload("volume_spike"),
        build_signal_payload("range_breakout"),
        build_signal_payload("oi_divergence", score=7.1, confidence=68.0),
    ]

    setups = compute_confluence_setup_payloads(
        signal_payloads=signal_payloads,
        market_snapshots=snapshots,
    )

    assert setups
    assert setups[0]["setup_key"] == "trend_continuation"
    assert setups[0]["asset_symbol"] == "BTC"
    assert {"volume_spike", "range_breakout"}.issubset(setups[0]["signal_keys"])


def test_clean_trend_continuation_can_be_executable() -> None:
    setups = compute_confluence_setup_payloads(
        signal_payloads=[build_signal_payload("volume_spike"), build_signal_payload("range_breakout")],
        market_snapshots=[base_snapshot()],
    )
    view = build_setup_views(setups, [base_snapshot()], plan="pro")[0]

    assert view.execution_state == "EXECUTABLE"
    assert view.is_trade_executable is True
    assert view.action_plan is not None
    assert view.action_plan.action_now == "enter"


def test_mock_contaminated_setup_never_becomes_executable() -> None:
    setups = compute_confluence_setup_payloads(
        signal_payloads=[
            build_signal_payload("volume_spike", source="binance+bybit+mock"),
            build_signal_payload("range_breakout", source="binance+bybit+mock"),
        ],
        market_snapshots=[base_snapshot(source="binance+bybit+mock")],
    )
    view = build_setup_views(setups, [base_snapshot(source="binance+bybit+mock")], plan="pro")[0]

    assert view.is_mock_contaminated is True
    assert view.execution_state != "EXECUTABLE"
    assert any(warning.code == "mock_contamination" for warning in view.data_quality_warnings)


def test_setup_formatter_includes_confluence_and_plan() -> None:
    setups = compute_confluence_setup_payloads(
        signal_payloads=[build_signal_payload("volume_spike"), build_signal_payload("range_breakout")],
        market_snapshots=[base_snapshot()],
    )
    view = build_setup_views(setups, [base_snapshot()], plan="pro")[0]
    message = format_confluence_setup_alert(view, plan="pro")

    assert "SETUP PRO" in message
    assert "Confluencia:" in message
    assert "volume_spike + range_breakout" in message
    assert "Plan:" in message
    assert "Riesgo / calidad del dato:" in message


def test_confluence_mode_does_not_send_individual_signal_alerts_by_default(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal = build_persisted_signal("volume_spike")
    signal.asset_id = asset.id
    session.add(signal)
    session.commit()
    session.refresh(signal)

    subscription = AlertSubscriptionRecord(
        user_id=user.id,
        channel="telegram",
        is_active=True,
        telegram_chat_id="123456789",
    )
    session.add(subscription)
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            enable_confluence_engine=True,
            alert_on_individual_signals=False,
        ),
    )
    monkeypatch.setattr(
        setup_view,
        "get_settings",
        lambda: SimpleNamespace(setup_require_no_mock_for_executable=True),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-1"},
    )

    result = process_alert_pipeline(
        session,
        [signal],
        detected_signals=[build_signal_payload("volume_spike")],
        market_snapshots=[base_snapshot()],
    )

    assert result["sent"] == 0
    assert calls == []


def test_legacy_mode_still_sends_individual_signal_alerts(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal = build_persisted_signal("volume_spike")
    signal.asset_id = asset.id
    session.add(signal)
    session.commit()
    session.refresh(signal)

    subscription = AlertSubscriptionRecord(
        user_id=user.id,
        channel="telegram",
        is_active=True,
        telegram_chat_id="123456789",
    )
    session.add(subscription)
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            enable_confluence_engine=False,
            alert_on_individual_signals=True,
        ),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-2"},
    )

    result = process_alert_pipeline(
        session,
        [signal],
        detected_signals=[build_signal_payload("volume_spike")],
        market_snapshots=[base_snapshot()],
    )

    assert result["sent"] == 1
    assert len(calls) == 1
    assert result["individual_signals_sent"] == 1


def test_hybrid_mode_prioritizes_setup_over_individual_components(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    volume_spike = build_persisted_signal("volume_spike")
    volume_spike.asset_id = asset.id
    range_breakout = build_persisted_signal("range_breakout")
    range_breakout.asset_id = asset.id
    session.add_all([volume_spike, range_breakout])
    session.commit()
    session.refresh(volume_spike)
    session.refresh(range_breakout)

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(alert_engine, "get_settings", lambda: make_alert_settings(alert_on_individual_signals=True))
    monkeypatch.setattr(
        setup_view,
        "get_settings",
        lambda: SimpleNamespace(setup_require_no_mock_for_executable=True),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-setup"},
    )

    result = process_alert_pipeline(
        session,
        [volume_spike, range_breakout],
        market_snapshots=[base_snapshot()],
    )

    assert result["setups_sent"] == 1
    assert result["individual_signals_sent"] == 0
    assert result["skip_reasons"]["skipped_due_to_setup_priority"] >= 1
    assert len(calls) == 1
    assert "SETUP PRO" in calls[0]


def test_hybrid_mode_sends_individual_signal_when_no_setup_exists(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal = build_persisted_signal("volume_spike")
    signal.asset_id = asset.id
    session.add(signal)
    session.commit()
    session.refresh(signal)

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(alert_engine, "get_settings", lambda: make_alert_settings(alert_on_individual_signals=True))
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-signal"},
    )

    result = process_alert_pipeline(
        session,
        [signal],
        market_snapshots=[base_snapshot()],
    )

    assert result["setups_sent"] == 0
    assert result["individual_signals_sent"] == 1
    assert len(calls) == 1
    assert "SEÑAL TEMPRANA" in calls[0]


def test_hybrid_mode_setup_pro_is_not_affected_by_early_signal_limits(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    volume_spike = build_persisted_signal("volume_spike")
    volume_spike.asset_id = asset.id
    range_breakout = build_persisted_signal("range_breakout")
    range_breakout.asset_id = asset.id
    session.add_all([volume_spike, range_breakout])
    session.commit()

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            alert_on_individual_signals=True,
            early_signal_min_score=9.9,
            early_signal_min_confidence=0.99,
            early_signal_max_per_run=1,
            early_signal_cooldown_hours=24,
        ),
    )
    monkeypatch.setattr(
        setup_view,
        "get_settings",
        lambda: SimpleNamespace(setup_require_no_mock_for_executable=True),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-setup-priority"},
    )

    result = process_alert_pipeline(
        session,
        [volume_spike, range_breakout],
        market_snapshots=[base_snapshot()],
    )

    assert result["setups_sent"] == 1
    assert result["individual_signals_sent"] == 0
    assert len(calls) == 1
    assert "SETUP PRO" in calls[0]


def test_hybrid_mode_blocks_early_signal_with_stricter_specific_threshold(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal = build_persisted_signal("volume_spike", score=7.0, confidence=70.0)
    signal.asset_id = asset.id
    session.add(signal)
    session.commit()
    session.refresh(signal)

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
            min_score=6.5,
            min_confidence=0.55,
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            alert_on_individual_signals=True,
            early_signal_min_score=7.2,
            early_signal_min_confidence=0.65,
        ),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-none"},
    )

    result = process_alert_pipeline(
        session,
        [signal],
        market_snapshots=[base_snapshot()],
    )

    assert result["sent"] == 0
    assert result["individual_signals_sent"] == 0
    assert result["skip_reasons"]["skipped_threshold"] >= 1
    assert calls == []


def test_hybrid_mode_does_not_send_individual_signal_below_threshold(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal = build_persisted_signal("volume_spike")
    signal.asset_id = asset.id
    signal.score = 6.0
    signal.confidence = 50.0
    session.add(signal)
    session.commit()
    session.refresh(signal)

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
            min_score=6.5,
            min_confidence=0.55,
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(alert_engine, "get_settings", lambda: make_alert_settings(alert_on_individual_signals=True))
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-none"},
    )

    result = process_alert_pipeline(
        session,
        [signal],
        market_snapshots=[base_snapshot()],
    )

    assert result["sent"] == 0
    assert calls == []


def test_hybrid_mode_blocks_early_signal_by_asset_cooldown(monkeypatch) -> None:
    session = build_session()
    now = datetime.now(timezone.utc)
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    previous_signal = build_persisted_signal("range_breakout", asset_symbol="BTC", created_at=now - timedelta(hours=1))
    previous_signal.asset_id = asset.id
    current_signal = build_persisted_signal("volume_spike", asset_symbol="BTC", created_at=now)
    current_signal.asset_id = asset.id
    session.add_all([previous_signal, current_signal])
    session.commit()
    session.refresh(previous_signal)
    session.refresh(current_signal)

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    session.add(
        AlertDeliveryRecord(
            signal_id=previous_signal.id,
            user_id=user.id,
            channel="telegram",
            delivery_status="sent",
            provider_message_id="old-message",
            sent_at=now - timedelta(hours=1),
            created_at=now - timedelta(hours=1),
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            alert_on_individual_signals=True,
            early_signal_cooldown_hours=8,
        ),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-cooldown"},
    )

    result = process_alert_pipeline(
        session,
        [current_signal],
        market_snapshots=[base_snapshot()],
    )

    assert result["sent"] == 0
    assert result["individual_signals_sent"] == 0
    assert result["skip_reasons"]["skipped_early_signal_cooldown"] >= 1
    assert calls == []


def test_hybrid_mode_respects_dedupe_for_individual_signal(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    asset = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    session.add_all([user, asset])
    session.commit()
    session.refresh(user)
    session.refresh(asset)

    signal = build_persisted_signal("volume_spike")
    signal.asset_id = asset.id
    session.add(signal)
    session.commit()
    session.refresh(signal)

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            alert_on_individual_signals=True,
            early_signal_cooldown_hours=0,
        ),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-dedupe"},
    )

    first = process_alert_pipeline(
        session,
        [signal],
        market_snapshots=[base_snapshot()],
    )
    second = process_alert_pipeline(
        session,
        [signal],
        market_snapshots=[base_snapshot()],
    )

    assert first["individual_signals_sent"] == 1
    assert second["individual_signals_sent"] == 0
    assert second["skip_reasons"]["skipped_duplicate"] >= 1


def test_hybrid_mode_caps_early_signals_per_run(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    btc = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    eth = AssetRecord(symbol="ETH", name="Ethereum", category="Layer 1")
    sol = AssetRecord(symbol="SOL", name="Solana", category="Layer 1")
    session.add_all([user, btc, eth, sol])
    session.commit()
    session.refresh(user)
    session.refresh(btc)
    session.refresh(eth)
    session.refresh(sol)

    btc_signal = build_persisted_signal("volume_spike", asset_symbol="BTC", score=8.9, confidence=84.0)
    btc_signal.asset_id = btc.id
    eth_signal = build_persisted_signal("volume_spike", asset_symbol="ETH", score=8.6, confidence=82.0)
    eth_signal.asset_id = eth.id
    sol_signal = build_persisted_signal("volume_spike", asset_symbol="SOL", score=8.2, confidence=80.0)
    sol_signal.asset_id = sol.id
    session.add_all([btc_signal, eth_signal, sol_signal])
    session.commit()

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            alert_on_individual_signals=True,
            early_signal_max_per_run=2,
        ),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": f"m-{len(calls)}"},
    )

    result = process_alert_pipeline(
        session,
        [btc_signal, eth_signal, sol_signal],
        market_snapshots=[
            base_snapshot(),
            base_snapshot(symbol="ETH", name="Ethereum", price_usd=3520.0),
            base_snapshot(symbol="SOL", name="Solana", price_usd=142.0),
        ],
    )

    assert result["setups_sent"] == 0
    assert result["individual_signals_sent"] == 2
    assert len(calls) == 2
    assert result["skip_reasons"]["skipped_early_signal_cap"] >= 1


def test_hybrid_mode_ranks_early_signals_by_score_then_confidence(monkeypatch) -> None:
    session = build_session()
    user = UserRecord(email="pro@example.com", password_hash="hash", plan="pro", is_active=True)
    btc = AssetRecord(symbol="BTC", name="Bitcoin", category="Layer 1")
    eth = AssetRecord(symbol="ETH", name="Ethereum", category="Layer 1")
    session.add_all([user, btc, eth])
    session.commit()
    session.refresh(user)
    session.refresh(btc)
    session.refresh(eth)

    btc_signal = build_persisted_signal("volume_spike", asset_symbol="BTC", score=8.4, confidence=72.0)
    btc_signal.asset_id = btc.id
    eth_signal = build_persisted_signal("volume_spike", asset_symbol="ETH", score=8.4, confidence=90.0)
    eth_signal.asset_id = eth.id
    session.add_all([btc_signal, eth_signal])
    session.commit()

    session.add(
        AlertSubscriptionRecord(
            user_id=user.id,
            channel="telegram",
            is_active=True,
            telegram_chat_id="123456789",
        )
    )
    session.commit()

    calls: list[str] = []
    monkeypatch.setattr(
        alert_engine,
        "get_settings",
        lambda: make_alert_settings(
            alert_on_individual_signals=True,
            early_signal_max_per_run=1,
        ),
    )
    monkeypatch.setattr(
        alert_engine,
        "send_telegram_message",
        lambda chat_id, text: calls.append(text) or {"message_id": "m-ranked"},
    )

    result = process_alert_pipeline(
        session,
        [btc_signal, eth_signal],
        market_snapshots=[
            base_snapshot(),
            base_snapshot(symbol="ETH", name="Ethereum", price_usd=3520.0),
        ],
    )

    assert result["individual_signals_sent"] == 1
    assert len(calls) == 1
    assert "ETH" in calls[0]
    assert "BTC" not in calls[0]
