from sqlalchemy import inspect, select, text, update

from db.base import Base
from db.models import AssetRecord, UserRecord
from db.session import SessionLocal, engine

DEFAULT_ASSETS = [
    {"symbol": "BTC", "name": "Bitcoin", "category": "Layer 1"},
    {"symbol": "ETH", "name": "Ethereum", "category": "Layer 1"},
    {"symbol": "SOL", "name": "Solana", "category": "Layer 1"},
    {"symbol": "DOGE", "name": "Dogecoin", "category": "Meme"},
    {"symbol": "XRP", "name": "XRP", "category": "Payments"},
]

SIGNAL_SCHEMA_PATCHES = [
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS asset_symbol VARCHAR(20)",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS signal_key VARCHAR(120)",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS direction VARCHAR(20)",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS evidence_json JSON",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS source VARCHAR(80) DEFAULT 'runtime'",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS source_snapshot_time TIMESTAMPTZ",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS signal_hash VARCHAR(64)",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
]

SIGNAL_SCHEMA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_signals_asset_symbol ON signals (asset_symbol)",
    "CREATE INDEX IF NOT EXISTS ix_signals_signal_key ON signals (signal_key)",
    "CREATE INDEX IF NOT EXISTS ix_signals_timeframe ON signals (timeframe)",
    "CREATE INDEX IF NOT EXISTS ix_signals_created_at ON signals (created_at)",
    "CREATE INDEX IF NOT EXISTS ix_signals_is_active ON signals (is_active)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_signals_signal_hash ON signals (signal_hash) WHERE signal_hash IS NOT NULL",
]

SETUP_SCHEMA_PATCHES = [
    "ALTER TABLE setups ADD COLUMN IF NOT EXISTS tp1_hit_at TIMESTAMPTZ",
    "ALTER TABLE setups ADD COLUMN IF NOT EXISTS tp2_hit_at TIMESTAMPTZ",
    "ALTER TABLE setups ADD COLUMN IF NOT EXISTS invalidated_at TIMESTAMPTZ",
    "ALTER TABLE setups ADD COLUMN IF NOT EXISTS expired_at TIMESTAMPTZ",
]

SETUP_SCHEMA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_setups_status ON setups (status)",
    "CREATE INDEX IF NOT EXISTS ix_setups_setup_key ON setups (setup_key)",
    "CREATE INDEX IF NOT EXISTS ix_setups_asset_symbol ON setups (asset_symbol)",
]

ALERT_DELIVERY_SCHEMA_PATCHES = [
    "ALTER TABLE alert_deliveries ADD COLUMN IF NOT EXISTS error_code VARCHAR(120)",
]

ALERT_DELIVERY_SCHEMA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_alert_deliveries_error_code ON alert_deliveries (error_code)",
]


def _patch_signal_schema() -> None:
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    if "signals" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        for statement in SIGNAL_SCHEMA_PATCHES:
            connection.execute(text(statement))

        connection.execute(
            text(
                """
                UPDATE signals
                SET asset_symbol = assets.symbol
                FROM assets
                WHERE signals.asset_symbol IS NULL
                  AND signals.asset_id = assets.id
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE signals
                SET signal_key = COALESCE(signal_key, lower(replace(signal_type, ' ', '_')), 'legacy_signal')
                WHERE signal_key IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE signals
                SET direction = COALESCE(direction, 'neutral'),
                    evidence_json = COALESCE(evidence_json, '[]'::json),
                    source = COALESCE(source, 'runtime'),
                    source_snapshot_time = COALESCE(source_snapshot_time, created_at),
                    is_active = COALESCE(is_active, TRUE)
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE signals
                SET signal_hash = md5(
                    concat_ws(
                        '|',
                        COALESCE(asset_symbol, 'unknown'),
                        COALESCE(signal_key, 'legacy_signal'),
                        COALESCE(timeframe, 'unknown'),
                        COALESCE(direction, 'neutral'),
                        to_char(date_trunc('minute', COALESCE(source_snapshot_time, created_at)), 'YYYY-MM-DD"T"HH24:MI')
                    )
                )
                WHERE signal_hash IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE signals
                SET public_id = COALESCE(public_id, signal_hash)
                WHERE public_id IS NULL
                """
            )
        )

        for statement in SIGNAL_SCHEMA_INDEXES:
            connection.execute(text(statement))


def _patch_setup_schema() -> None:
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    if "setups" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        for statement in SETUP_SCHEMA_PATCHES:
            connection.execute(text(statement))

        for statement in SETUP_SCHEMA_INDEXES:
            connection.execute(text(statement))


def _patch_alert_delivery_schema() -> None:
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    if "alert_deliveries" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        for statement in ALERT_DELIVERY_SCHEMA_PATCHES:
            connection.execute(text(statement))

        for statement in ALERT_DELIVERY_SCHEMA_INDEXES:
            connection.execute(text(statement))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _patch_signal_schema()
    _patch_setup_schema()
    _patch_alert_delivery_schema()

    with SessionLocal() as session:
        existing_symbols = {
            symbol for symbol in session.scalars(select(AssetRecord.symbol)).all()
        }
        for asset in DEFAULT_ASSETS:
            if asset["symbol"] not in existing_symbols:
                session.add(AssetRecord(**asset))
        session.execute(
            update(UserRecord)
            .where(UserRecord.plan == "starter")
            .values(plan="free")
        )
        session.commit()


if __name__ == "__main__":
    init_db()
