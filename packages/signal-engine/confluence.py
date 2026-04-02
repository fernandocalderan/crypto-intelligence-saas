from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from formatter import MarketSnapshot, SignalPayload
from setup_scoring import build_quality_flags, calculate_setup_confidence, calculate_setup_score

ConfluenceSetup = dict[str, Any]


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return datetime.now(timezone.utc)


def group_signals_by_asset(signals: list[SignalPayload]) -> dict[str, list[SignalPayload]]:
    grouped: dict[str, list[SignalPayload]] = {}
    for signal in signals:
        symbol = str(signal.get("asset_symbol", "")).upper()
        if not symbol:
            continue
        grouped.setdefault(symbol, []).append(signal)

    for bucket in grouped.values():
        bucket.sort(
            key=lambda signal: (float(signal.get("score", 0.0)), float(signal.get("confidence", 0.0))),
            reverse=True,
        )

    return grouped


def _snapshot_index(market_snapshots: list[MarketSnapshot] | None = None) -> dict[str, MarketSnapshot]:
    return {str(snapshot.get("symbol", "")).upper(): snapshot for snapshot in (market_snapshots or [])}


def _best_signal(
    signals: list[SignalPayload],
    signal_key: str,
    *,
    direction: str | None = None,
) -> SignalPayload | None:
    candidates = [
        signal
        for signal in signals
        if str(signal.get("signal_key")) == signal_key
        and (direction is None or str(signal.get("direction")) == direction)
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda signal: (float(signal.get("score", 0.0)), float(signal.get("confidence", 0.0))),
    )


def _opposite_direction(direction: str) -> str:
    if direction == "bullish":
        return "bearish"
    if direction == "bearish":
        return "bullish"
    return "neutral"


def _breakout_failure_context(
    oi_signal: SignalPayload,
    signals: list[SignalPayload],
    snapshot: MarketSnapshot | None,
) -> SignalPayload | None:
    opposite_breakout = _best_signal(signals, "range_breakout", direction=_opposite_direction(str(oi_signal.get("direction"))))
    if opposite_breakout is None or snapshot is None:
        return None

    price_change = float(snapshot.get("change_24h", 0.0))
    oi_direction = str(oi_signal.get("direction", "neutral"))
    if oi_direction == "bullish" and price_change >= 0:
        return opposite_breakout
    if oi_direction == "bearish" and price_change <= 0:
        return opposite_breakout
    return None


def _build_setup(
    *,
    setup_key: str,
    setup_type: str,
    asset_symbol: str,
    direction: str,
    signals: list[SignalPayload],
    snapshot: MarketSnapshot | None,
    notes: list[str] | None = None,
) -> ConfluenceSetup:
    generated_at = max(
        (_coerce_datetime(signal.get("generated_at")) for signal in signals),
        default=datetime.now(timezone.utc),
    )
    quality_flags = build_quality_flags(signals, snapshot)

    return {
        "setup_key": setup_key,
        "setup_type": setup_type,
        "asset_symbol": asset_symbol,
        "direction": direction,
        "signal_keys": [str(signal.get("signal_key", "")) for signal in signals],
        "signals": signals,
        "score": calculate_setup_score(signals, snapshot, setup_key=setup_key),
        "confidence": calculate_setup_confidence(signals, snapshot, setup_key=setup_key),
        "quality_flags": quality_flags,
        "market_context": snapshot or {},
        "notes": notes or [],
        "generated_at": generated_at,
        "source_snapshot_time": (snapshot or {}).get("captured_at"),
        "summary": None,
        "thesis": None,
        "confirmations": [],
        "data_quality_warnings": [],
        "action_plan": None,
        "execution_state": None,
        "execution_reason": None,
        "is_mock_contaminated": bool(quality_flags.get("mock_contamination") or quality_flags.get("snapshot_missing")),
        "is_trade_executable": False,
    }


def detect_confluence_setups(
    signals_by_asset: dict[str, list[SignalPayload]],
    market_snapshots: list[MarketSnapshot] | None = None,
) -> list[ConfluenceSetup]:
    snapshots = _snapshot_index(market_snapshots)
    setups: list[ConfluenceSetup] = []

    for asset_symbol, asset_signals in signals_by_asset.items():
        snapshot = snapshots.get(asset_symbol)
        directions = {str(signal.get("direction", "neutral")) for signal in asset_signals}

        for direction in directions:
            volume_spike = _best_signal(asset_signals, "volume_spike", direction=direction)
            range_breakout = _best_signal(asset_signals, "range_breakout", direction=direction)
            if volume_spike is not None and range_breakout is not None:
                setups.append(
                    _build_setup(
                        setup_key="trend_continuation",
                        setup_type="Trend Continuation",
                        asset_symbol=asset_symbol,
                        direction=direction,
                        signals=[volume_spike, range_breakout],
                        snapshot=snapshot,
                        notes=["Confluencia válida: volume_spike + range_breakout."],
                    )
                )

            funding_extreme = _best_signal(asset_signals, "funding_extreme", direction=direction)
            liquidation_cluster = _best_signal(asset_signals, "liquidation_cluster", direction=direction)
            if funding_extreme is not None and liquidation_cluster is not None:
                setups.append(
                    _build_setup(
                        setup_key="squeeze_reversal",
                        setup_type="Squeeze Reversal",
                        asset_symbol=asset_symbol,
                        direction=direction,
                        signals=[funding_extreme, liquidation_cluster],
                        snapshot=snapshot,
                        notes=["Confluencia válida: funding_extreme + liquidation_cluster."],
                    )
                )

        oi_divergence = _best_signal(asset_signals, "oi_divergence")
        if oi_divergence is not None:
            trap_signals = [oi_divergence]
            notes = ["Base de setup: oi_divergence."]
            same_direction_funding = _best_signal(
                asset_signals,
                "funding_extreme",
                direction=str(oi_divergence.get("direction")),
            )
            if same_direction_funding is not None:
                trap_signals.append(same_direction_funding)
                notes.append("Bonus de prioridad: funding_extreme acompaña la divergencia.")

            failed_breakout = _breakout_failure_context(oi_divergence, asset_signals, snapshot)
            if failed_breakout is not None:
                trap_signals.append(failed_breakout)
                notes.append("Contexto adicional: breakout opuesto muestra síntomas de fallo.")

            deduped_trap_signals: list[SignalPayload] = []
            seen_component_keys: set[str] = set()
            for signal in trap_signals:
                key = f"{signal.get('signal_key')}:{signal.get('direction')}"
                if key in seen_component_keys:
                    continue
                seen_component_keys.add(key)
                deduped_trap_signals.append(signal)

            setups.append(
                _build_setup(
                    setup_key="positioning_trap",
                    setup_type="Positioning Trap",
                    asset_symbol=asset_symbol,
                    direction=str(oi_divergence.get("direction", "neutral")),
                    signals=deduped_trap_signals,
                    snapshot=snapshot,
                    notes=notes,
                )
            )

    setups.sort(
        key=lambda setup: (float(setup.get("score", 0.0)), float(setup.get("confidence", 0.0))),
        reverse=True,
    )
    return setups
