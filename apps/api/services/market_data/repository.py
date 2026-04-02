from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from db.models import AssetRecord, MarketSnapshotRecord
from db.session import SessionLocal


def _ensure_asset(session, snapshot: dict[str, Any]) -> AssetRecord:
    asset = session.scalar(
        select(AssetRecord).where(AssetRecord.symbol == snapshot["symbol"])
    )

    if asset is None:
        asset = AssetRecord(
            symbol=snapshot["symbol"],
            name=snapshot["name"],
            category=snapshot["category"],
        )
        session.add(asset)
        session.flush()
    else:
        asset.name = snapshot["name"]
        asset.category = snapshot["category"]

    return asset


def _record_to_snapshot(record: MarketSnapshotRecord) -> dict[str, Any]:
    return {
        "symbol": record.asset.symbol,
        "name": record.asset.name,
        "category": record.asset.category,
        "source": record.source,
        "timeframe": record.timeframe,
        "open_price": record.open_price,
        "high_price": record.high_price,
        "low_price": record.low_price,
        "close_price": record.close_price,
        "price_usd": record.price_usd,
        "change_24h": record.change_24h,
        "volume_24h": record.volume_24h,
        "avg_volume_24h": record.avg_volume_24h,
        "range_high_20d": record.range_high_20d,
        "range_low_20d": record.range_low_20d,
        "funding_rate": record.funding_rate,
        "funding_zscore": record.funding_zscore,
        "open_interest": record.open_interest,
        "oi_change_24h": record.oi_change_24h,
        "long_liquidations_1h": record.long_liquidations_1h,
        "short_liquidations_1h": record.short_liquidations_1h,
        "avg_liquidations_1h": record.avg_liquidations_1h,
        "momentum_score": record.momentum_score,
        "captured_at": record.captured_at,
        "generated_at": record.captured_at,
        "raw_payload": record.raw_payload,
    }


def save_market_snapshots(snapshots: list[dict[str, Any]]) -> None:
    with SessionLocal() as session:
        for snapshot in snapshots:
            asset = _ensure_asset(session, snapshot)
            session.add(
                MarketSnapshotRecord(
                    asset_id=asset.id,
                    source=snapshot["source"],
                    timeframe=snapshot["timeframe"],
                    open_price=snapshot["open_price"],
                    high_price=snapshot["high_price"],
                    low_price=snapshot["low_price"],
                    close_price=snapshot["close_price"],
                    price_usd=snapshot["price_usd"],
                    change_24h=snapshot["change_24h"],
                    volume_24h=snapshot["volume_24h"],
                    avg_volume_24h=snapshot["avg_volume_24h"],
                    range_high_20d=snapshot["range_high_20d"],
                    range_low_20d=snapshot["range_low_20d"],
                    funding_rate=snapshot["funding_rate"],
                    funding_zscore=snapshot["funding_zscore"],
                    open_interest=snapshot["open_interest"],
                    oi_change_24h=snapshot["oi_change_24h"],
                    long_liquidations_1h=snapshot["long_liquidations_1h"],
                    short_liquidations_1h=snapshot["short_liquidations_1h"],
                    avg_liquidations_1h=snapshot["avg_liquidations_1h"],
                    momentum_score=snapshot["momentum_score"],
                    raw_payload=snapshot.get("raw_payload", {}),
                    captured_at=snapshot["captured_at"],
                )
            )

        session.commit()


def get_latest_market_snapshots() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        records = session.scalars(
            select(MarketSnapshotRecord)
            .options(joinedload(MarketSnapshotRecord.asset))
            .order_by(MarketSnapshotRecord.captured_at.desc(), MarketSnapshotRecord.id.desc())
        ).all()

        latest_by_symbol: dict[str, dict[str, Any]] = {}
        for record in records:
            symbol = record.asset.symbol
            if symbol in latest_by_symbol:
                continue
            latest_by_symbol[symbol] = _record_to_snapshot(record)

        return list(latest_by_symbol.values())


def get_previous_snapshot(symbol: str) -> dict[str, Any] | None:
    with SessionLocal() as session:
        record = session.scalar(
            select(MarketSnapshotRecord)
            .join(MarketSnapshotRecord.asset)
            .options(joinedload(MarketSnapshotRecord.asset))
            .where(AssetRecord.symbol == symbol)
            .order_by(MarketSnapshotRecord.captured_at.desc(), MarketSnapshotRecord.id.desc())
        )
        if record is None:
            return None
        return _record_to_snapshot(record)
