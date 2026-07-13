import uuid
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.modules.teams.models import Team, TeamMember
from app.modules.teams.schemas import TeamCreate, TeamUpdate
from app.modules.auth.models import User
from app.modules.audit_logs.services import AuditLogService

class TeamService:
    @staticmethod
    async def create_team(db: AsyncSession, data: TeamCreate, creator_id: uuid.UUID) -> Team:
        team = Team(
            name=data.name,
            description=data.description,
            organization_id=data.organization_id,
            owner_id=creator_id,
            created_by_id=creator_id
        )
        db.add(team)
        await db.flush()

        # Add creator as a Team member (role Lead/Owner)
        member = TeamMember(
            team_id=team.id,
            user_id=creator_id,
            role="lead",
            created_by_id=creator_id
        )
        db.add(member)
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=creator_id,
            organization_id=data.organization_id,
            action="team:create",
            resource_type="team",
            resource_id=str(team.id),
            details={"name": team.name}
        )
        return team

    @staticmethod
    async def get_team(db: AsyncSession, team_id: uuid.UUID) -> Team | None:
        stmt = select(Team).where(Team.id == team_id, Team.is_deleted == False)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_teams(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Team], int]:
        stmt = select(Team).where(Team.organization_id == org_id, Team.is_deleted == False)
        if search:
            stmt = stmt.where(Team.name.ilike(f"%{search}%"))

        res_all = await db.execute(stmt)
        all_teams = res_all.scalars().all()

        paginated = all_teams[skip : skip + limit]
        return list(paginated), len(all_teams)

    @staticmethod
    async def update_team(
        db: AsyncSession, team_id: uuid.UUID, data: TeamUpdate, updater_id: uuid.UUID
    ) -> Team:
        team = await TeamService.get_team(db, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(team, k, v)
        team.updated_by_id = updater_id
        team.updated_at = datetime.utcnow()
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=updater_id,
            organization_id=team.organization_id,
            action="team:update",
            resource_type="team",
            resource_id=str(team.id),
            details=update_dict
        )
        return team

    @staticmethod
    async def delete_team(db: AsyncSession, team_id: uuid.UUID, deleter_id: uuid.UUID) -> None:
        team = await TeamService.get_team(db, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        team.is_deleted = True
        team.deleted_at = datetime.utcnow()
        team.updated_by_id = deleter_id
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=deleter_id,
            organization_id=team.organization_id,
            action="team:delete",
            resource_type="team",
            resource_id=str(team.id)
        )

    @staticmethod
    async def add_member(
        db: AsyncSession, team_id: uuid.UUID, user_id: uuid.UUID, role: str, adder_id: uuid.UUID
    ) -> TeamMember:
        team = await TeamService.get_team(db, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        # Check if already a member
        stmt = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this team")

        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            created_by_id=adder_id
        )
        db.add(member)
        await db.commit()

        # Reload with selectinload to populate member.user
        stmt_member = select(TeamMember).options(selectinload(TeamMember.user)).where(TeamMember.id == member.id)
        res_member = await db.execute(stmt_member)
        member = res_member.scalar_one()

        await AuditLogService.log_event(
            db=db,
            user_id=adder_id,
            organization_id=team.organization_id,
            action="team:member_add",
            resource_type="team",
            resource_id=str(team_id),
            details={"user_id": str(user_id), "role": role}
        )
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession, team_id: uuid.UUID, user_id: uuid.UUID, remover_id: uuid.UUID
    ) -> None:
        team = await TeamService.get_team(db, team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        stmt = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        res = await db.execute(stmt)
        member = res.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in team")

        await db.delete(member)
        await db.commit()

        await AuditLogService.log_event(
            db=db,
            user_id=remover_id,
            organization_id=team.organization_id,
            action="team:member_remove",
            resource_type="team",
            resource_id=str(team_id),
            details={"user_id": str(user_id)}
        )

    @staticmethod
    async def list_members(
        db: AsyncSession, team_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[dict], int]:
        stmt = select(TeamMember).join(User).where(TeamMember.team_id == team_id)
        res_all = await db.execute(stmt.options(selectinload(TeamMember.user)))
        all_members = res_all.scalars().all()

        paginated = all_members[skip : skip + limit]
        out = []
        for m in paginated:
            out.append({
                "id": m.id,
                "team_id": m.team_id,
                "user_id": m.user_id,
                "role": m.role,
                "email": m.user.email,
                "full_name": m.user.full_name
            })
        return out, len(all_members)
