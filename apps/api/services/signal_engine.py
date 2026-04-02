from datetime import datetime, timezone

from models.schemas import SignalResponse

NOW = datetime.now(timezone.utc)

MOCK_SIGNALS = [
    SignalResponse(
        id="sig-btc-breakout",
        asset_symbol="BTC",
        signal_type="Momentum Breakout",
        timeframe="4H",
        confidence=89.0,
        score=92.0,
        thesis="BTC rompe rango con expansión de volumen y funding todavía lejos de euforia.",
        generated_at=NOW,
    ),
    SignalResponse(
        id="sig-eth-rotation",
        asset_symbol="ETH",
        signal_type="Capital Rotation",
        timeframe="1D",
        confidence=76.0,
        score=81.0,
        thesis="ETH muestra rotación positiva frente a BTC mientras mejora el flujo hacia majors.",
        generated_at=NOW,
    ),
    SignalResponse(
        id="sig-sol-strength",
        asset_symbol="SOL",
        signal_type="Relative Strength",
        timeframe="1D",
        confidence=82.0,
        score=86.0,
        thesis="SOL mantiene liderazgo relativo frente al mercado amplio y confirma continuidad de tendencia.",
        generated_at=NOW,
    ),
]


def list_signals() -> list[SignalResponse]:
    return MOCK_SIGNALS

