from datetime import datetime, timezone
from typing import Any

from scoring import score_to_confidence

MarketSnapshot = dict[str, Any]
SignalPayload = dict[str, Any]


def format_signal(
    *,
    signal_key: str,
    signal_type: str,
    data: MarketSnapshot,
    direction: str,
    score: float,
    thesis: str,
    evidence: list[str],
    timeframe: str | None = None,
    source: str | None = None,
) -> SignalPayload:
    asset_symbol = str(data["symbol"])
    generated_at = data.get("generated_at") or datetime.now(timezone.utc).isoformat()

    return {
        "id": f"sig-{asset_symbol.lower()}-{signal_key}",
        "signal_key": signal_key,
        "asset_symbol": asset_symbol,
        "signal_type": signal_type,
        "timeframe": timeframe or str(data.get("timeframe", "4H")),
        "direction": direction,
        "score": round(score, 1),
        "confidence": score_to_confidence(score, len(evidence)),
        "thesis": thesis,
        "evidence": evidence,
        "source": source or str(data.get("source", "mock")),
        "generated_at": generated_at,
    }

