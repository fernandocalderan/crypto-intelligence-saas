from fastapi import APIRouter

from models.schemas import AssetResponse
from services.market_data import list_assets

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetResponse])
def get_assets() -> list[AssetResponse]:
    return list_assets()

