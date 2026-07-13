import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    logo_url: str | None = Field(None, max_length=1024)
    settings: dict | None = None

class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    logo_url: str | None = Field(None, max_length=1024)
    status: str | None = Field(None, max_length=50)

class OrganizationSettingsUpdate(BaseModel):
    timezone: str | None = "UTC"
    locale: str | None = "en"
    working_days: list[int] | None = [1, 2, 3, 4, 5]
    business_hours: dict | None = {"start": "09:00", "end": "17:00"}
    branding: dict | None = {"primary_color": "#4F46E5", "logo_url": None}

class OrganizationMemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str | None
    role_name: str
    invitation_status: str
    joined_at: datetime

    class Config:
        from_attributes = True

class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    status: str
    subscription_tier: str
    subscription_status: str
    owner_id: uuid.UUID | None
    settings: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
