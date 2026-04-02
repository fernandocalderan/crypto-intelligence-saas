import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Header, HTTPException, status
from sqlalchemy import select

from config import get_settings
from db.models import SubscriptionRecord, UserRecord
from db.session import SessionLocal
from models.schemas import AuthResponse, UserProfile
from services.plans import can_access_all_signals, get_signal_limit, normalize_plan

PBKDF2_ITERATIONS = 390_000
TOKEN_TTL = timedelta(days=14)


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", maxsplit=1)
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return secrets.compare_digest(candidate, digest)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _sign_payload(payload: str) -> str:
    secret = get_settings().auth_secret.encode("utf-8")
    digest = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).digest()
    return _urlsafe_b64encode(digest)


def create_auth_token(user: UserRecord) -> str:
    expires_at = datetime.now(timezone.utc) + TOKEN_TTL
    payload = {
        "sub": user.id,
        "email": user.email,
        "exp": int(expires_at.timestamp()),
    }
    encoded_payload = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign_payload(encoded_payload)
    return f"{encoded_payload}.{signature}"


def decode_auth_token(token: str) -> dict[str, Any]:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        ) from exc

    expected_signature = _sign_payload(encoded_payload)
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session signature",
        )

    payload = json.loads(_urlsafe_b64decode(encoded_payload))
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    return payload


def _latest_subscription_for_user(session, user_id: int) -> SubscriptionRecord | None:
    return session.scalar(
        select(SubscriptionRecord)
        .where(SubscriptionRecord.user_id == user_id)
        .order_by(SubscriptionRecord.updated_at.desc(), SubscriptionRecord.id.desc())
    )


def build_user_profile(user: UserRecord, session=None) -> UserProfile:
    owns_session = session is None
    current_session = session or SessionLocal()

    try:
        subscription = _latest_subscription_for_user(current_session, user.id)
        plan = normalize_plan(user.plan)
        return UserProfile(
            id=user.id,
            email=user.email,
            plan=plan,
            is_active=user.is_active,
            subscription_status=subscription.status if subscription else None,
            signal_limit=get_signal_limit(plan),
            can_access_all_signals=can_access_all_signals(plan),
        )
    finally:
        if owns_session:
            current_session.close()


def issue_auth_response(user: UserRecord, session=None) -> AuthResponse:
    return AuthResponse(
        token=create_auth_token(user),
        user=build_user_profile(user, session=session),
    )


def create_user(email: str, password: str) -> AuthResponse:
    normalized_email = _normalize_email(email)
    if len(password.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La password debe tener al menos 8 caracteres",
        )

    with SessionLocal() as session:
        existing_user = session.scalar(
            select(UserRecord).where(UserRecord.email == normalized_email)
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con ese email",
            )

        user = UserRecord(
            email=normalized_email,
            password_hash=hash_password(password),
            plan="free",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return issue_auth_response(user, session=session)


def authenticate_user(email: str, password: str) -> AuthResponse:
    normalized_email = _normalize_email(email)

    with SessionLocal() as session:
        user = session.scalar(select(UserRecord).where(UserRecord.email == normalized_email))
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La cuenta está desactivada",
            )
        return issue_auth_response(user, session=session)


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _load_user_from_token(token: str) -> UserRecord:
    payload = decode_auth_token(token)
    user_id = int(payload["sub"])

    with SessionLocal() as session:
        user = session.get(UserRecord, user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User session not found",
            )
        session.expunge(user)
        return user


def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
) -> UserRecord | None:
    token = _extract_bearer_token(authorization)
    if token is None:
        return None
    return _load_user_from_token(token)


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> UserRecord:
    token = _extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return _load_user_from_token(token)
