from __future__ import annotations

from typing import Any

from scoring import clamp, normalize

MarketSnapshot = dict[str, Any]
SignalPayload = dict[str, Any]


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_confidence(value: Any) -> float:
    numeric = _coerce_float(value)
    if 0.0 <= numeric <= 1.0:
        numeric *= 100.0
    return clamp(numeric / 100.0, 0.0, 1.0)


def _snapshot_source(snapshot: MarketSnapshot | None) -> str:
    return str((snapshot or {}).get("source", "")).lower()


def build_quality_flags(
    signals: list[SignalPayload],
    snapshot: MarketSnapshot | None = None,
) -> dict[str, bool]:
    raw_payload = (snapshot or {}).get("raw_payload") or {}
    signal_timeframes = {str(signal.get("timeframe", "")).upper() for signal in signals if signal.get("timeframe")}
    snapshot_timeframe = str((snapshot or {}).get("timeframe", "")).upper()
    signal_sources = [str(signal.get("source", "")) for signal in signals]

    has_real_oi = bool(
        raw_payload.get("bybit", {}).get("open_interest") or raw_payload.get("binance", {}).get("open_interest")
    )
    has_real_liquidations = bool(raw_payload.get("coinglass", {}).get("liquidations"))

    return {
        "snapshot_missing": snapshot is None,
        "mock_contamination": "mock" in _snapshot_source(snapshot)
        or any("mock" in source.lower() for source in signal_sources),
        "oi_inferred": snapshot is not None and not has_real_oi,
        "liquidations_unverified": any(signal.get("signal_key") == "liquidation_cluster" for signal in signals)
        and not has_real_liquidations,
        "timeframe_misaligned": bool(signal_timeframes)
        and bool(snapshot_timeframe)
        and any(timeframe != snapshot_timeframe for timeframe in signal_timeframes),
    }


def _market_context_score(snapshot: MarketSnapshot | None = None) -> float:
    if snapshot is None:
        return 0.35

    volume_24h = _coerce_float(snapshot.get("volume_24h"))
    avg_volume_24h = _coerce_float(snapshot.get("avg_volume_24h"))
    volume_ratio = volume_24h / avg_volume_24h if avg_volume_24h > 0 else 0.0

    components = {
        "volume": normalize(volume_ratio, 1.0, 2.8),
        "momentum": normalize(abs(_coerce_float(snapshot.get("momentum_score"))), 55.0, 90.0),
        "price_move": normalize(abs(_coerce_float(snapshot.get("change_24h"))), 0.8, 6.0),
        "oi_move": normalize(abs(_coerce_float(snapshot.get("oi_change_24h"))), 2.0, 12.0),
        "funding": max(
            normalize(abs(_coerce_float(snapshot.get("funding_rate"))), 0.005, 0.03),
            normalize(abs(_coerce_float(snapshot.get("funding_zscore"))), 1.0, 3.5),
        ),
    }

    return clamp(
        (
            (components["volume"] * 0.25)
            + (components["momentum"] * 0.25)
            + (components["price_move"] * 0.20)
            + (components["oi_move"] * 0.15)
            + (components["funding"] * 0.15)
        ),
        0.0,
        1.0,
    )


def _confluence_bonus(signals: list[SignalPayload], setup_key: str | None = None) -> float:
    unique_keys = {str(signal.get("signal_key", "")) for signal in signals}
    directions = {str(signal.get("direction", "neutral")) for signal in signals}
    aligned = len(directions) == 1
    bonus = 0.30 + (0.18 * max(len(unique_keys) - 1, 0))

    if aligned:
        bonus += 0.20

    if setup_key == "trend_continuation" and {"volume_spike", "range_breakout"}.issubset(unique_keys):
        bonus += 0.15
    elif setup_key == "squeeze_reversal" and {"funding_extreme", "liquidation_cluster"}.issubset(unique_keys):
        bonus += 0.18
    elif setup_key == "positioning_trap" and "oi_divergence" in unique_keys:
        bonus += 0.12
        if "funding_extreme" in unique_keys:
            bonus += 0.08
        if "range_breakout" in unique_keys:
            bonus += 0.05

    return clamp(bonus, 0.0, 1.0)


def _score_penalty_points(flags: dict[str, bool]) -> float:
    penalty = 0.0
    if flags.get("snapshot_missing"):
        penalty += 1.6
    if flags.get("mock_contamination"):
        penalty += 2.0
    if flags.get("liquidations_unverified"):
        penalty += 0.6
    if flags.get("oi_inferred"):
        penalty += 0.4
    return penalty


def _confidence_penalty_points(flags: dict[str, bool]) -> float:
    penalty = 0.0
    if flags.get("snapshot_missing"):
        penalty += 14.0
    if flags.get("mock_contamination"):
        penalty += 18.0
    if flags.get("liquidations_unverified"):
        penalty += 6.0
    if flags.get("oi_inferred"):
        penalty += 5.0
    if flags.get("timeframe_misaligned"):
        penalty += 4.0
    return penalty


def calculate_setup_score(
    signals: list[SignalPayload],
    snapshot: MarketSnapshot | None = None,
    *,
    setup_key: str | None = None,
) -> float:
    if not signals:
        return 1.0

    avg_signal_score = sum(clamp(_coerce_float(signal.get("score")) / 10.0) for signal in signals) / len(signals)
    avg_confidence = sum(_normalize_confidence(signal.get("confidence")) for signal in signals) / len(signals)
    context_score = _market_context_score(snapshot)
    confluence_bonus = _confluence_bonus(signals, setup_key)
    raw_score = (
        (avg_signal_score * 0.50)
        + (avg_confidence * 0.20)
        + (context_score * 0.20)
        + (confluence_bonus * 0.10)
    )
    score = 1.0 + (clamp(raw_score) * 9.0)
    quality_flags = build_quality_flags(signals, snapshot)
    return round(clamp(score - _score_penalty_points(quality_flags), 1.0, 10.0), 1)


def calculate_setup_confidence(
    signals: list[SignalPayload],
    snapshot: MarketSnapshot | None = None,
    *,
    setup_key: str | None = None,
) -> float:
    if not signals:
        return 35.0

    avg_confidence = sum(_normalize_confidence(signal.get("confidence")) for signal in signals) / len(signals)
    avg_score = sum(clamp(_coerce_float(signal.get("score")) / 10.0) for signal in signals) / len(signals)
    direction_alignment = 1.0 if len({str(signal.get("direction", "neutral")) for signal in signals}) == 1 else 0.4
    structure_bonus = _confluence_bonus(signals, setup_key)
    context_score = _market_context_score(snapshot)
    confidence = 35.0 + (
        clamp(
            (avg_confidence * 0.55)
            + (avg_score * 0.15)
            + (direction_alignment * 0.15)
            + (context_score * 0.10)
            + (structure_bonus * 0.05)
        )
        * 63.0
    )
    quality_flags = build_quality_flags(signals, snapshot)
    return round(clamp(confidence - _confidence_penalty_points(quality_flags), 20.0, 98.0), 1)
