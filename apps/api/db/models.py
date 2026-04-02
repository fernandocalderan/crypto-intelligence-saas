from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
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
    public_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    signal_type: Mapped[str] = mapped_column(String(120))
    timeframe: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float)
    thesis: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    asset: Mapped["AssetRecord"] = relationship(back_populates="signals")
    user: Mapped[UserRecord | None] = relationship(back_populates="signals")


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
