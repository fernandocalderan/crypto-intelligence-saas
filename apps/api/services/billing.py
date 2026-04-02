import logging
from datetime import datetime, timezone
from uuid import uuid4

import stripe
from fastapi import HTTPException, status
from sqlalchemy import select

from config import get_settings
from db.models import SubscriptionRecord, UserRecord
from db.session import SessionLocal
from models.schemas import CheckoutResponse, SubscriptionResponse
from services.plans import PLAN_FREE, can_checkout, normalize_plan

logger = logging.getLogger(__name__)


def _has_real_value(value: str | None) -> bool:
    if not value:
        return False

    lowered = value.lower()
    return all(fragment not in lowered for fragment in ("placeholder", "your-", "replace-with"))


def _price_id_for_plan(plan: str) -> str:
    settings = get_settings()
    if plan == "pro":
        return settings.stripe_price_pro
    if plan == "pro_plus":
        return settings.stripe_price_pro_plus
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Plan no soportado para checkout",
    )


def _is_mock_checkout(plan: str) -> bool:
    settings = get_settings()
    if settings.enable_stripe_mock_checkout:
        return True

    return not (
        _has_real_value(settings.stripe_secret_key)
        and _has_real_value(_price_id_for_plan(plan))
    )


def _success_url() -> str:
    return f"{get_settings().app_base_url}/dashboard?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"


def _cancel_url(plan: str) -> str:
    return f"{get_settings().app_base_url}/pricing?checkout=canceled&plan={plan}"


def _find_subscription_by_checkout_session(session, user_id: int, session_id: str) -> SubscriptionRecord | None:
    return session.scalar(
        select(SubscriptionRecord)
        .where(
            SubscriptionRecord.user_id == user_id,
            SubscriptionRecord.stripe_checkout_session_id == session_id,
        )
        .order_by(SubscriptionRecord.updated_at.desc(), SubscriptionRecord.id.desc())
    )


def _upsert_subscription(
    session,
    *,
    user: UserRecord,
    plan: str,
    status_value: str,
    checkout_session_id: str,
    price_id: str | None,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    current_period_end: datetime | None = None,
    cancel_at_period_end: bool = False,
) -> SubscriptionRecord:
    subscription = _find_subscription_by_checkout_session(session, user.id, checkout_session_id)
    if subscription is None and stripe_subscription_id:
        subscription = session.scalar(
            select(SubscriptionRecord).where(
                SubscriptionRecord.stripe_subscription_id == stripe_subscription_id
            )
        )

    if subscription is None:
        subscription = SubscriptionRecord(
            user_id=user.id,
            provider="stripe",
            plan=plan,
            status=status_value,
            stripe_checkout_session_id=checkout_session_id,
        )
        session.add(subscription)

    subscription.plan = plan
    subscription.status = status_value
    subscription.stripe_checkout_session_id = checkout_session_id
    subscription.stripe_price_id = price_id
    subscription.stripe_customer_id = stripe_customer_id
    subscription.stripe_subscription_id = stripe_subscription_id
    subscription.current_period_end = current_period_end
    subscription.cancel_at_period_end = cancel_at_period_end
    user.plan = plan if status_value in {"active", "trialing", "paid"} else PLAN_FREE
    return subscription


def create_checkout_session(user: UserRecord, plan: str) -> CheckoutResponse:
    normalized_plan = normalize_plan(plan)
    if not can_checkout(normalized_plan):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo los planes Pro y Pro+ requieren checkout",
        )

    price_id = _price_id_for_plan(normalized_plan)
    settings = get_settings()

    with SessionLocal() as session:
        persistent_user = session.get(UserRecord, user.id)
        if persistent_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if _is_mock_checkout(normalized_plan):
            session_id = f"mock_cs_{uuid4().hex}"
            _upsert_subscription(
                session,
                user=persistent_user,
                plan=normalized_plan,
                status_value="pending",
                checkout_session_id=session_id,
                price_id="mock",
            )
            session.commit()
            return CheckoutResponse(
                checkout_url=f"{settings.app_base_url}/dashboard?checkout=success&session_id={session_id}",
                session_id=session_id,
                is_mock=True,
            )

        stripe.api_key = settings.stripe_secret_key
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            success_url=_success_url(),
            cancel_url=_cancel_url(normalized_plan),
            line_items=[{"price": price_id, "quantity": 1}],
            allow_promotion_codes=True,
            client_reference_id=str(persistent_user.id),
            customer_email=persistent_user.email,
            metadata={
                "user_id": str(persistent_user.id),
                "plan": normalized_plan,
            },
            subscription_data={
                "metadata": {
                    "user_id": str(persistent_user.id),
                    "plan": normalized_plan,
                }
            },
        )
        _upsert_subscription(
            session,
            user=persistent_user,
            plan=normalized_plan,
            status_value="pending",
            checkout_session_id=checkout_session.id,
            price_id=price_id,
            stripe_customer_id=checkout_session.customer,
        )
        session.commit()
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id,
            is_mock=False,
        )


def confirm_checkout_session(user: UserRecord, session_id: str) -> SubscriptionResponse:
    settings = get_settings()

    with SessionLocal() as session:
        persistent_user = session.get(UserRecord, user.id)
        if persistent_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        subscription = _find_subscription_by_checkout_session(session, persistent_user.id, session_id)
        if subscription is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkout session no encontrada",
            )

        if session_id.startswith("mock_cs_") or _is_mock_checkout(subscription.plan):
            _upsert_subscription(
                session,
                user=persistent_user,
                plan=subscription.plan,
                status_value="active",
                checkout_session_id=session_id,
                price_id=subscription.stripe_price_id,
            )
            session.commit()
            session.refresh(subscription)
            return SubscriptionResponse(
                plan=subscription.plan,
                status="active",
                checkout_session_id=session_id,
                current_period_end=subscription.current_period_end,
                cancel_at_period_end=subscription.cancel_at_period_end,
            )

        stripe.api_key = settings.stripe_secret_key
        checkout_session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["subscription"],
        )
        if checkout_session.status != "complete":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El checkout aún no está completado",
            )

        stripe_subscription = checkout_session.subscription
        current_period_end = None
        cancel_at_period_end = False
        stripe_subscription_id = None
        if stripe_subscription:
            stripe_subscription_id = stripe_subscription.id
            period_end = getattr(stripe_subscription, "current_period_end", None)
            if period_end:
                current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
            cancel_at_period_end = bool(getattr(stripe_subscription, "cancel_at_period_end", False))

        updated_subscription = _upsert_subscription(
            session,
            user=persistent_user,
            plan=subscription.plan,
            status_value="active",
            checkout_session_id=session_id,
            price_id=subscription.stripe_price_id,
            stripe_customer_id=checkout_session.customer,
            stripe_subscription_id=stripe_subscription_id,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )
        session.commit()
        session.refresh(updated_subscription)
        return SubscriptionResponse(
            plan=updated_subscription.plan,
            status=updated_subscription.status,
            checkout_session_id=updated_subscription.stripe_checkout_session_id,
            stripe_subscription_id=updated_subscription.stripe_subscription_id,
            current_period_end=updated_subscription.current_period_end,
            cancel_at_period_end=updated_subscription.cancel_at_period_end,
        )
