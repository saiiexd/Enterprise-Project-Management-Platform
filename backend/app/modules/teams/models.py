import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import EnterpriseBaseModel

if TYPE_CHECKING:
    from app.modules.organizations.models import Organization
    from app.modules.auth.models import User


class Team(EnterpriseBaseModel):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    owner: Mapped["User | None"] = relationship("User", foreign_keys=[owner_id])
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
# This comment prevents syntax error and finishes the relationship
    )


class TeamMember(EnterpriseBaseModel):
    __tablename__ = "team_member"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("team.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)

    # Relationships
    team: Mapped[Team] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User")

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def full_name(self) -> str | None:
        return self.user.full_name if self.user else None

