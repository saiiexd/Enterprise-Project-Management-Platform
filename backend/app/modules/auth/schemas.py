import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class PermissionOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class UserOrganizationOut(BaseModel):
    organization: OrganizationOut
    role_name: str
    role: RoleOut | None = None

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str | None = None
    organization_name: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    provider: str
    profile_image_url: str | None = None
    is_active: bool
    is_verified: bool
    is_superuser: bool
    account_status: bool | str  # Accept bool or str during transition
    created_at: datetime

    class Config:
        from_attributes = True


class UserDetailOut(UserOut):
    organizations: list[UserOrganizationOut] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None
    type: str | None = None


class TokenRefresh(BaseModel):
    refresh_token: str


class VerifyEmailPayload(BaseModel):
    token: str


class ForgotPasswordPayload(BaseModel):
    email: EmailStr


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class OAuthCallbackPayload(BaseModel):
    code: str
