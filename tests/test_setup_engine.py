from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.models import SetupRecord
from models.schemas import ConfluenceSetupResponse, SignalActionPlan, SignalKeyData
from services.setup_engine import (
    SETUP_STATUS_ACTIVE,
    SETUP_STATUS_TP1,
    create_setups_from_views,
    get_setup_performance,
    list_setup_history,
    update_setups_status,
)


def build_test_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    testing_session = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    return testing_session()


def executable_setup_view(**overrides) -> ConfluenceSetupResponse:
    payload = {
        "setup_key": "trend_continuation",
        "setup_type": "Trend Continuation",
        "asset_symbol": "BTC",
        "direction": "bullish",
        "signal_keys": ["volume_spike", "range_breakout"],
        "signals": [],
        "headline": "BTC — Trend Continuation",
        "execution_state": "EXECUTABLE",
        "execution_reason": "Confluencia suficiente para una ejecución táctica.",
        "summary": "BTC alinea volumen y breakout con plan indicativo completo.",
        "thesis": "BTC alinea volumen anómalo y ruptura de estructura en sesgo bullish.",
        "thesis_short": "BTC alinea volumen anómalo y ruptura de estructura en sesgo bullish.",
        "score": 8.2,
        "confidence": 81.4,
        "model_score": 8.2,
        "confidence_pct": 81.4,
        "key_data": SignalKeyData(
            price=68420.45,
            change_24h=3.4,
            volume_24h=31_200_000_000,
            funding=0.009,
            oi_change_24h=5.2,
            timeframe_base="1D",
            source="binance+bybit",
        ),
        "confirmations": [],
        "action_plan": SignalActionPlan(
            action_now="enter",
            bias="bullish",
            trigger_level=68557,
            invalidation_level=67216,
            tp1=69926,
            tp2=70952,
            levels_are_indicative=True,
            note="Indicativo",
        ),
        "data_quality_warnings": [],
        "is_mock_contaminated": False,
        "is_trade_executable": True,
        "generated_at": datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        "source_snapshot_time": datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        "detail_level": "full",
        "pro_plus_follow_up": None,
    }
    payload.update(overrides)
    return ConfluenceSetupResponse(**payload)


def test_create_setups_from_views_persists_only_executable_and_dedupes_active() -> None:
    session = build_test_session()
    created = create_setups_from_views(
        [
            executable_setup_view(),
            executable_setup_view(
                setup_key="positioning_trap",
                execution_state="WATCHLIST",
                is_trade_executable=False,
                action_plan=SignalActionPlan(
                    action_now="wait",
                    bias="bearish",
                    trigger_level=171.4,
                    invalidation_level=177.1,
                    tp1=167.9,
                    tp2=162.2,
                ),
            ),
        ],
        session,
    )

    assert len(created) == 1
    assert session.query(SetupRecord).count() == 1

    duplicate_attempt = create_setups_from_views([executable_setup_view()], session)
    assert duplicate_attempt == []
    assert session.query(SetupRecord).count() == 1


def test_update_setups_status_progresses_bullish_setup() -> None:
    session = build_test_session()
    record = SetupRecord(
        id="setup-btc-1",
        asset_symbol="BTC",
        setup_key="trend_continuation",
        setup_type="Trend Continuation",
        direction="bullish",
        signal_keys=["volume_spike", "range_breakout"],
        signal_hashes=["a", "b"],
        headline="BTC — Trend Continuation",
        summary="summary",
        score=8.2,
        confidence=81.4,
        execution_state="EXECUTABLE",
        execution_reason="reason",
        trigger_level=68557,
        invalidation_level=67216,
        tp1=69926,
        tp2=70952,
        status=SETUP_STATUS_ACTIVE,
        is_mock_contaminated=False,
        snapshot_data={},
        generated_at=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        source_snapshot_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
    )
    session.add(record)
    session.commit()

    first = update_setups_status(session.query(SetupRecord).all(), {"BTC": {"price_usd": 70010}}, session)
    session.refresh(record)
    assert first["updated"] == 1
    assert record.status == SETUP_STATUS_TP1
    assert record.tp1_hit_at is not None

    second = update_setups_status(session.query(SetupRecord).all(), {"BTC": {"price_usd": 71020}}, session)
    session.refresh(record)
    assert second["updated"] == 1
    assert record.status == "TP2_HIT"
    assert record.tp2_hit_at is not None


def test_list_setup_history_gates_free_but_shows_full_for_pro() -> None:
    session = build_test_session()
    record = SetupRecord(
        id="setup-btc-2",
        asset_symbol="BTC",
        setup_key="trend_continuation",
        setup_type="Trend Continuation",
        direction="bullish",
        signal_keys=["volume_spike", "range_breakout"],
        signal_hashes=["a", "b"],
        headline="BTC — Trend Continuation",
        summary="BTC alinea volumen y breakout con plan indicativo completo.",
        score=8.2,
        confidence=81.4,
        execution_state="EXECUTABLE",
        execution_reason="reason",
        trigger_level=68557,
        invalidation_level=67216,
        tp1=69926,
        tp2=70952,
        status=SETUP_STATUS_ACTIVE,
        is_mock_contaminated=False,
        snapshot_data={"price": 69000},
        generated_at=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        source_snapshot_time=datetime(2026, 4, 2, 18, 0, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    session.add(record)
    session.commit()

    free_items = list_setup_history(session, plan="free", limit=50)
    pro_items = list_setup_history(session, plan="pro", limit=50)

    assert len(free_items) == 1
    assert free_items[0].detail_level == "teaser"
    assert free_items[0].entry is None
    assert free_items[0].summary is None

    assert len(pro_items) == 1
    assert pro_items[0].detail_level == "full"
    assert pro_items[0].entry == 68557
    assert pro_items[0].current_price == 69000


def test_get_setup_performance_aggregates_lifecycle_metrics() -> None:
    session = build_test_session()
    created_at = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            SetupRecord(
                id="setup-1",
                asset_symbol="BTC",
                setup_key="trend_continuation",
                setup_type="Trend Continuation",
                direction="bullish",
                signal_keys=["volume_spike", "range_breakout"],
                signal_hashes=["a", "b"],
                headline="BTC — Trend Continuation",
                summary="summary",
                score=8.4,
                confidence=82.0,
                execution_state="EXECUTABLE",
                execution_reason="reason",
                trigger_level=68000,
                invalidation_level=67000,
                tp1=69000,
                tp2=70000,
                status="TP1_HIT",
                is_mock_contaminated=False,
                snapshot_data={},
                generated_at=created_at,
                source_snapshot_time=created_at,
                created_at=created_at,
                updated_at=created_at + timedelta(hours=4),
                tp1_hit_at=created_at + timedelta(hours=4),
            ),
            SetupRecord(
                id="setup-2",
                asset_symbol="ETH",
                setup_key="trend_continuation",
                setup_type="Trend Continuation",
                direction="bullish",
                signal_keys=["volume_spike", "range_breakout"],
                signal_hashes=["c", "d"],
                headline="ETH — Trend Continuation",
                summary="summary",
                score=8.1,
                confidence=79.0,
                execution_state="EXECUTABLE",
                execution_reason="reason",
                trigger_level=3500,
                invalidation_level=3400,
                tp1=3600,
                tp2=3700,
                status="TP2_HIT",
                is_mock_contaminated=False,
                snapshot_data={},
                generated_at=created_at,
                source_snapshot_time=created_at,
                created_at=created_at,
                updated_at=created_at + timedelta(hours=8),
                tp1_hit_at=created_at + timedelta(hours=3),
                tp2_hit_at=created_at + timedelta(hours=8),
            ),
            SetupRecord(
                id="setup-3",
                asset_symbol="SOL",
                setup_key="positioning_trap",
                setup_type="Positioning Trap",
                direction="bearish",
                signal_keys=["oi_divergence"],
                signal_hashes=["e"],
                headline="SOL — Positioning Trap",
                summary="summary",
                score=7.9,
                confidence=74.0,
                execution_state="EXECUTABLE",
                execution_reason="reason",
                trigger_level=170,
                invalidation_level=176,
                tp1=165,
                tp2=160,
                status="INVALIDATED",
                is_mock_contaminated=True,
                snapshot_data={},
                generated_at=created_at,
                source_snapshot_time=created_at,
                created_at=created_at,
                updated_at=created_at + timedelta(hours=2),
                invalidated_at=created_at + timedelta(hours=2),
            ),
            SetupRecord(
                id="setup-4",
                asset_symbol="XRP",
                setup_key="squeeze_reversal",
                setup_type="Squeeze Reversal",
                direction="bullish",
                signal_keys=["funding_extreme", "liquidation_cluster"],
                signal_hashes=["f", "g"],
                headline="XRP — Squeeze Reversal",
                summary="summary",
                score=8.0,
                confidence=77.0,
                execution_state="EXECUTABLE",
                execution_reason="reason",
                trigger_level=0.71,
                invalidation_level=0.68,
                tp1=0.74,
                tp2=0.77,
                status="ACTIVE",
                is_mock_contaminated=False,
                snapshot_data={},
                generated_at=created_at,
                source_snapshot_time=created_at,
                created_at=created_at,
                updated_at=created_at + timedelta(hours=1),
            ),
        ]
    )
    session.commit()

    pro = get_setup_performance(session, plan="pro")
    pro_plus = get_setup_performance(session, plan="pro_plus")

    assert pro.total_setups == 4
    assert pro.active == 1
    assert pro.tp1_hit_pct == 50.0
    assert pro.tp2_hit_pct == 25.0
    assert pro.invalidated_pct == 25.0
    assert pro.avg_time_to_tp1_hours == 3.5
    assert pro.by_setup_type == []

    assert len(pro_plus.by_setup_type) == 3
    trend_bucket = next(bucket for bucket in pro_plus.by_setup_type if bucket.setup_key == "trend_continuation")
    assert trend_bucket.total == 2
    assert trend_bucket.tp1_hit_pct == 100.0
