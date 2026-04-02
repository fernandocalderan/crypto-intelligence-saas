from formatter import MarketSnapshot, SignalPayload, format_signal
from scoring import calculate_score, normalize


def detect(data: MarketSnapshot) -> SignalPayload | None:
    long_liquidations = float(data["long_liquidations_1h"])
    short_liquidations = float(data["short_liquidations_1h"])
    average_liquidations = float(data["avg_liquidations_1h"])
    total_liquidations = long_liquidations + short_liquidations

    if average_liquidations <= 0:
        return None

    cluster_ratio = total_liquidations / average_liquidations
    dominance = max(long_liquidations, short_liquidations) / total_liquidations

    if cluster_ratio < 2.5 or dominance < 0.68:
        return None

    dominant_side = "longs" if long_liquidations > short_liquidations else "shorts"
    direction = "bullish" if dominant_side == "longs" else "bearish"

    score = calculate_score(
        {
            "cluster_ratio": normalize(cluster_ratio, 2.5, 5.0),
            "dominance": normalize(dominance, 0.68, 0.9),
            "momentum": normalize(abs(float(data["change_24h"])), 0.5, 4.0),
        },
        weights={
            "cluster_ratio": 0.45,
            "dominance": 0.35,
            "momentum": 0.20,
        },
    )

    evidence = [
        f"liquidation ratio {cluster_ratio:.2f}x",
        f"dominant side {dominant_side}",
        f"1h liquidations ${total_liquidations / 1_000_000:.1f}M",
    ]

    thesis = (
        f"{data['symbol']} registra un cluster de liquidaciones en {dominant_side}, "
        "lo que suele limpiar posicionamiento y dejar una reversión táctica operable."
    )

    return format_signal(
        signal_key="liquidation_cluster",
        signal_type="Liquidation Cluster",
        data=data,
        direction=direction,
        score=score,
        thesis=thesis,
        evidence=evidence,
        timeframe="1H",
    )

