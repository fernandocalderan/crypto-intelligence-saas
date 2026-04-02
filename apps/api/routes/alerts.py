from fastapi import APIRouter, Depends

from models.schemas import AlertPreferencesRequest, AlertsMeResponse, TelegramConnectRequest
from services.alert_engine import (
    get_alert_settings_for_user,
    upsert_telegram_subscription,
    update_user_alert_preferences,
)
from services.auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/me", response_model=AlertsMeResponse)
def get_my_alerts(user=Depends(get_current_user)) -> AlertsMeResponse:
    return get_alert_settings_for_user(user)


@router.post("/telegram/connect", response_model=AlertsMeResponse)
def connect_telegram_alerts(
    payload: TelegramConnectRequest,
    user=Depends(get_current_user),
) -> AlertsMeResponse:
    return upsert_telegram_subscription(
        user,
        telegram_chat_id=payload.telegram_chat_id,
        is_active=payload.is_active,
    )


@router.post("/preferences", response_model=AlertsMeResponse)
def update_alerts_preferences(
    payload: AlertPreferencesRequest,
    user=Depends(get_current_user),
) -> AlertsMeResponse:
    return update_user_alert_preferences(
        user,
        min_score=payload.min_score,
        min_confidence=payload.min_confidence,
        telegram_enabled=payload.telegram_enabled,
        email_enabled=payload.email_enabled,
    )
