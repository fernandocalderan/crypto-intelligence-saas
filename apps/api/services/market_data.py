from typing import Any

from models.schemas import AssetResponse

MOCK_MARKET_SNAPSHOTS: list[dict[str, Any]] = [
    {
        "symbol": "BTC",
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
        "oi_change_24h": 4.2,
        "long_liquidations_1h": 8_400_000,
        "short_liquidations_1h": 5_200_000,
        "avg_liquidations_1h": 7_500_000,
        "momentum_score": 84.2,
        "timeframe": "4H",
        "source": "mock",
    },
    {
        "symbol": "ETH",
        "name": "Ethereum",
        "category": "Layer 1",
        "price_usd": 3_628.18,
        "change_24h": 2.1,
        "volume_24h": 18_600_000_000,
        "avg_volume_24h": 12_800_000_000,
        "range_high_20d": 3_588.00,
        "range_low_20d": 3_010.00,
        "funding_rate": 0.011,
        "funding_zscore": 1.2,
        "oi_change_24h": 3.0,
        "long_liquidations_1h": 6_900_000,
        "short_liquidations_1h": 5_100_000,
        "avg_liquidations_1h": 6_200_000,
        "momentum_score": 79.4,
        "timeframe": "4H",
        "source": "mock",
    },
    {
        "symbol": "SOL",
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
        "oi_change_24h": 11.4,
        "long_liquidations_1h": 4_100_000,
        "short_liquidations_1h": 3_600_000,
        "avg_liquidations_1h": 3_900_000,
        "momentum_score": 88.6,
        "timeframe": "8H",
        "source": "mock",
    },
    {
        "symbol": "DOGE",
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
        "oi_change_24h": 10.8,
        "long_liquidations_1h": 3_200_000,
        "short_liquidations_1h": 2_300_000,
        "avg_liquidations_1h": 4_000_000,
        "momentum_score": 61.0,
        "timeframe": "4H",
        "source": "mock",
    },
    {
        "symbol": "XRP",
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
        "oi_change_24h": 1.2,
        "long_liquidations_1h": 18_600_000,
        "short_liquidations_1h": 3_400_000,
        "avg_liquidations_1h": 6_300_000,
        "momentum_score": 58.4,
        "timeframe": "1H",
        "source": "mock",
    },
]

MOCK_ASSETS = [
    AssetResponse(
        symbol=snapshot["symbol"],
        name=snapshot["name"],
        category=snapshot["category"],
        price_usd=snapshot["price_usd"],
        change_24h=snapshot["change_24h"],
        volume_24h=snapshot["volume_24h"],
        momentum_score=snapshot["momentum_score"],
    )
    for snapshot in MOCK_MARKET_SNAPSHOTS
]


def list_assets() -> list[AssetResponse]:
    return MOCK_ASSETS


def list_signal_market_snapshots() -> list[dict[str, Any]]:
    return MOCK_MARKET_SNAPSHOTS
