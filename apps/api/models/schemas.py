from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssetResponse(BaseModel):
    symbol: str
    name: str
    category: str
    price_usd: float
    change_24h: float
    volume_24h: float
    momentum_score: float


class SignalResponse(BaseModel):
    id: str
    asset_symbol: str
    signal_type: str
    timeframe: str
    confidence: float
    score: float
    thesis: str
    generated_at: datetime


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    email: str
    plan: str = "starter"
    is_active: bool = True
