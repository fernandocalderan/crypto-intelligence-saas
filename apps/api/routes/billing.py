from fastapi import APIRouter, Depends

from models.schemas import (
    CheckoutConfirmRequest,
    CheckoutRequest,
    CheckoutResponse,
    SubscriptionResponse,
)
from services.auth import get_current_user
from services.billing import confirm_checkout_session, create_checkout_session

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(payload: CheckoutRequest, user=Depends(get_current_user)) -> CheckoutResponse:
    return create_checkout_session(user, payload.plan)


@router.post("/confirm", response_model=SubscriptionResponse)
def confirm_checkout(
    payload: CheckoutConfirmRequest,
    user=Depends(get_current_user),
) -> SubscriptionResponse:
    return confirm_checkout_session(user, payload.session_id)
