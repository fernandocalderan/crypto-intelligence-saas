from datetime import datetime, timezone

from services.pro_signal_view import build_pro_signal_view
from services.telegram_service import format_pro_telegram_alert


def base_signal(**overrides):
    payload = {
        "id": "sig-btc-volume",
        "signal_key": "volume_spike",
        "asset_symbol": "BTC",
        "signal_type": "Volume Spike",
        "timeframe": "4H",
        "direction": "bullish",
        "score": 8.6,
        "confidence": 82.0,
        "thesis": "BTC imprime un spike de volumen con expansión direccional y entrada de flujo nuevo.",
        "evidence": ["volume ratio 2.1x over baseline", "24h price change +3.4%", "momentum score 84.2"],
        "source": "binance+bybit",
        "generated_at": datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
    }
    payload.update(overrides)
    return payload


def base_snapshot(**overrides):
    payload = {
        "symbol": "BTC",
        "source": "binance+bybit",
        "timeframe": "1D",
        "price_usd": 68420.45,
        "change_24h": 3.4,
        "volume_24h": 31_200_000_000,
        "avg_volume_24h": 16_800_000_000,
        "range_high_20d": 69500.0,
        "range_low_20d": 61200.0,
        "funding_rate": 0.009,
        "funding_zscore": 1.1,
        "open_interest": 14_800_000_000,
        "oi_change_24h": 4.2,
        "long_liquidations_1h": 8_400_000,
        "short_liquidations_1h": 5_200_000,
        "avg_liquidations_1h": 7_500_000,
        "momentum_score": 84.2,
        "captured_at": datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        "raw_payload": {
            "binance": {"open_interest": {"open_interest": 14_800_000_000}},
            "bybit": {"open_interest": {"open_interest": 14_800_000_000}},
            "coinglass": {"liquidations": {"long_liquidations_1h": 8_400_000}},
        },
    }
    payload.update(overrides)
    return payload


def test_low_score_signal_is_discarded() -> None:
    signal = base_signal(score=5.4, confidence=49.0)
    view = build_pro_signal_view(signal, base_snapshot(), plan="pro")

    assert view.execution_state == "DISCARD"
    assert view.is_trade_executable is False
    assert view.action_plan is not None
    assert view.action_plan.action_now == "discard"


def test_partial_signal_waits_for_confirmation() -> None:
    signal = base_signal(score=6.9, confidence=63.0, signal_key="oi_divergence", signal_type="OI Divergence")
    snapshot = base_snapshot(change_24h=-1.4, oi_change_24h=5.5, source="binance+bybit")
    view = build_pro_signal_view(signal, snapshot, plan="pro")

    assert view.execution_state == "WAIT_CONFIRMATION"
    assert view.is_trade_executable is False
    assert any(item.severity == "warning" for item in view.confirmations)


def test_strong_clean_signal_is_executable() -> None:
    view = build_pro_signal_view(base_signal(), base_snapshot(), plan="pro")

    assert view.execution_state == "EXECUTABLE"
    assert view.is_trade_executable is True
    assert view.action_plan is not None
    assert view.action_plan.action_now == "enter"


def test_mock_contamination_never_becomes_executable() -> None:
    view = build_pro_signal_view(
        base_signal(score=8.9, confidence=88.0, source="binance+bybit+mock"),
        base_snapshot(source="binance+bybit+mock"),
        plan="pro",
    )

    assert view.is_mock_contaminated is True
    assert view.execution_state != "EXECUTABLE"
    assert any(item.code == "mock_contamination" for item in view.data_quality_warnings)


def test_telegram_pro_formatter_includes_state_plan_and_warnings() -> None:
    view = build_pro_signal_view(
        base_signal(source="binance+mock"),
        base_snapshot(source="binance+mock"),
        plan="pro",
    )
    message = format_pro_telegram_alert(view, plan="pro")

    assert "BTC — Volume Spike" in message
    assert "PRO" in message
    assert "Score:" in message
    assert "Estado:" in message
    assert "Plan:" in message
    assert "Riesgo / calidad del dato:" in message
