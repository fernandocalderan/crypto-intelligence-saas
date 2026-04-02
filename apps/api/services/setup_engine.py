from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import SetupRecord
from models.schemas import (
    ConfluenceSetupResponse,
    SetupHistoryResponse,
    SetupPerformanceBucket,
    SetupPerformanceResponse,
)
from services.plans import PLAN_FREE, PLAN_PRO_PLUS, normalize_plan

logger = logging.getLogger(__name__)

SETUP_STATUS_ACTIVE = "ACTIVE"
SETUP_STATUS_TP1 = "TP1_HIT"
SETUP_STATUS_TP2 = "TP2_HIT"
SETUP_STATUS_INVALIDATED = "INVALIDATED"
SETUP_STATUS_EXPIRED = "EXPIRED"

ACTIVE_SETUP_STATUSES = {SETUP_STATUS_ACTIVE, SETUP_STATUS_TP1}
TERMINAL_SETUP_STATUSES = {SETUP_STATUS_TP2, SETUP_STATUS_INVALIDATED, SETUP_STATUS_EXPIRED}
SETUP_EXPIRY_HOURS = 72


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


def _normalize_direction(value: Any) -> str:
    normalized = str(value or "neutral").strip().lower()
    if normalized not in {"bullish", "bearish", "neutral"}:
        return "neutral"
    return normalized


def _setup_id(view: ConfluenceSetupResponse) -> str:
    base = "|".join(
        [
            view.asset_symbol.upper(),
            view.setup_key.lower(),
            _normalize_direction(view.direction),
            ",".join(sorted(view.signal_keys)),
            _coerce_datetime(view.generated_at).isoformat(),
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _snapshot_payload(view: ConfluenceSetupResponse) -> dict[str, Any]:
    key_data = view.key_data.model_dump() if view.key_data is not None else {}
    return {
        **key_data,
        "signal_keys": list(view.signal_keys),
        "execution_state": view.execution_state,
        "generated_at": _coerce_datetime(view.generated_at).isoformat(),
    }


def list_active_setups(db: Session) -> list[SetupRecord]:
    return db.scalars(
        select(SetupRecord).where(SetupRecord.status.in_(sorted(ACTIVE_SETUP_STATUSES)))
    ).all()


def create_setups_from_views(
    setup_views: list[ConfluenceSetupResponse],
    db: Session,
) -> list[SetupRecord]:
    if not setup_views:
        return []

    created: list[SetupRecord] = []

    for view in setup_views:
        if view.execution_state != "EXECUTABLE" or not view.is_trade_executable or view.action_plan is None:
            continue

        existing = db.scalar(
            select(SetupRecord)
            .where(
                SetupRecord.asset_symbol == view.asset_symbol,
                SetupRecord.setup_key == view.setup_key,
                SetupRecord.direction == view.direction,
                SetupRecord.status.in_(sorted(ACTIVE_SETUP_STATUSES)),
            )
            .order_by(SetupRecord.created_at.desc())
        )
        if existing is not None:
            continue

        signal_hashes = []
        for signal in view.signals:
            signal_hashes.append(f"{signal.signal_key}:{signal.direction}:{signal.score:.1f}")

        record = SetupRecord(
            id=_setup_id(view),
            asset_symbol=view.asset_symbol,
            setup_key=view.setup_key,
            setup_type=view.setup_type,
            direction=view.direction,
            signal_keys=list(view.signal_keys),
            signal_hashes=signal_hashes,
            headline=view.headline,
            summary=view.summary,
            score=float(view.score),
            confidence=float(view.confidence),
            execution_state=str(view.execution_state),
            execution_reason=view.execution_reason,
            trigger_level=view.action_plan.trigger_level,
            invalidation_level=view.action_plan.invalidation_level,
            tp1=view.action_plan.tp1,
            tp2=view.action_plan.tp2,
            status=SETUP_STATUS_ACTIVE,
            is_mock_contaminated=bool(view.is_mock_contaminated),
            snapshot_data=_snapshot_payload(view),
            generated_at=_coerce_datetime(view.generated_at),
            source_snapshot_time=_coerce_datetime(view.source_snapshot_time)
            if view.source_snapshot_time is not None
            else None,
        )
        db.add(record)
        created.append(record)

    if not created:
        return []

    db.commit()
    for record in created:
        db.refresh(record)

    logger.info("Persisted %s new executable setups", len(created))
    return created


def update_setups_status(
    setups: list[SetupRecord],
    market_snapshots: dict[str, dict[str, Any]],
    db: Session,
) -> dict[str, int]:
    if not setups:
        return {"updated": 0, "expired": 0}

    now = datetime.now(timezone.utc)
    updated = 0
    expired = 0

    for setup in setups:
        current_status = setup.status
        created_at = _coerce_datetime(setup.created_at)
        if current_status in ACTIVE_SETUP_STATUSES and now - created_at >= timedelta(hours=SETUP_EXPIRY_HOURS):
            setup.status = SETUP_STATUS_EXPIRED
            if setup.expired_at is None:
                setup.expired_at = now
            setup.updated_at = now
            expired += 1
            updated += 1
            continue

        snapshot = market_snapshots.get(setup.asset_symbol.upper(), {})
        price = snapshot.get("price_usd")
        if price is None:
            continue

        price_value = float(price)
        direction = _normalize_direction(setup.direction)
        next_status = current_status

        if direction == "bullish":
            if setup.invalidation_level is not None and price_value <= float(setup.invalidation_level):
                next_status = SETUP_STATUS_INVALIDATED
            elif setup.tp2 is not None and price_value >= float(setup.tp2):
                next_status = SETUP_STATUS_TP2
            elif current_status == SETUP_STATUS_ACTIVE and setup.tp1 is not None and price_value >= float(setup.tp1):
                next_status = SETUP_STATUS_TP1
        elif direction == "bearish":
            if setup.invalidation_level is not None and price_value >= float(setup.invalidation_level):
                next_status = SETUP_STATUS_INVALIDATED
            elif setup.tp2 is not None and price_value <= float(setup.tp2):
                next_status = SETUP_STATUS_TP2
            elif current_status == SETUP_STATUS_ACTIVE and setup.tp1 is not None and price_value <= float(setup.tp1):
                next_status = SETUP_STATUS_TP1

        if next_status != current_status:
            setup.status = next_status
            if next_status == SETUP_STATUS_TP1 and setup.tp1_hit_at is None:
                setup.tp1_hit_at = now
            elif next_status == SETUP_STATUS_TP2:
                if setup.tp1_hit_at is None:
                    setup.tp1_hit_at = now
                if setup.tp2_hit_at is None:
                    setup.tp2_hit_at = now
            elif next_status == SETUP_STATUS_INVALIDATED and setup.invalidated_at is None:
                setup.invalidated_at = now
            setup.updated_at = now
            updated += 1

    if updated > 0:
        db.commit()
    return {"updated": updated, "expired": expired}


def _sanitize_history_item(record: SetupRecord, plan: str) -> SetupHistoryResponse:
    normalized_plan = normalize_plan(plan)
    current_price = None
    if isinstance(record.snapshot_data, dict):
        raw_price = record.snapshot_data.get("price")
        if raw_price is not None:
            try:
                current_price = float(raw_price)
            except (TypeError, ValueError):
                current_price = None

    item = SetupHistoryResponse(
        id=record.id,
        asset_symbol=record.asset_symbol,
        setup_key=record.setup_key,
        setup_type=record.setup_type,
        headline=record.headline,
        direction=record.direction,
        status=record.status,
        execution_state=record.execution_state,
        score=record.score,
        confidence=record.confidence,
        summary=record.summary,
        entry=record.trigger_level,
        tp1=record.tp1,
        tp2=record.tp2,
        invalidation=record.invalidation_level,
        current_price=current_price,
        is_mock_contaminated=record.is_mock_contaminated,
        created_at=_coerce_datetime(record.created_at),
        updated_at=_coerce_datetime(record.updated_at) if record.updated_at is not None else None,
        detail_level="full",
    )

    if normalized_plan == PLAN_FREE:
        return item.model_copy(
            update={
                "summary": None,
                "entry": None,
                "tp1": None,
                "tp2": None,
                "invalidation": None,
                "current_price": None,
                "detail_level": "teaser",
            }
        )

    return item


def list_setup_history(
    db: Session,
    *,
    plan: str,
    limit: int = 50,
) -> list[SetupHistoryResponse]:
    normalized_plan = normalize_plan(plan)
    safe_limit = min(max(limit, 1), 100)
    if normalized_plan == PLAN_FREE:
        safe_limit = min(safe_limit, 2)

    records = db.scalars(
        select(SetupRecord).order_by(SetupRecord.created_at.desc()).limit(safe_limit)
    ).all()
    return [_sanitize_history_item(record, normalized_plan) for record in records]


def _round_metric(value: float) -> float:
    return round(value, 1)


def get_setup_performance(db: Session, *, plan: str) -> SetupPerformanceResponse:
    records = db.scalars(select(SetupRecord)).all()
    total_setups = len(records)
    active_count = sum(1 for record in records if record.status == SETUP_STATUS_ACTIVE)
    tp1_hit_count = sum(
        1
        for record in records
        if record.tp1_hit_at is not None or record.status in {SETUP_STATUS_TP1, SETUP_STATUS_TP2}
    )
    tp2_hit_count = sum(
        1
        for record in records
        if record.tp2_hit_at is not None or record.status == SETUP_STATUS_TP2
    )
    invalidated_count = sum(1 for record in records if record.status == SETUP_STATUS_INVALIDATED)

    if total_setups == 0:
        return SetupPerformanceResponse(
            total_setups=0,
            active=0,
            tp1_hit_pct=0.0,
            tp2_hit_pct=0.0,
            invalidated_pct=0.0,
            avg_time_to_tp1_hours=0.0,
            by_setup_type=[],
        )

    tp1_durations_hours: list[float] = []
    for record in records:
        tp1_reference = record.tp1_hit_at
        if tp1_reference is None and record.status == SETUP_STATUS_TP1 and record.updated_at is not None:
            tp1_reference = record.updated_at
        if tp1_reference is None:
            continue
        elapsed_hours = max(
            (_coerce_datetime(tp1_reference) - _coerce_datetime(record.created_at)).total_seconds() / 3600,
            0.0,
        )
        tp1_durations_hours.append(elapsed_hours)

    buckets: dict[str, dict[str, Any]] = {}
    for record in records:
        bucket = buckets.setdefault(
            record.setup_key,
            {
                "setup_key": record.setup_key,
                "setup_type": record.setup_type,
                "total": 0,
                "tp1_hits": 0,
                "tp2_hits": 0,
                "invalidated": 0,
            },
        )
        bucket["total"] += 1
        if record.tp1_hit_at is not None or record.status in {SETUP_STATUS_TP1, SETUP_STATUS_TP2}:
            bucket["tp1_hits"] += 1
        if record.tp2_hit_at is not None or record.status == SETUP_STATUS_TP2:
            bucket["tp2_hits"] += 1
        if record.status == SETUP_STATUS_INVALIDATED:
            bucket["invalidated"] += 1

    breakdown = [
        SetupPerformanceBucket(
            setup_key=bucket["setup_key"],
            setup_type=bucket["setup_type"],
            total=int(bucket["total"]),
            tp1_hit_pct=_round_metric((bucket["tp1_hits"] / bucket["total"]) * 100),
            tp2_hit_pct=_round_metric((bucket["tp2_hits"] / bucket["total"]) * 100),
            invalidated_pct=_round_metric((bucket["invalidated"] / bucket["total"]) * 100),
        )
        for bucket in buckets.values()
        if bucket["total"] > 0
    ]
    breakdown.sort(key=lambda item: (-item.total, item.setup_key))

    if normalize_plan(plan) != PLAN_PRO_PLUS:
        breakdown = []

    return SetupPerformanceResponse(
        total_setups=total_setups,
        active=active_count,
        tp1_hit_pct=_round_metric((tp1_hit_count / total_setups) * 100),
        tp2_hit_pct=_round_metric((tp2_hit_count / total_setups) * 100),
        invalidated_pct=_round_metric((invalidated_count / total_setups) * 100),
        avg_time_to_tp1_hours=_round_metric(
            sum(tp1_durations_hours) / len(tp1_durations_hours) if tp1_durations_hours else 0.0
        ),
        by_setup_type=breakdown,
    )
