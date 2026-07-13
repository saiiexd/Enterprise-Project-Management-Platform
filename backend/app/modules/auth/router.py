import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.auth.schemas import Token, TokenRefresh, UserDetailOut, UserRegister
from app.modules.auth.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
)
from app.modules.auth.services import (
    authenticate_user,
    get_user_by_email,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserDetailOut, status_code=status.HTTP_201_CREATED
)
async def register(
    register_data: UserRegister, db: AsyncSession = Depends(get_db)
) -> User:
    user = await register_user(db, register_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)

    return Token(access_token=access_token, refresh_token=refresh_token)


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
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise credentials_exception

    access_token = create_access_token(subject=user.email)
    # Generate new refresh token to implement sliding session security
    new_refresh_token = create_refresh_token(subject=user.email)

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserDetailOut)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user
