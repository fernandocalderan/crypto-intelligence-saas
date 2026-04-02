import logging
from typing import Any

from config import get_settings
from models.schemas import AssetResponse
from services.market_data.binance_client import BinanceClient
from services.market_data.bybit_client import BybitClient
from services.market_data.coinglass_client import CoinglassClient
from services.market_data.normalizer import build_mock_market_snapshots, normalize_market_snapshot
from services.market_data.repository import (
    get_latest_market_snapshots as get_latest_market_snapshot_rows,
    get_previous_snapshot,
    save_market_snapshots,
)

logger = logging.getLogger(__name__)


def _fetch_binance_bundle(client: BinanceClient, symbol: str) -> dict[str, Any]:
    return {
        "ohlcv": client.fetch_ohlcv(symbol),
        "ticker": client.fetch_ticker(symbol),
        "funding": client.fetch_funding(symbol),
        "open_interest": client.fetch_open_interest(symbol),
    }


def _fetch_bybit_bundle(client: BybitClient, symbol: str) -> dict[str, Any]:
    return {
        "ohlcv": client.fetch_ohlcv(symbol),
        "ticker": client.fetch_ticker(symbol),
        "funding": client.fetch_funding(symbol),
        "open_interest": client.fetch_open_interest(symbol),
    }


def ingest_market_snapshots() -> list[dict[str, Any]]:
    settings = get_settings()
    snapshots: list[dict[str, Any]] = []
    binance_client = BinanceClient() if settings.enable_binance_market_data else None
    bybit_client = BybitClient() if settings.enable_bybit_market_data else None
    coinglass_client = (
        CoinglassClient(api_key=settings.coinglass_api_key)
        if settings.enable_coinglass_market_data
        else None
    )

    for market_symbol in settings.parsed_market_data_symbols:
        provider_data: dict[str, Any] = {}
        previous_snapshot = None
        try:
            previous_snapshot = get_previous_snapshot(market_symbol.replace("USDT", ""))
        except Exception as exc:
            logger.warning(
                "Previous snapshot lookup failed for %s, continuing without DB baseline: %s",
                market_symbol,
                exc,
            )

        if binance_client is not None:
            try:
                provider_data["binance"] = _fetch_binance_bundle(binance_client, market_symbol)
            except Exception as exc:
                logger.warning("Binance fetch failed for %s: %s", market_symbol, exc)

        if bybit_client is not None:
            try:
                provider_data["bybit"] = _fetch_bybit_bundle(bybit_client, market_symbol)
            except Exception as exc:
                logger.warning("Bybit fetch failed for %s: %s", market_symbol, exc)

        if coinglass_client is not None:
            try:
                liquidations = coinglass_client.fetch_liquidations(market_symbol)
                if liquidations:
                    provider_data["coinglass"] = {"liquidations": liquidations}
            except Exception as exc:
                logger.warning("Coinglass fetch failed for %s: %s", market_symbol, exc)

        normalized = normalize_market_snapshot(
            symbol=market_symbol,
            provider_data=provider_data,
            previous_snapshot=previous_snapshot,
            use_mock_fallback=settings.market_data_use_mock_fallback,
        )
        if normalized is not None:
            snapshots.append(normalized)

    if not snapshots:
        return []

    try:
        save_market_snapshots(snapshots)
    except Exception as exc:
        logger.warning("Saving market snapshots failed, continuing with in-memory data: %s", exc)

    logger.info("Ingested %s market snapshots", len(snapshots))
    return snapshots


def list_latest_market_snapshots(force_refresh: bool = False) -> list[dict[str, Any]]:
    settings = get_settings()

    if not force_refresh:
        try:
            snapshots = get_latest_market_snapshot_rows()
            if snapshots:
                return snapshots
        except Exception as exc:
            logger.warning("Loading latest market snapshots from DB failed: %s", exc)

    live_snapshots = ingest_market_snapshots()
    if live_snapshots:
        return live_snapshots

    if settings.market_data_use_mock_fallback:
        return build_mock_market_snapshots(settings.parsed_market_data_symbols)

    return []


def list_signal_market_snapshots() -> list[dict[str, Any]]:
    snapshots = list_latest_market_snapshots()
    for snapshot in snapshots:
        if "generated_at" not in snapshot:
            snapshot["generated_at"] = snapshot["captured_at"]
    return snapshots


def list_assets() -> list[AssetResponse]:
    snapshots = list_latest_market_snapshots()
    return [
        AssetResponse(
            symbol=snapshot["symbol"],
            name=snapshot["name"],
            category=snapshot["category"],
            price_usd=snapshot["price_usd"],
            change_24h=snapshot["change_24h"],
            volume_24h=snapshot["volume_24h"],
            momentum_score=snapshot["momentum_score"],
        )
        for snapshot in snapshots
    ]
