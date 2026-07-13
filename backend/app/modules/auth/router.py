import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.dependencies import (
    check_rate_limit,
    get_current_active_user,
    oauth2_scheme,
)
from app.modules.auth.models import User
from app.modules.auth.oauth import google_oauth
from app.modules.auth.schemas import (
    ForgotPasswordPayload,
    OAuthCallbackPayload,
    ResetPasswordPayload,
    Token,
    TokenRefresh,
    UserDetailOut,
    UserRegister,
    VerifyEmailPayload,
)
from app.modules.auth.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    create_verification_token,
)
from app.modules.auth.services import (
    authenticate_user,
    execute_password_reset,
    get_user_by_email,
    handle_google_user_provisioning,
    process_password_reset_request,
    register_user,
    verify_user_email,
)
from app.services.email.email_service import email_service
from app.services.redis_service import redis_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserDetailOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit(limit=5, window=60))],
)
async def register(
    register_data: UserRegister, db: AsyncSession = Depends(get_db)
) -> User:
    user = await register_user(db, register_data)
    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(check_rate_limit(limit=10, window=60))],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Check attempts & locking in DB
        attempts = await redis_service.increment_login_attempts(form_data.username)
        if attempts >= 5:
            # Enforce lock in Redis for double security
            logger_msg = f"Brute force detected in Redis for {form_data.username}"
            print(logger_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Success, reset attempts in Redis
    await redis_service.reset_login_attempts(user.email)

    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    _request: Request,
    _current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
) -> None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp", 0)
        import time

        now = int(time.time())
        expires_in = max(exp - now, 1)
        # Blacklist the current token in Redis
        await redis_service.blacklist_token(token, expires_in)
    except Exception:
        pass


@router.post("/refresh", response_model=Token)
async def refresh(
    refresh_data: TokenRefresh, db: AsyncSession = Depends(get_db)
) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            refresh_data.refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_type: str = payload.get("type", "")
        if token_type != "refresh":
            raise credentials_exception
        email: str = payload.get("sub", "")
        if not email:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        raise credentials_exception

    access_token = create_access_token(subject=user.email)
    new_refresh_token = create_refresh_token(subject=user.email)

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    payload: VerifyEmailPayload, db: AsyncSession = Depends(get_db)
) -> dict:
    success = await verify_user_email(db, payload.token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )
    return {"message": "Email verified successfully."}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if current_user.is_verified:
        return {"message": "Email is already verified."}
    v_token = create_verification_token(current_user.email)
    email_service.send_verification_email(current_user.email, v_token)
    return {"message": "Verification email resent successfully."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    payload: ForgotPasswordPayload, db: AsyncSession = Depends(get_db)
) -> dict:
    await process_password_reset_request(db, payload.email)
    return {"message": "If the account exists, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: ResetPasswordPayload, db: AsyncSession = Depends(get_db)
) -> dict:
    success = await execute_password_reset(db, payload.token, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    return {"message": "Password reset successfully."}


@router.get("/google/login")
async def google_login() -> dict:
    return {"url": google_oauth.get_google_auth_url()}


@router.post("/google/callback", response_model=Token)
async def google_callback(
    payload: OAuthCallbackPayload, db: AsyncSession = Depends(get_db)
) -> Token:
    profile = await google_oauth.verify_google_code(payload.code)
    user = await handle_google_user_provisioning(db, profile)

    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserDetailOut)
async def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
