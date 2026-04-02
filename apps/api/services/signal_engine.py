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


def _detect_live_signals() -> list[SignalResponse]:
    settings = get_settings()

    market_snapshots = list_signal_market_snapshots()
    active_signals = detect_active_signals(
        market_snapshots,
        enabled_signals=settings.signal_flags,
    )
    return [SignalResponse(**signal) for signal in active_signals]


def list_live_signals(plan: str = PLAN_FREE) -> list[SignalResponse]:
    active_signals = _detect_live_signals()
    signal_limit = get_signal_limit(plan)
    if signal_limit is None:
        return active_signals
    return active_signals[:signal_limit]


def get_signal_feed(plan: str = PLAN_FREE) -> SignalFeedResponse:
    active_signals = _detect_live_signals()
    normalized_plan = normalize_plan(plan)
    visible_signals = list_live_signals(normalized_plan)
    return SignalFeedResponse(
        access_plan=normalized_plan,
        total_available=len(active_signals),
        visible_count=len(visible_signals),
        has_locked_signals=len(visible_signals) < len(active_signals),
        signals=visible_signals,
    )


def list_signals() -> list[SignalResponse]:
    return list_live_signals()
