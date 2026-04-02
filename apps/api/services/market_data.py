from models.schemas import AssetResponse

MOCK_ASSETS = [
    AssetResponse(
        symbol="BTC",
        name="Bitcoin",
        category="Layer 1",
        price_usd=68420.45,
        change_24h=2.8,
        volume_24h=29_850_000_000,
        momentum_score=84.2,
    ),
    AssetResponse(
        symbol="ETH",
        name="Ethereum",
        category="Layer 1",
        price_usd=3520.18,
        change_24h=1.6,
        volume_24h=15_400_000_000,
        momentum_score=78.4,
    ),
    AssetResponse(
        symbol="SOL",
        name="Solana",
        category="Layer 1",
        price_usd=171.89,
        change_24h=4.2,
        volume_24h=6_200_000_000,
        momentum_score=88.6,
    ),
]


def list_assets() -> list[AssetResponse]:
    return MOCK_ASSETS

