import sys
from pathlib import Path

from config import get_settings
from models.schemas import ConfluenceSetupResponse, ProSignalResponse, SignalFeedResponse
from services.market_data import list_signal_market_snapshots
from services.plans import PLAN_FREE, get_signal_limit, normalize_plan
from services.pro_signal_view import build_pro_signal_views


def _resolve_signal_engine_dir() -> Path:
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        candidate = parent / "packages" / "signal-engine"
        if candidate.exists():
            return candidate
    raise RuntimeError("Signal engine package not found")


SIGNAL_ENGINE_DIR = _resolve_signal_engine_dir()

if str(SIGNAL_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(SIGNAL_ENGINE_DIR))

from engine import detect_active_signals  # noqa: E402


def compute_signal_payloads(
    market_snapshots: list[dict] | None = None,
) -> list[dict]:
    settings = get_settings()
    snapshots = market_snapshots if market_snapshots is not None else list_signal_market_snapshots()
    if not snapshots:
        return []

    return detect_active_signals(
        snapshots,
        enabled_signals=settings.signal_flags,
    )


def _detect_live_signals(
    market_snapshots: list[dict] | None = None,
) -> list[dict]:
    return compute_signal_payloads(market_snapshots=market_snapshots)


def compute_signal_and_setup_payloads(
    market_snapshots: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    snapshots = market_snapshots if market_snapshots is not None else list_signal_market_snapshots()
    signal_payloads = compute_signal_payloads(market_snapshots=snapshots)

    from services.confluence_engine import compute_confluence_setup_payloads

    setup_payloads = compute_confluence_setup_payloads(
        signal_payloads=signal_payloads,
        market_snapshots=snapshots,
    )
    return signal_payloads, setup_payloads


def _build_signal_views(plan: str = PLAN_FREE) -> list[ProSignalResponse]:
    normalized_plan = normalize_plan(plan)
    market_snapshots = list_signal_market_snapshots()
    active_signals = _detect_live_signals(market_snapshots=market_snapshots)
    signal_views = build_pro_signal_views(active_signals, market_snapshots, plan=normalized_plan)
    signal_limit = get_signal_limit(normalized_plan)
    if signal_limit is None:
        return signal_views
    return signal_views[:signal_limit]


def list_live_signals(plan: str = PLAN_FREE) -> list[ProSignalResponse]:
    return _build_signal_views(plan=plan)


def list_live_setups(plan: str = PLAN_FREE) -> list[ConfluenceSetupResponse]:
    normalized_plan = normalize_plan(plan)
    market_snapshots = list_signal_market_snapshots()
    signal_payloads, _setup_payloads = compute_signal_and_setup_payloads(market_snapshots=market_snapshots)
    if not signal_payloads:
        return []

    from services.confluence_engine import build_confluence_setup_views

    return build_confluence_setup_views(
        signal_payloads=signal_payloads,
        market_snapshots=market_snapshots,
        plan=normalized_plan,
    )


def get_signal_feed(plan: str = PLAN_FREE) -> SignalFeedResponse:
    normalized_plan = normalize_plan(plan)
    market_snapshots = list_signal_market_snapshots()
    active_signals = build_pro_signal_views(
        _detect_live_signals(market_snapshots=market_snapshots),
        market_snapshots,
        plan=normalized_plan,
    )
    signal_limit = get_signal_limit(normalized_plan)
    visible_signals = active_signals if signal_limit is None else active_signals[:signal_limit]
    return SignalFeedResponse(
        access_plan=normalized_plan,
        total_available=len(active_signals),
        visible_count=len(visible_signals),
        has_locked_signals=len(visible_signals) < len(active_signals),
        signals=visible_signals,
    )


def list_signals() -> list[ProSignalResponse]:
    return list_live_signals()
