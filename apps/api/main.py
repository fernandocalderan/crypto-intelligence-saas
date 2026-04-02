from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes.assets import router as assets_router
from routes.health import router as health_router
from routes.signals import router as signals_router

settings = get_settings()

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
app.include_router(assets_router)
app.include_router(signals_router)


@app.get("/", tags=["meta"])
def read_root() -> dict[str, str]:
    return {"service": "crypto-intelligence-api", "status": "ok"}

