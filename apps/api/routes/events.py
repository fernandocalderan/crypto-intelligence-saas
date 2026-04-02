import logging

from fastapi import APIRouter, Depends

from models.schemas import TrackEventRequest
from services.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/track", status_code=202)
def track_event(payload: TrackEventRequest, user=Depends(get_current_user_optional)) -> dict[str, bool]:
    logger.info(
        "track_event event=%s context=%s user_id=%s properties=%s",
        payload.event,
        payload.context,
        getattr(user, "id", None),
        payload.properties,
    )
    return {"accepted": True}
