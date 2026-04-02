from fastapi import APIRouter, Depends

from db.session import get_db
from models.schemas import (
    ConfluenceSetupResponse,
    ProSignalResponse,
    SetupHistoryResponse,
    SetupPerformanceResponse,
    SignalFeedResponse,
)
from services.auth import get_current_user_optional
from services.plans import PLAN_FREE
from services.signal_engine import get_signal_feed, list_live_setups, list_live_signals, list_signals
from services.setup_engine import get_setup_performance, list_setup_history
from sqlalchemy.orm import Session

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[ProSignalResponse])
def get_signals() -> list[ProSignalResponse]:
    return list_signals()


@router.get("/live", response_model=list[ProSignalResponse])
def get_live_signals(user=Depends(get_current_user_optional)) -> list[ProSignalResponse]:
    plan = getattr(user, "plan", PLAN_FREE)
    return list_live_signals(plan=plan)


@router.get("/setups", response_model=list[ConfluenceSetupResponse])
def get_live_setups(user=Depends(get_current_user_optional)) -> list[ConfluenceSetupResponse]:
    plan = getattr(user, "plan", PLAN_FREE)
    return list_live_setups(plan=plan)


@router.get("/setups/history", response_model=list[SetupHistoryResponse])
def get_setups_history(
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> list[SetupHistoryResponse]:
    plan = getattr(user, "plan", PLAN_FREE)
    return list_setup_history(db, plan=plan, limit=50)


@router.get("/setups/performance", response_model=SetupPerformanceResponse)
def get_setups_performance(
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> SetupPerformanceResponse:
    plan = getattr(user, "plan", PLAN_FREE)
    return get_setup_performance(db, plan=plan)


@router.get("/feed", response_model=SignalFeedResponse)
def get_live_signal_feed(user=Depends(get_current_user_optional)) -> SignalFeedResponse:
    plan = getattr(user, "plan", PLAN_FREE)
    return get_signal_feed(plan=plan)
