from datetime import datetime, timezone

from fastapi import APIRouter

from config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "crypto-intelligence-api",
        "environment": settings.app_env,
        "database_configured": bool(settings.database_url),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

