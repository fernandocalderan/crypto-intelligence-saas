import sys
from pathlib import Path
from typing import Any

from models.schemas import ConfluenceSetupResponse
from services.market_data import list_signal_market_snapshots
from services.plans import PLAN_FREE, normalize_plan
from services.setup_view import build_setup_views
from services.signal_persistence import build_signal_hash


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

from confluence import detect_confluence_setups, group_signals_by_asset  # noqa: E402


def _snapshot_index(market_snapshots: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {
        str(snapshot.get("symbol", "")).upper(): snapshot
        for snapshot in (market_snapshots or [])
    }


def _attach_signal_hashes(
    signal_payloads: list[dict[str, Any]],
    market_snapshots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    snapshots = _snapshot_index(market_snapshots)
    hashed_payloads: list[dict[str, Any]] = []

    for signal in signal_payloads:
        asset_symbol = str(signal.get("asset_symbol", "")).upper()
        snapshot = snapshots.get(asset_symbol, {})
        source_snapshot_time = snapshot.get("captured_at") or signal.get("generated_at")
        signal_hash = build_signal_hash(
            asset_symbol=asset_symbol,
            signal_key=str(signal.get("signal_key", "signal")),
            timeframe=str(signal.get("timeframe", "4H")),
            direction=str(signal.get("direction", "neutral")) if signal.get("direction") else None,
            source_snapshot_time=source_snapshot_time,
            created_at=signal.get("generated_at"),
        )
        hashed_signal = dict(signal)
        hashed_signal["signal_hash"] = signal_hash
        hashed_signal["source_snapshot_time"] = source_snapshot_time
        hashed_payloads.append(hashed_signal)

    return hashed_payloads


def compute_confluence_setup_payloads(
    *,
    signal_payloads: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if signal_payloads is None:
        from services.signal_engine import compute_signal_payloads

        signal_payloads = compute_signal_payloads(market_snapshots=market_snapshots)

    snapshots = market_snapshots if market_snapshots is not None else list_signal_market_snapshots()
    hashed_signals = _attach_signal_hashes(signal_payloads, snapshots)
    return detect_confluence_setups(
        group_signals_by_asset(hashed_signals),
        market_snapshots=snapshots,
    )


def build_confluence_setup_views(
    *,
    signal_payloads: list[dict[str, Any]] | None = None,
    market_snapshots: list[dict[str, Any]] | None = None,
    plan: str = PLAN_FREE,
) -> list[ConfluenceSetupResponse]:
    snapshots = market_snapshots if market_snapshots is not None else list_signal_market_snapshots()
    payloads = compute_confluence_setup_payloads(
        signal_payloads=signal_payloads,
        market_snapshots=snapshots,
    )
    return build_setup_views(payloads, snapshots, plan=normalize_plan(plan))
