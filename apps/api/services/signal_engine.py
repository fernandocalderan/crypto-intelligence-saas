import sys
from pathlib import Path

from config import get_settings
from models.schemas import SignalFeedResponse, SignalResponse
from services.market_data import list_signal_market_snapshots
from services.plans import PLAN_FREE, get_signal_limit, normalize_plan


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
) -> list[SignalResponse]:
    return [SignalResponse(**signal) for signal in compute_signal_payloads(market_snapshots=market_snapshots)]


def list_live_signals(plan: str = PLAN_FREE) -> list[SignalResponse]:
    active_signals = _detect_live_signals()
    signal_limit = get_signal_limit(plan)
    if signal_limit is None:
        return active_signals
    return active_signals[:signal_limit]


def get_signal_feed(plan: str = PLAN_FREE) -> SignalFeedResponse:
    active_signals = _detect_live_signals()
    normalized_plan = normalize_plan(plan)
    signal_limit = get_signal_limit(normalized_plan)
    visible_signals = active_signals if signal_limit is None else active_signals[:signal_limit]
    return SignalFeedResponse(
        access_plan=normalized_plan,
        total_available=len(active_signals),
        visible_count=len(visible_signals),
        has_locked_signals=len(visible_signals) < len(active_signals),
        signals=visible_signals,
    )


def list_signals() -> list[SignalResponse]:
    return list_live_signals()
