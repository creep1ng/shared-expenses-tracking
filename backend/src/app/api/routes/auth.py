from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies.auth import get_auth_service, get_current_user
from app.core.config import Settings, get_settings
from app.db.models import User
from app.schemas.auth import (
    AuthenticatedUserResponse,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    SignInRequest,
    SignUpRequest,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-up", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def sign_up(
    payload: SignUpRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = auth_service.sign_up(
        email=payload.email,
        password=payload.password.get_secret_value(),
    )
    return UserResponse.model_validate(user)


@router.post("/sign-in", response_model=AuthenticatedUserResponse)
def sign_in(
    payload: SignInRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUserResponse:
    user, session_data = auth_service.sign_in(
        email=payload.email,
        password=payload.password.get_secret_value(),
    )
    _set_session_cookie(response, session_data.session_id, settings)
    return AuthenticatedUserResponse(user=UserResponse.model_validate(user))


@router.post("/sign-out", response_model=MessageResponse)
def sign_out(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    auth_service.sign_out(request.cookies.get(settings.auth_cookie_name))
    _clear_session_cookie(response, settings)
    return MessageResponse(message="Signed out successfully.")


@router.get("/me", response_model=AuthenticatedUserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(user=UserResponse.model_validate(current_user))


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> PasswordResetRequestResponse:
    result = auth_service.request_password_reset(email=payload.email)
    return PasswordResetRequestResponse(
        message="If the account exists, a reset token has been issued.",
        reset_token=result.token,
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    auth_service.confirm_password_reset(
        token=payload.token,
        new_password=payload.new_password.get_secret_value(),
    )
    return MessageResponse(message="Password reset completed successfully.")


def _set_session_cookie(response: Response, session_id: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.auth_session_ttl_seconds,
        domain=settings.auth_cookie_domain,
        path="/",
    )


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        domain=settings.auth_cookie_domain,
        path="/",
    )
