from formatter import MarketSnapshot, SignalPayload, format_signal
from scoring import calculate_score, normalize


def detect(data: MarketSnapshot) -> SignalPayload | None:
    price = float(data["price_usd"])
    range_high = float(data["range_high_20d"])
    range_low = float(data["range_low_20d"])
    volume_ratio = float(data["volume_24h"]) / float(data["avg_volume_24h"])

    breakout_above = (price - range_high) / range_high
    breakout_below = (range_low - price) / range_low

    if breakout_above < 0.004 and breakout_below < 0.004:
        return None

    bullish = breakout_above >= breakout_below
    breakout_strength = breakout_above if bullish else breakout_below
    direction = "bullish" if bullish else "bearish"

    score = calculate_score(
        {
            "breakout_strength": normalize(breakout_strength, 0.004, 0.025),
            "volume_ratio": normalize(volume_ratio, 1.2, 2.0),
            "price_change": normalize(abs(float(data["change_24h"])), 1.0, 5.0),
        },
        weights={
            "breakout_strength": 0.45,
            "volume_ratio": 0.35,
            "price_change": 0.20,
        },
    )

    reference_range = range_high if bullish else range_low
    evidence = [
        f"breakout margin {(breakout_strength * 100):.2f}% from 20d range",
        f"range reference {reference_range:.2f}",
        f"volume ratio {volume_ratio:.2f}x",
    ]

    thesis = (
        f"{data['symbol']} sale de su rango de 20 días con confirmación de precio y "
        "volumen suficiente para considerarlo ruptura operable."
    )

    return format_signal(
        signal_key="range_breakout",
        signal_type="Range Breakout",
        data=data,
        direction=direction,
        score=score,
        thesis=thesis,
        evidence=evidence,
        timeframe="4H",
    )

