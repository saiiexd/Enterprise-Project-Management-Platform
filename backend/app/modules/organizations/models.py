import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, EnterpriseBaseModel

if TYPE_CHECKING:
    from app.modules.auth.models import User, Role


class Organization(EnterpriseBaseModel):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    # Subscription fields
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    # Owner reference
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    
    # Settings (JSON for future extensibility)
    settings: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    members: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember", back_populates="organization", cascade="all, delete-orphan"
    )
    owner: Mapped["User | None"] = relationship("User", foreign_keys=[owner_id])


class OrganizationMember(EnterpriseBaseModel):
    __tablename__ = "organization_member"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role.id", ondelete="SET NULL"), nullable=True
    )
    role_name: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    
    # Membership specifics
    invitation_status: Mapped[str] = mapped_column(String(50), default="accepted", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    activity_metadata: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="organizations")
    organization: Mapped[Organization] = relationship("Organization", back_populates="members")
    role: Mapped["Role | None"] = relationship("Role")
