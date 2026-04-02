from datetime import datetime, timezone
from typing import Any


DEFAULT_MARKET_BASELINES: dict[str, dict[str, Any]] = {
    "BTC": {
        "name": "Bitcoin",
        "category": "Layer 1",
        "price_usd": 68420.45,
        "change_24h": 3.4,
        "volume_24h": 31_200_000_000,
        "avg_volume_24h": 16_800_000_000,
        "range_high_20d": 69_500.00,
        "range_low_20d": 61_200.00,
        "funding_rate": 0.009,
        "funding_zscore": 1.1,
        "open_interest": 14_800_000_000,
        "oi_change_24h": 4.2,
        "long_liquidations_1h": 8_400_000,
        "short_liquidations_1h": 5_200_000,
        "avg_liquidations_1h": 7_500_000,
        "momentum_score": 84.2,
    },
    "ETH": {
        "name": "Ethereum",
        "category": "Layer 1",
        "price_usd": 3628.18,
        "change_24h": 2.1,
        "volume_24h": 18_600_000_000,
        "avg_volume_24h": 12_800_000_000,
        "range_high_20d": 3588.00,
        "range_low_20d": 3010.00,
        "funding_rate": 0.011,
        "funding_zscore": 1.2,
        "open_interest": 8_200_000_000,
        "oi_change_24h": 3.0,
        "long_liquidations_1h": 6_900_000,
        "short_liquidations_1h": 5_100_000,
        "avg_liquidations_1h": 6_200_000,
        "momentum_score": 79.4,
    },
    "SOL": {
        "name": "Solana",
        "category": "Layer 1",
        "price_usd": 171.89,
        "change_24h": 4.5,
        "volume_24h": 6_200_000_000,
        "avg_volume_24h": 3_900_000_000,
        "range_high_20d": 189.00,
        "range_low_20d": 138.00,
        "funding_rate": 0.031,
        "funding_zscore": 2.8,
        "open_interest": 2_400_000_000,
        "oi_change_24h": 11.4,
        "long_liquidations_1h": 4_100_000,
        "short_liquidations_1h": 3_600_000,
        "avg_liquidations_1h": 3_900_000,
        "momentum_score": 88.6,
    },
    "DOGE": {
        "name": "Dogecoin",
        "category": "Meme",
        "price_usd": 0.194,
        "change_24h": -2.6,
        "volume_24h": 2_100_000_000,
        "avg_volume_24h": 1_800_000_000,
        "range_high_20d": 0.214,
        "range_low_20d": 0.170,
        "funding_rate": -0.004,
        "funding_zscore": 0.6,
        "open_interest": 980_000_000,
        "oi_change_24h": 10.8,
        "long_liquidations_1h": 3_200_000,
        "short_liquidations_1h": 2_300_000,
        "avg_liquidations_1h": 4_000_000,
        "momentum_score": 61.0,
    },
    "XRP": {
        "name": "XRP",
        "category": "Payments",
        "price_usd": 0.724,
        "change_24h": -0.8,
        "volume_24h": 1_400_000_000,
        "avg_volume_24h": 1_200_000_000,
        "range_high_20d": 0.781,
        "range_low_20d": 0.662,
        "funding_rate": 0.003,
        "funding_zscore": 0.4,
        "open_interest": 620_000_000,
        "oi_change_24h": 1.2,
        "long_liquidations_1h": 18_600_000,
        "short_liquidations_1h": 3_400_000,
        "avg_liquidations_1h": 6_300_000,
        "momentum_score": 58.4,
    },
}


def _to_asset_symbol(symbol: str) -> str:
    return symbol.upper().replace("USDT", "")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _compute_momentum_score(change_24h: float, volume_ratio: float, oi_change_24h: float) -> float:
    change_component = _clamp(abs(change_24h) / 6.0, 0.0, 1.0) * 45.0
    volume_component = _clamp((volume_ratio - 0.8) / 1.7, 0.0, 1.0) * 35.0
    oi_component = _clamp(abs(oi_change_24h) / 12.0, 0.0, 1.0) * 20.0
    return round(change_component + volume_component + oi_component, 1)


def build_mock_market_snapshots(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    selected_symbols = symbols or [f"{asset}USDT" for asset in DEFAULT_MARKET_BASELINES]
    snapshots: list[dict[str, Any]] = []

    for market_symbol in selected_symbols:
        asset_symbol = _to_asset_symbol(market_symbol)
        defaults = DEFAULT_MARKET_BASELINES.get(asset_symbol)
        if defaults is None:
            continue

        price = float(defaults["price_usd"])
        snapshots.append(
            {
                "symbol": asset_symbol,
                "name": defaults["name"],
                "category": defaults["category"],
                "source": "mock",
                "timeframe": "1D",
                "open_price": price * (1 - (float(defaults["change_24h"]) / 100.0)),
                "high_price": float(defaults["range_high_20d"]),
                "low_price": float(defaults["range_low_20d"]),
                "close_price": price,
                "price_usd": price,
                "change_24h": float(defaults["change_24h"]),
                "volume_24h": float(defaults["volume_24h"]),
                "avg_volume_24h": float(defaults["avg_volume_24h"]),
                "range_high_20d": float(defaults["range_high_20d"]),
                "range_low_20d": float(defaults["range_low_20d"]),
                "funding_rate": float(defaults["funding_rate"]),
                "funding_zscore": float(defaults["funding_zscore"]),
                "open_interest": float(defaults["open_interest"]),
                "oi_change_24h": float(defaults["oi_change_24h"]),
                "long_liquidations_1h": float(defaults["long_liquidations_1h"]),
                "short_liquidations_1h": float(defaults["short_liquidations_1h"]),
                "avg_liquidations_1h": float(defaults["avg_liquidations_1h"]),
                "momentum_score": float(defaults["momentum_score"]),
                "captured_at": datetime.now(timezone.utc),
                "raw_payload": {"mock": defaults},
            }
        )

    return snapshots


def normalize_market_snapshot(
    *,
    symbol: str,
    provider_data: dict[str, Any],
    previous_snapshot: dict[str, Any] | None,
    use_mock_fallback: bool,
) -> dict[str, Any] | None:
    asset_symbol = _to_asset_symbol(symbol)
    defaults = DEFAULT_MARKET_BASELINES.get(asset_symbol, {})
    binance = provider_data.get("binance", {})
    bybit = provider_data.get("bybit", {})
    coinglass = provider_data.get("coinglass", {})

    if not provider_data and not use_mock_fallback:
        return None

    ticker = binance.get("ticker") or bybit.get("ticker") or {}
    ohlcv = binance.get("ohlcv") or bybit.get("ohlcv") or []
    funding = bybit.get("funding") or binance.get("funding") or {}
    open_interest_payload = bybit.get("open_interest") or binance.get("open_interest") or {}
    liquidation_payload = coinglass.get("liquidations") or {}

    sources_used: set[str] = set()
    if binance:
        sources_used.add("binance")
    if bybit:
        sources_used.add("bybit")
    if coinglass:
        sources_used.add("coinglass")

    if not sources_used and use_mock_fallback:
        return build_mock_market_snapshots([symbol])[0]

    latest_candle = ohlcv[-1] if ohlcv else {}
    candle_highs = [_safe_float(item.get("high")) for item in ohlcv]
    candle_lows = [_safe_float(item.get("low")) for item in ohlcv]
    candle_volumes = [_safe_float(item.get("volume")) for item in ohlcv]

    price_usd = _safe_float(ticker.get("last_price"), _safe_float(defaults.get("price_usd")))
    change_24h = _safe_float(ticker.get("price_change_percent"), _safe_float(defaults.get("change_24h")))
    volume_24h = _safe_float(ticker.get("quote_volume") or ticker.get("volume"), _safe_float(defaults.get("volume_24h")))
    avg_volume_24h = (
        sum(candle_volumes) / len(candle_volumes)
        if candle_volumes
        else _safe_float(defaults.get("avg_volume_24h"))
    )
    range_high_20d = max(candle_highs) if candle_highs else _safe_float(defaults.get("range_high_20d"))
    range_low_20d = min(candle_lows) if candle_lows else _safe_float(defaults.get("range_low_20d"))

    funding_rate = _safe_float(
        funding.get("funding_rate", ticker.get("funding_rate")),
        _safe_float(defaults.get("funding_rate")),
    )
    funding_zscore = _safe_float(defaults.get("funding_zscore"))
    if funding_rate:
        funding_zscore = round(abs(funding_rate) / 0.01, 1)

    open_interest = _safe_float(
        open_interest_payload.get("open_interest", ticker.get("open_interest")),
        _safe_float(defaults.get("open_interest")),
    )

    oi_change_24h = _safe_float(open_interest_payload.get("open_interest_change_pct"))
    if oi_change_24h == 0.0 and previous_snapshot and previous_snapshot.get("open_interest"):
        previous_oi = _safe_float(previous_snapshot["open_interest"])
        if previous_oi:
            oi_change_24h = ((open_interest - previous_oi) / previous_oi) * 100.0
    if oi_change_24h == 0.0:
        oi_change_24h = _safe_float(defaults.get("oi_change_24h"))

    long_liquidations = _safe_float(
        liquidation_payload.get("long_liquidations_1h"),
        _safe_float(defaults.get("long_liquidations_1h")),
    )
    short_liquidations = _safe_float(
        liquidation_payload.get("short_liquidations_1h"),
        _safe_float(defaults.get("short_liquidations_1h")),
    )
    avg_liquidations = _safe_float(
        liquidation_payload.get("avg_liquidations_1h"),
        _safe_float(defaults.get("avg_liquidations_1h")),
    )

    volume_ratio = volume_24h / avg_volume_24h if avg_volume_24h else 1.0
    momentum_score = _compute_momentum_score(change_24h, volume_ratio, oi_change_24h)

    if defaults and (
        not ohlcv or not funding or not open_interest_payload or not liquidation_payload
    ):
        sources_used.add("mock")

    return {
        "symbol": asset_symbol,
        "name": defaults.get("name", asset_symbol),
        "category": defaults.get("category", "Unknown"),
        "source": "+".join(sorted(sources_used)) if sources_used else "mock",
        "timeframe": "1D",
        "open_price": _safe_float(
            latest_candle.get("open"),
            price_usd * (1 - (change_24h / 100.0)),
        ),
        "high_price": _safe_float(latest_candle.get("high"), range_high_20d),
        "low_price": _safe_float(latest_candle.get("low"), range_low_20d),
        "close_price": _safe_float(latest_candle.get("close"), price_usd),
        "price_usd": price_usd,
        "change_24h": change_24h,
        "volume_24h": volume_24h,
        "avg_volume_24h": avg_volume_24h,
        "range_high_20d": range_high_20d,
        "range_low_20d": range_low_20d,
        "funding_rate": funding_rate,
        "funding_zscore": funding_zscore,
        "open_interest": open_interest,
        "oi_change_24h": oi_change_24h,
        "long_liquidations_1h": long_liquidations,
        "short_liquidations_1h": short_liquidations,
        "avg_liquidations_1h": avg_liquidations,
        "momentum_score": momentum_score,
        "captured_at": ticker.get("close_time")
        or funding.get("timestamp")
        or open_interest_payload.get("timestamp")
        or datetime.now(timezone.utc),
        "raw_payload": _json_safe(provider_data),
    }
