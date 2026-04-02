from formatter import MarketSnapshot, SignalPayload, format_signal
from scoring import calculate_score, normalize


def detect(data: MarketSnapshot) -> SignalPayload | None:
    volume_ratio = float(data["volume_24h"]) / float(data["avg_volume_24h"])
    price_change = float(data["change_24h"])

    if volume_ratio < 1.8 or abs(price_change) < 1.5:
        return None

    score = calculate_score(
        {
            "volume_ratio": normalize(volume_ratio, 1.8, 3.5),
            "price_change": normalize(abs(price_change), 1.5, 6.0),
            "momentum": normalize(float(data["momentum_score"]), 55.0, 90.0),
        },
        weights={
            "volume_ratio": 0.5,
            "price_change": 0.25,
            "momentum": 0.25,
        },
    )

    direction = "bullish" if price_change > 0 else "bearish"
    evidence = [
        f"volume ratio {volume_ratio:.2f}x over baseline",
        f"24h price change {price_change:+.1f}%",
        f"momentum score {float(data['momentum_score']):.1f}",
    ]

    thesis = (
        f"{data['symbol']} imprime un spike de volumen con expansión direccional, "
        "lo que sugiere entrada de flujo nuevo y continuación táctica."
    )

    return format_signal(
        signal_key="volume_spike",
        signal_type="Volume Spike",
        data=data,
        direction=direction,
        score=score,
        thesis=thesis,
        evidence=evidence,
        timeframe="4H",
    )

