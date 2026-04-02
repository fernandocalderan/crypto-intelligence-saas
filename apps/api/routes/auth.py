from fastapi import APIRouter, Depends

from models.schemas import AuthCredentials, AuthResponse, UserProfile
from services.auth import (
    authenticate_user,
    build_user_profile,
    create_user,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(credentials: AuthCredentials) -> AuthResponse:
    return create_user(credentials.email, credentials.password)


@router.post("/login", response_model=AuthResponse)
def login(credentials: AuthCredentials) -> AuthResponse:
    return authenticate_user(credentials.email, credentials.password)


@router.get("/me", response_model=UserProfile)
def me(user=Depends(get_current_user)) -> UserProfile:
    return build_user_profile(user)
