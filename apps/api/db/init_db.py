from sqlalchemy import select

from db.base import Base
from db.models import AssetRecord
from db.session import SessionLocal, engine

DEFAULT_ASSETS = [
    {"symbol": "BTC", "name": "Bitcoin", "category": "Layer 1"},
    {"symbol": "ETH", "name": "Ethereum", "category": "Layer 1"},
    {"symbol": "SOL", "name": "Solana", "category": "Layer 1"},
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        existing_symbols = {
            symbol for symbol in session.scalars(select(AssetRecord.symbol)).all()
        }
        for asset in DEFAULT_ASSETS:
            if asset["symbol"] not in existing_symbols:
                session.add(AssetRecord(**asset))
        session.commit()


if __name__ == "__main__":
    init_db()

