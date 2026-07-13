import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.dependencies import (
    get_current_active_user,
    get_current_organization,
    requires_permission,
)
from app.modules.auth.models import User
from app.modules.organizations.models import Organization
from app.modules.teams.schemas import (
    TeamCreate,
    TeamOut,
    TeamUpdate,
    TeamMemberAdd,
    TeamMemberOut,
    TeamPagination,
    TeamMemberPagination,
)
from app.modules.teams.services import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:create")),
) -> Any:
    # Ensure team belongs to the active organization
    # Let's verify data.organization_id matches the active org context
    if data.organization_id != org.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create team for a different organization than active context."
        )
    return await TeamService.create_team(db, data, current_user.id)


@router.get("/", response_model=TeamPagination)
async def list_teams(
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:view")),
) -> Any:
    teams, total = await TeamService.list_teams(db, org.id, search, skip, limit)
    return {"teams": teams, "total": total}


@router.get("/{team_id}", response_model=TeamOut)
async def get_team(
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:view")),
) -> Any:
    team = await TeamService.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/{team_id}", response_model=TeamOut)
async def update_team(
    team_id: uuid.UUID,
    data: TeamUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:update")),
) -> Any:
    return await TeamService.update_team(db, team_id, data, current_user.id)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:delete")),
) -> None:
    await TeamService.delete_team(db, team_id, current_user.id)


@router.get("/{team_id}/members", response_model=TeamMemberPagination)
async def list_team_members(
    team_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:view")),
) -> Any:
    members, total = await TeamService.list_members(db, team_id, skip, limit)
    return {"members": members, "total": total}


@router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: uuid.UUID,
    data: TeamMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:update")),
) -> Any:
    return await TeamService.add_member(
        db, team_id, data.user_id, data.role or "member", current_user.id
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _perm: None = Depends(requires_permission("team:update")),
) -> None:
    await TeamService.remove_member(db, team_id, user_id, current_user.id)
