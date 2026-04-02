from formatter import MarketSnapshot, SignalPayload, format_signal
from scoring import calculate_score, normalize


def detect(data: MarketSnapshot) -> SignalPayload | None:
    price_change = float(data["change_24h"])
    oi_change = float(data["oi_change_24h"])
    divergence = abs(oi_change - price_change)

    bullish_setup = price_change <= -1.0 and oi_change >= 6.0
    bearish_setup = price_change >= 1.0 and oi_change <= -5.0

    if not bullish_setup and not bearish_setup:
        return None

    direction = "bullish" if bullish_setup else "bearish"

    score = calculate_score(
        {
            "divergence": normalize(divergence, 6.0, 15.0),
            "oi_change": normalize(abs(oi_change), 5.0, 12.0),
            "price_change": normalize(abs(price_change), 1.0, 5.0),
        },
        weights={
            "divergence": 0.5,
            "oi_change": 0.3,
            "price_change": 0.2,
        },
    )

    evidence = [
        f"price change {price_change:+.1f}%",
        f"OI change {oi_change:+.1f}%",
        f"divergence spread {divergence:.1f} points",
    ]

    thesis = (
        f"{data['symbol']} presenta divergencia entre precio y open interest, una señal "
        "de posicionamiento desequilibrado que suele anticipar squeeze o fallo del movimiento."
    )

    return format_signal(
        signal_key="oi_divergence",
        signal_type="OI Divergence",
        data=data,
        direction=direction,
        score=score,
        thesis=thesis,
        evidence=evidence,
        timeframe="4H",
    )

