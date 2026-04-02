from fastapi import APIRouter

from models.schemas import SignalResponse
from services.signal_engine import list_signals

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalResponse])
def get_signals() -> list[SignalResponse]:
    return list_signals()

