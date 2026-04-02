from fastapi import APIRouter, Depends

from models.schemas import SignalFeedResponse, SignalResponse
from services.auth import get_current_user_optional
from services.plans import PLAN_FREE
from services.signal_engine import get_signal_feed, list_live_signals, list_signals

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalResponse])
def get_signals() -> list[SignalResponse]:
    return list_signals()


@router.get("/live", response_model=list[SignalResponse])
def get_live_signals(user=Depends(get_current_user_optional)) -> list[SignalResponse]:
    plan = getattr(user, "plan", PLAN_FREE)
    return list_live_signals(plan=plan)


@router.get("/feed", response_model=SignalFeedResponse)
def get_live_signal_feed(user=Depends(get_current_user_optional)) -> SignalFeedResponse:
    plan = getattr(user, "plan", PLAN_FREE)
    return get_signal_feed(plan=plan)
