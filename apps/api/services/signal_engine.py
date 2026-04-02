import sys
from pathlib import Path

from config import get_settings
from models.schemas import SignalResponse
from services.market_data import list_signal_market_snapshots

ROOT_DIR = Path(__file__).resolve().parents[3]
SIGNAL_ENGINE_DIR = ROOT_DIR / "packages" / "signal-engine"

if str(SIGNAL_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(SIGNAL_ENGINE_DIR))

from engine import detect_active_signals  # noqa: E402


def list_live_signals() -> list[SignalResponse]:
    settings = get_settings()

    if not settings.signal_engine_use_mock_data:
        return []

    market_snapshots = list_signal_market_snapshots()
    active_signals = detect_active_signals(
        market_snapshots,
        enabled_signals=settings.signal_flags,
    )
    return [SignalResponse(**signal) for signal in active_signals]


def list_signals() -> list[SignalResponse]:
    return list_live_signals()
