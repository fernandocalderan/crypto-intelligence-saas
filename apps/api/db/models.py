from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(50), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signals: Mapped[list["SignalRecord"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["SubscriptionRecord"]] = relationship(back_populates="user")
    alert_subscriptions: Mapped[list["AlertSubscriptionRecord"]] = relationship(back_populates="user")
    alert_deliveries: Mapped[list["AlertDeliveryRecord"]] = relationship(back_populates="user")


class AssetRecord(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signals: Mapped[list["SignalRecord"]] = relationship(back_populates="asset")
    market_snapshots: Mapped[list["MarketSnapshotRecord"]] = relationship(back_populates="asset")


class SignalRecord(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True, index=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    asset_symbol: Mapped[str] = mapped_column(String(20), index=True)
    signal_key: Mapped[str] = mapped_column(String(120), index=True)
    signal_type: Mapped[str] = mapped_column(String(120))
    timeframe: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float)
    thesis: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="runtime")
    source_snapshot_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signal_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, server_default=func.now())

    asset: Mapped["AssetRecord"] = relationship(back_populates="signals")
    user: Mapped[UserRecord | None] = relationship(back_populates="signals")
    alert_deliveries: Mapped[list["AlertDeliveryRecord"]] = relationship(back_populates="signal")


class SetupRecord(Base):
    __tablename__ = "setups"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    asset_symbol: Mapped[str] = mapped_column(String(20), index=True)
    setup_key: Mapped[str] = mapped_column(String(120), index=True)
    setup_type: Mapped[str] = mapped_column(String(120))
    direction: Mapped[str] = mapped_column(String(20), index=True)
    signal_keys: Mapped[list[str]] = mapped_column(JSON, default=list)
    signal_hashes: Mapped[list[str]] = mapped_column(JSON, default=list)
    headline: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    execution_state: Mapped[str] = mapped_column(String(40), index=True)
    execution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    invalidation_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp1: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp2: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="ACTIVE")
    is_mock_contaminated: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_data: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_snapshot_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    tp1_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tp2_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class MarketSnapshotRecord(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    timeframe: Mapped[str] = mapped_column(String(20), default="1D")
    open_price: Mapped[float] = mapped_column(Float)
    high_price: Mapped[float] = mapped_column(Float)
    low_price: Mapped[float] = mapped_column(Float)
    close_price: Mapped[float] = mapped_column(Float)
    price_usd: Mapped[float] = mapped_column(Float)
    change_24h: Mapped[float] = mapped_column(Float)
    volume_24h: Mapped[float] = mapped_column(Float)
    avg_volume_24h: Mapped[float] = mapped_column(Float)
    range_high_20d: Mapped[float] = mapped_column(Float)
    range_low_20d: Mapped[float] = mapped_column(Float)
    funding_rate: Mapped[float] = mapped_column(Float)
    funding_zscore: Mapped[float] = mapped_column(Float)
    open_interest: Mapped[float] = mapped_column(Float)
    oi_change_24h: Mapped[float] = mapped_column(Float)
    long_liquidations_1h: Mapped[float] = mapped_column(Float)
    short_liquidations_1h: Mapped[float] = mapped_column(Float)
    avg_liquidations_1h: Mapped[float] = mapped_column(Float)
    momentum_score: Mapped[float] = mapped_column(Float)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    asset: Mapped["AssetRecord"] = relationship(back_populates="market_snapshots")


class SubscriptionRecord(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40), default="stripe")
    plan: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True, index=True)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        unique=True,
        index=True,
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["UserRecord"] = relationship(back_populates="subscriptions")


class AlertSubscriptionRecord(Base):
    __tablename__ = "alert_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", name="uq_alert_subscriptions_user_channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    min_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["UserRecord"] = relationship(back_populates="alert_subscriptions")


class AlertDeliveryRecord(Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        UniqueConstraint("signal_id", "user_id", "channel", name="uq_alert_deliveries_signal_user_channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    delivery_status: Mapped[str] = mapped_column(String(20), index=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signal: Mapped["SignalRecord"] = relationship(back_populates="alert_deliveries")
    user: Mapped["UserRecord"] = relationship(back_populates="alert_deliveries")
