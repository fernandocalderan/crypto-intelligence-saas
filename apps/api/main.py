import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db.init_db import init_db
from routes.auth import router as auth_router
from routes.assets import router as assets_router
from routes.billing import router as billing_router
from routes.events import router as events_router
from routes.health import router as health_router
from routes.market import router as market_router
from routes.signals import router as signals_router
from services.market_data.scheduler import (
    run_market_data_job,
    start_market_data_scheduler,
    stop_market_data_scheduler,
)

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Crypto Intelligence API",
    description="Backend API for market data, scoring and crypto signals.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(assets_router)
app.include_router(signals_router)
app.include_router(market_router)
app.include_router(billing_router)
app.include_router(events_router)


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
    except Exception as exc:
        logger.warning("Database initialization skipped: %s", exc)

    if settings.enable_market_data_scheduler:
        start_market_data_scheduler()

    if settings.market_data_run_initial_sync:
        run_market_data_job()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_market_data_scheduler()


@app.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"service": "crypto-intelligence-api", "status": "ok"}
