from datetime import UTC, datetime, timedelta
from typing import Annotated
from urllib.parse import urlparse

import jwt
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth import (
    AuthenticateUser,
    AuthenticationError,
    RegisterUser,
    RegisterUserCommand,
)
from app.core.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.tokens import RefreshTokenRepository
from app.infrastructure.repositories.users import SqlAlchemyUserRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _validate_csrf_origin(origin: str | None, referer: str | None) -> None:
    source = origin or referer
    if source is None:
        raise HTTPException(status_code=403, detail="CSRF validation failed")
    value = source if origin else f"{urlparse(source).scheme}://{urlparse(source).netloc}"
    if value not in settings.CORS_ORIGINS:
        raise HTTPException(status_code=403, detail="CSRF validation failed")


def _create_access_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    use_case = RegisterUser(SqlAlchemyUserRepository(session))
    try:
        user = await use_case.execute(RegisterUserCommand(**request.model_dump()))
    except (AuthenticationError, IntegrityError) as error:
        if isinstance(error, AuthenticationError):
            raise HTTPException(status_code=409, detail=str(error)) from error
        raise HTTPException(
            status_code=409, detail="Username or email is already registered"
        ) from error
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
) -> TokenResponse:
    use_case = AuthenticateUser(SqlAlchemyUserRepository(session))
    try:
        user = await use_case.execute(request.login, request.password)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=401, detail="Invalid credentials") from error
    refresh_token = await RefreshTokenRepository(session).issue(user.id)
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
    )
    return TokenResponse(
        access_token=_create_access_token(str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
    origin: Annotated[str | None, Header()] = None,
    referer: Annotated[str | None, Header()] = None,
) -> TokenResponse:
    _validate_csrf_origin(origin, referer)
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    rotated = await RefreshTokenRepository(session).rotate(refresh_token)
    if rotated is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id, replacement = rotated
    user = await SqlAlchemyUserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(
        "refresh_token",
        replacement,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
    )
    return TokenResponse(
        access_token=_create_access_token(str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Response:
    if refresh_token is not None:
        await RefreshTokenRepository(session).revoke(refresh_token)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("refresh_token")
    return response


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[object, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
