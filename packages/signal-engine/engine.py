from collections.abc import Callable

from formatter import MarketSnapshot, SignalPayload
from funding_extreme import detect as detect_funding_extreme
from liquidation_cluster import detect as detect_liquidation_cluster
from oi_divergence import detect as detect_oi_divergence
from range_breakout import detect as detect_range_breakout
from volume_spike import detect as detect_volume_spike

Detector = Callable[[MarketSnapshot], SignalPayload | None]

DETECTORS: list[tuple[str, Detector]] = [
    ("volume_spike", detect_volume_spike),
    ("range_breakout", detect_range_breakout),
    ("funding_extreme", detect_funding_extreme),
    ("oi_divergence", detect_oi_divergence),
    ("liquidation_cluster", detect_liquidation_cluster),
]


def detect_active_signals(
    market_data: list[MarketSnapshot], enabled_signals: dict[str, bool] | None = None
) -> list[SignalPayload]:
    active_signals: list[SignalPayload] = []
    seen: set[tuple[str, str, str]] = set()
    flags = enabled_signals or {}

    for snapshot in market_data:
        for detector_key, detector in DETECTORS:
            if not flags.get(detector_key, True):
                continue

            signal = detector(snapshot)
            if signal is None:
                continue

            signature = (
                str(signal["asset_symbol"]),
                str(signal["signal_key"]),
                str(signal["timeframe"]),
            )

            if signature in seen:
                continue

            seen.add(signature)
            active_signals.append(signal)

    active_signals.sort(
        key=lambda signal: (float(signal["score"]), float(signal["confidence"])),
        reverse=True,
    )

    return active_signals

