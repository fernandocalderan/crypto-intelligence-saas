from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    signal_key: str
    asset_symbol: str
    signal_type: str
    timeframe: str
    direction: str
    confidence: float
    score: float
    thesis: str
    evidence: list[str] = Field(default_factory=list)
    source: str = "mock"
    generated_at: datetime


class MarketSnapshotResponse(BaseModel):
    symbol: str
    name: str
    category: str
    source: str
    timeframe: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    price_usd: float
    change_24h: float
    volume_24h: float
    avg_volume_24h: float
    range_high_20d: float
    range_low_20d: float
    funding_rate: float
    funding_zscore: float
    open_interest: float
    oi_change_24h: float
    long_liquidations_1h: float
    short_liquidations_1h: float
    avg_liquidations_1h: float
    momentum_score: float
    captured_at: datetime


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    email: str
    plan: str = "free"
    is_active: bool = True
    subscription_status: str | None = None
    signal_limit: int | None = None
    can_access_all_signals: bool = False


class AuthCredentials(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile


class SubscriptionResponse(BaseModel):
    provider: str = "stripe"
    plan: str
    status: str
    checkout_session_id: str | None = None
    stripe_subscription_id: str | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False


class CheckoutRequest(BaseModel):
    plan: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    is_mock: bool = False


class CheckoutConfirmRequest(BaseModel):
    session_id: str


class SignalFeedResponse(BaseModel):
    access_plan: str
    total_available: int
    visible_count: int
    has_locked_signals: bool
    signals: list[SignalResponse]


class TrackEventRequest(BaseModel):
    event: str
    context: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
