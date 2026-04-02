from fastapi import APIRouter

from models.schemas import MarketSnapshotResponse
from services.market_data import list_latest_market_snapshots

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/latest", response_model=list[MarketSnapshotResponse])
def get_latest_market_snapshots() -> list[MarketSnapshotResponse]:
    return [MarketSnapshotResponse(**snapshot) for snapshot in list_latest_market_snapshots()]
