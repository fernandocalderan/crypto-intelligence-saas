import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import get_settings
from db.models import AssetRecord, SignalRecord
from models.schemas import ProSignalResponse
from services.pro_signal_view import build_pro_signal_view

logger = logging.getLogger(__name__)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return datetime.now(timezone.utc)


def _floor_to_bucket(timestamp: datetime, window_minutes: int) -> datetime:
    safe_window = max(window_minutes, 1)
    normalized = _coerce_datetime(timestamp).astimezone(timezone.utc)
    bucket_minute = (normalized.minute // safe_window) * safe_window
    return normalized.replace(minute=bucket_minute, second=0, microsecond=0)


def build_signal_hash(
    *,
    asset_symbol: str,
    signal_key: str,
    timeframe: str,
    direction: str | None,
    source_snapshot_time: datetime | str | None = None,
    created_at: datetime | str | None = None,
    dedupe_window_minutes: int | None = None,
) -> str:
    settings = get_settings()
    window_minutes = dedupe_window_minutes or settings.alert_dedupe_window_minutes
    base_timestamp = source_snapshot_time or created_at or datetime.now(timezone.utc)
    bucket = _floor_to_bucket(_coerce_datetime(base_timestamp), window_minutes)
    base = "|".join(
        [
            asset_symbol.strip().upper(),
            signal_key.strip().lower(),
            timeframe.strip().upper(),
            (direction or "neutral").strip().lower(),
            bucket.isoformat(),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _resolve_signal_type(detected_signal: dict[str, Any]) -> str:
    signal_type = detected_signal.get("signal_type")
    if signal_type:
        return str(signal_type)
    return str(detected_signal.get("signal_key", "signal")).replace("_", " ").title()


def _ensure_assets(
    db: Session,
    detected_signals: list[dict[str, Any]],
    snapshot_index: dict[str, dict[str, Any]],
) -> dict[str, AssetRecord]:
    symbols = sorted({str(signal["asset_symbol"]).upper() for signal in detected_signals})
    if not symbols:
        return {}

    existing_assets = db.scalars(
        select(AssetRecord).where(AssetRecord.symbol.in_(symbols))
    ).all()
    asset_lookup = {asset.symbol: asset for asset in existing_assets}

    for symbol in symbols:
        if symbol in asset_lookup:
            continue

        snapshot = snapshot_index.get(symbol, {})
        asset = AssetRecord(
            symbol=symbol,
            name=str(snapshot.get("name", symbol)),
            category=str(snapshot.get("category", "Unknown")),
        )
        db.add(asset)
        db.flush()
        asset_lookup[symbol] = asset

    return asset_lookup


def map_detector_output_to_model(
    detected_signal: dict[str, Any],
    *,
    snapshot_index: dict[str, dict[str, Any]] | None = None,
    asset_lookup: dict[str, AssetRecord] | None = None,
) -> dict[str, Any]:
    snapshots = snapshot_index or {}
    assets = asset_lookup or {}

    asset_symbol = str(detected_signal["asset_symbol"]).upper()
    snapshot = snapshots.get(asset_symbol, {})
    created_at = _coerce_datetime(detected_signal.get("generated_at") or snapshot.get("captured_at"))
    source_snapshot_time = _coerce_datetime(snapshot.get("captured_at") or created_at)
    signal_key = str(detected_signal.get("signal_key", "signal"))
    timeframe = str(detected_signal.get("timeframe", "4H"))
    direction = detected_signal.get("direction")
    signal_hash = build_signal_hash(
        asset_symbol=asset_symbol,
        signal_key=signal_key,
        timeframe=timeframe,
        direction=str(direction) if direction else None,
        source_snapshot_time=source_snapshot_time,
        created_at=created_at,
    )

    asset = assets.get(asset_symbol)
    evidence = detected_signal.get("evidence") or []

    return {
        "public_id": signal_hash,
        "asset_id": asset.id if asset else None,
        "user_id": None,
        "asset_symbol": asset_symbol,
        "signal_key": signal_key,
        "signal_type": _resolve_signal_type(detected_signal),
        "timeframe": timeframe,
        "direction": str(direction) if direction else None,
        "confidence": float(detected_signal["confidence"]),
        "score": float(detected_signal["score"]),
        "thesis": str(detected_signal["thesis"]),
        "evidence_json": [str(item) for item in evidence],
        "source": str(detected_signal.get("source", snapshot.get("source", "runtime"))),
        "source_snapshot_time": source_snapshot_time,
        "signal_hash": signal_hash,
        "is_active": True,
        "created_at": created_at,
    }


def persist_signals(
    db: Session,
    detected_signals: list[dict[str, Any]],
    *,
    snapshot_index: dict[str, dict[str, Any]] | None = None,
) -> list[SignalRecord]:
    if not detected_signals:
        return []

    resolved_snapshot_index = snapshot_index or {}
    asset_lookup = _ensure_assets(db, detected_signals, resolved_snapshot_index)
    mapped_signals = [
        map_detector_output_to_model(
            signal,
            snapshot_index=resolved_snapshot_index,
            asset_lookup=asset_lookup,
        )
        for signal in detected_signals
    ]
    signal_hashes = [item["signal_hash"] for item in mapped_signals]
    existing_hashes = set(
        db.scalars(
            select(SignalRecord.signal_hash).where(SignalRecord.signal_hash.in_(signal_hashes))
        ).all()
    )
    duplicate_count = sum(1 for item in mapped_signals if item["signal_hash"] in existing_hashes)
    logger.info(
        "signal_persistence_summary detected=%s existing_hashes=%s duplicates=%s",
        len(detected_signals),
        len(existing_hashes),
        duplicate_count,
    )

    new_records: list[SignalRecord] = []
    for payload in mapped_signals:
        if payload["signal_hash"] in existing_hashes:
            continue
        record = SignalRecord(**payload)
        db.add(record)
        new_records.append(record)

    if not new_records:
        return []

    try:
        db.commit()
    except IntegrityError:
        logger.warning("Signal persistence encountered a dedupe race, retrying filtered insert")
        db.rollback()
        new_records = []
        for payload in mapped_signals:
            existing = db.scalar(
                select(SignalRecord).where(SignalRecord.signal_hash == payload["signal_hash"])
            )
            if existing is not None:
                continue
            record = SignalRecord(**payload)
            db.add(record)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                continue
            db.refresh(record)
            new_records.append(record)
    else:
        for record in new_records:
            db.refresh(record)

    logger.info(
        "signal_persistence_completed persisted=%s deduped=%s",
        len(new_records),
        duplicate_count,
    )
    return new_records


def map_signal_record_to_response(record: SignalRecord) -> ProSignalResponse:
    return build_pro_signal_view(
        {
            "id": record.public_id or record.signal_hash,
            "signal_key": record.signal_key,
            "asset_symbol": record.asset_symbol,
            "signal_type": record.signal_type,
            "timeframe": record.timeframe,
            "direction": record.direction or "neutral",
            "confidence": record.confidence,
            "score": record.score,
            "thesis": record.thesis,
            "evidence": list(record.evidence_json or []),
            "source": record.source,
            "generated_at": record.created_at,
            "source_snapshot_time": record.source_snapshot_time,
        },
        plan="pro",
    )
