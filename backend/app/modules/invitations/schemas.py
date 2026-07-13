import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class InvitationCreate(BaseModel):
    email: EmailStr
    role_name: str = Field("member", max_length=50)

class InvitationAccept(BaseModel):
    token: str

class InvitationReject(BaseModel):
    token: str

class InvitationOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role_name: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationPagination(BaseModel):
    invitations: list[InvitationOut]
    total: int

