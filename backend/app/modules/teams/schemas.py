import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    organization_id: uuid.UUID

class TeamUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)

class TeamMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str | None = "member"

class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    organization_id: uuid.UUID
    owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamMemberOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    email: str
    full_name: str | None

    class Config:
        from_attributes = True


class TeamPagination(BaseModel):
    teams: list[TeamOut]
    total: int


class TeamMemberPagination(BaseModel):
    members: list[TeamMemberOut]
    total: int

