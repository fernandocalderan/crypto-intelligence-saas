from formatter import MarketSnapshot, SignalPayload, format_signal
from scoring import calculate_score, normalize


def detect(data: MarketSnapshot) -> SignalPayload | None:
    funding_rate = float(data["funding_rate"])
    funding_zscore = abs(float(data["funding_zscore"]))
    oi_change = abs(float(data["oi_change_24h"]))

    if abs(funding_rate) < 0.02 or funding_zscore < 2.0:
        return None

    direction = "bearish" if funding_rate > 0 else "bullish"
    crowd_side = "longs" if funding_rate > 0 else "shorts"

    score = calculate_score(
        {
            "funding_rate": normalize(abs(funding_rate), 0.02, 0.05),
            "funding_zscore": normalize(funding_zscore, 2.0, 4.0),
            "oi_change": normalize(oi_change, 4.0, 15.0),
        },
        weights={
            "funding_rate": 0.4,
            "funding_zscore": 0.35,
            "oi_change": 0.25,
        },
    )

    evidence = [
        f"funding rate {funding_rate:+.4f}",
        f"funding z-score {funding_zscore:.1f}",
        f"OI change {float(data['oi_change_24h']):+.1f}%",
    ]

    thesis = (
        f"{data['symbol']} muestra un extremo de funding con mercado demasiado cargado en "
        f"{crowd_side}, lo que abre la puerta a reversión o squeeze en sentido contrario."
    )

    return format_signal(
        signal_key="funding_extreme",
        signal_type="Funding Extreme",
        data=data,
        direction=direction,
        score=score,
        thesis=thesis,
        evidence=evidence,
        timeframe="8H",
    )

