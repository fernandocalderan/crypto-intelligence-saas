from datetime import datetime
from typing import Any, Literal

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


class SignalConfirmation(BaseModel):
    label: str
    severity: Literal["positive", "warning", "negative"]


class SignalDataQualityWarning(BaseModel):
    code: str
    message: str
    severity: Literal["warning", "negative"] = "warning"


class SignalKeyData(BaseModel):
    price: float | None = None
    change_24h: float | None = None
    volume_24h: float | None = None
    funding: float | None = None
    oi_change_24h: float | None = None
    timeframe_base: str | None = None
    source: str | None = None


class SignalActionPlan(BaseModel):
    action_now: Literal["enter", "wait", "discard"]
    bias: str
    trigger_level: float | None = None
    invalidation_level: float | None = None
    tp1: float | None = None
    tp2: float | None = None
    levels_are_indicative: bool = True
    note: str | None = None


class SignalProPlusFollowUp(BaseModel):
    status: str
    note: str


class SetupSignalComponent(BaseModel):
    signal_key: str
    signal_type: str
    direction: str
    score: float
    confidence: float


class ProSignalResponse(SignalResponse):
    headline: str
    execution_state: Literal["EXECUTABLE", "WATCHLIST", "WAIT_CONFIRMATION", "DISCARD"] | None = None
    execution_reason: str | None = None
    summary: str | None = None
    model_score: float | None = None
    confidence_pct: float | None = None
    thesis_short: str | None = None
    key_data: SignalKeyData | None = None
    confirmations: list[SignalConfirmation] = Field(default_factory=list)
    action_plan: SignalActionPlan | None = None
    data_quality_warnings: list[SignalDataQualityWarning] = Field(default_factory=list)
    is_mock_contaminated: bool = False
    is_trade_executable: bool = False
    detail_level: Literal["teaser", "full"] = "full"
    source_snapshot_time: datetime | None = None
    pro_plus_follow_up: SignalProPlusFollowUp | None = None


class StoredSignalResponse(ProSignalResponse):
    signal_hash: str
    is_active: bool = True


class ConfluenceSetupResponse(BaseModel):
    setup_key: str
    setup_type: str
    asset_symbol: str
    direction: str
    signal_keys: list[str] = Field(default_factory=list)
    signals: list[SetupSignalComponent] = Field(default_factory=list)
    headline: str
    execution_state: Literal["EXECUTABLE", "WATCHLIST", "WAIT_CONFIRMATION", "DISCARD"] | None = None
    execution_reason: str | None = None
    summary: str | None = None
    thesis: str
    thesis_short: str | None = None
    score: float
    confidence: float
    model_score: float | None = None
    confidence_pct: float | None = None
    key_data: SignalKeyData | None = None
    confirmations: list[SignalConfirmation] = Field(default_factory=list)
    action_plan: SignalActionPlan | None = None
    data_quality_warnings: list[SignalDataQualityWarning] = Field(default_factory=list)
    is_mock_contaminated: bool = False
    is_trade_executable: bool = False
    generated_at: datetime
    source_snapshot_time: datetime | None = None
    detail_level: Literal["teaser", "full"] = "full"
    pro_plus_follow_up: SignalProPlusFollowUp | None = None


class SetupHistoryResponse(BaseModel):
    id: str
    asset_symbol: str
    setup_key: str
    setup_type: str
    headline: str
    direction: str
    status: Literal["ACTIVE", "TP1_HIT", "TP2_HIT", "INVALIDATED", "EXPIRED"]
    execution_state: Literal["EXECUTABLE", "WATCHLIST", "WAIT_CONFIRMATION", "DISCARD"]
    score: float
    confidence: float
    summary: str | None = None
    entry: float | None = None
    tp1: float | None = None
    tp2: float | None = None
    invalidation: float | None = None
    current_price: float | None = None
    is_mock_contaminated: bool = False
    created_at: datetime
    updated_at: datetime | None = None
    detail_level: Literal["teaser", "full"] = "full"


class SetupPerformanceBucket(BaseModel):
    setup_key: str
    setup_type: str
    total: int
    tp1_hit_pct: float
    tp2_hit_pct: float
    invalidated_pct: float


class SetupPerformanceResponse(BaseModel):
    total_setups: int
    active: int
    tp1_hit_pct: float
    tp2_hit_pct: float
    invalidated_pct: float
    avg_time_to_tp1_hours: float
    by_setup_type: list[SetupPerformanceBucket] = Field(default_factory=list)


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
    signals: list[ProSignalResponse]


class TrackEventRequest(BaseModel):
    event: str
    context: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class AlertsMeResponse(BaseModel):
    plan: str
    can_receive_alerts: bool
    alerts_globally_enabled: bool
    telegram_available: bool
    email_available: bool
    telegram_enabled: bool
    email_enabled: bool
    telegram_chat_id: str | None = None
    telegram_configured: bool = False
    email: str | None = None
    email_configured: bool = False
    min_score: float
    min_confidence: float
    effective_min_score: float
    effective_min_confidence_pct: float
    setup_min_score: float
    setup_min_confidence_pct: float


class AlertDeliveryDebugEntry(BaseModel):
    channel: str
    delivery_status: str
    provider_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    sent_at: datetime | None = None


class AlertsDebugResponse(BaseModel):
    plan: str
    can_receive_alerts: bool
    alerts_globally_enabled: bool
    telegram_available: bool
    bot_configured: bool
    telegram_subscription_active: bool
    telegram_enabled: bool
    telegram_chat_id_present: bool
    telegram_chat_id_masked: str | None = None
    min_score: float
    min_confidence: float
    effective_min_score: float
    effective_min_confidence_pct: float
    setup_min_score: float
    setup_min_confidence_pct: float
    alerts_process_on_scheduler: bool
    recent_deliveries_count: int
    recent_eligible_signal_count: int
    latest_sent: AlertDeliveryDebugEntry | None = None
    latest_failed: AlertDeliveryDebugEntry | None = None
    last_error_code: str | None = None
    last_error_known: str | None = None


class TelegramConnectRequest(BaseModel):
    telegram_chat_id: str | int
    is_active: bool | None = True


class AlertPreferencesRequest(BaseModel):
    min_score: float | None = None
    min_confidence: float | None = None
    telegram_enabled: bool | None = None
    email_enabled: bool | None = None


class TelegramTestResponse(BaseModel):
    ok: bool = True
    detail: str
    telegram_chat_id: str
    telegram_enabled: bool
    provider_message_id: str | None = None


class TelegramConnectInstructionsResponse(BaseModel):
    bot_username: str | None = None
    start_command: str = "/start"
    steps: list[str] = Field(default_factory=list)
    note: str
