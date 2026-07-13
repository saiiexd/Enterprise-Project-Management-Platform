import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User, Role
from app.modules.auth.security import create_verification_token
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.teams.models import Team, TeamMember
from app.modules.invitations.models import Invitation


@pytest_asyncio.fixture
async def authenticated_users(client: AsyncClient):
    # Register & Verify User 1
    payload1 = {
        "email": "user1@example.com",
        "password": "supersecurepassword123",
        "full_name": "User One",
        "organization_name": "Org One",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload1)
    if res1.status_code == 201:
        token1 = create_verification_token("user1@example.com")
        await client.post("/api/v1/auth/verify-email", json={"token": token1})

    # Register & Verify User 2
    payload2 = {
        "email": "user2@example.com",
        "password": "supersecurepassword123",
        "full_name": "User Two",
        "organization_name": "Org Two",
    }
    res2 = await client.post("/api/v1/auth/register", json=payload2)
    if res2.status_code == 201:
        token2 = create_verification_token("user2@example.com")
        await client.post("/api/v1/auth/verify-email", json={"token": token2})

    # Login User 1
    login_res1 = await client.post(
        "/api/v1/auth/login",
        data={"username": "user1@example.com", "password": "supersecurepassword123"}
    )
    assert login_res1.status_code == 200
    access_token1 = login_res1.json()["access_token"]

    # Login User 2
    login_res2 = await client.post(
        "/api/v1/auth/login",
        data={"username": "user2@example.com", "password": "supersecurepassword123"}
    )
    assert login_res2.status_code == 200
    access_token2 = login_res2.json()["access_token"]

    return {
        "user1_token": access_token1,
        "user2_token": access_token2,
        "user1_email": "user1@example.com",
        "user2_email": "user2@example.com"
    }


@pytest.mark.asyncio
async def test_organization_crud_and_switching(
    client: AsyncClient, authenticated_users
) -> None:
    headers1 = {"Authorization": f"Bearer {authenticated_users['user1_token']}"}
    headers2 = {"Authorization": f"Bearer {authenticated_users['user2_token']}"}

    # 1. Get user1's profile to retrieve default organization ID
    me_res = await client.get("/api/v1/auth/me", headers=headers1)
    assert me_res.status_code == 200
    me_data = me_res.json()
    org1_id = me_data["organizations"][0]["organization"]["id"]

    # 2. Get active organization details (defaults to first org if no header)
    active_res = await client.get("/api/v1/organizations/active", headers=headers1)
    assert active_res.status_code == 200
    assert active_res.json()["id"] == org1_id

    # 3. Create a second organization for user1
    new_org_payload = {
        "name": "Acme Ventures",
        "slug": "acme-ventures",
        "description": "Acme Venture Capital arm",
        "logo_url": "https://example.com/logo.png"
    }
    create_res = await client.post("/api/v1/organizations/", json=new_org_payload, headers=headers1)
    assert create_res.status_code == 201
    org2_data = create_res.json()
    org2_id = org2_data["id"]

    # 4. Verify user1 has two organizations now
    list_res = await client.get("/api/v1/organizations/", headers=headers1)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2

    # 5. Switch active context using X-Organization-ID header
    headers1_switched = {
        "Authorization": f"Bearer {authenticated_users['user1_token']}",
        "X-Organization-ID": org2_id
    }
    active_switched_res = await client.get("/api/v1/organizations/active", headers=headers1_switched)
    assert active_switched_res.status_code == 200
    assert active_switched_res.json()["id"] == org2_id

    # 6. Verify multi-tenant isolation: User 2 tries to access Org 2 (Forbidden)
    headers2_malicious = {
        "Authorization": f"Bearer {authenticated_users['user2_token']}",
        "X-Organization-ID": org2_id
    }
    malicious_res = await client.get("/api/v1/organizations/active", headers=headers2_malicious)
    assert malicious_res.status_code == 403

    # 7. Update organization details
    update_payload = {"name": "Acme Ventures Updated", "description": "New Description"}
    update_res = await client.put(
        f"/api/v1/organizations/{org2_id}", json=update_payload, headers=headers1_switched
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Acme Ventures Updated"

    # 8. Update organization settings
    settings_payload = {"timezone": "Europe/London", "locale": "en_GB"}
    settings_res = await client.put(
        f"/api/v1/organizations/{org2_id}/settings", json=settings_payload, headers=headers1_switched
    )
    assert settings_res.status_code == 200
    assert settings_res.json()["settings"]["timezone"] == "Europe/London"


@pytest.mark.asyncio
async def test_invitations_flow(
    client: AsyncClient, authenticated_users
) -> None:
    headers1 = {"Authorization": f"Bearer {authenticated_users['user1_token']}"}
    headers2 = {"Authorization": f"Bearer {authenticated_users['user2_token']}"}

    # Get user1's org ID
    me_res = await client.get("/api/v1/auth/me", headers=headers1)
    org_id = me_res.json()["organizations"][0]["organization"]["id"]

    headers1_org = {
        "Authorization": f"Bearer {authenticated_users['user1_token']}",
        "X-Organization-ID": org_id
    }

    # 1. Invite User 2 to Org 1
    invite_payload = {
        "email": "user2@example.com",
        "role_name": "Developer"
    }
    invite_res = await client.post("/api/v1/invitations/", json=invite_payload, headers=headers1_org)
    assert invite_res.status_code == 201
    inv_data = invite_res.json()
    token = inv_data["token"]
    assert inv_data["status"] == "pending"

    # 2. Try to double-invite User 2 (Should fail)
    double_res = await client.post("/api/v1/invitations/", json=invite_payload, headers=headers1_org)
    assert double_res.status_code == 400

    # 3. List invitations
    list_res = await client.get("/api/v1/invitations/", headers=headers1_org)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 4. Accept invitation (User 2 accepts using the token)
    accept_payload = {"token": token}
    accept_res = await client.post("/api/v1/invitations/accept", json=accept_payload, headers=headers2)
    assert accept_res.status_code == 200

    # 5. Verify User 2 is now a member of Org 1
    members_res = await client.get(f"/api/v1/organizations/{org_id}/members", headers=headers1_org)
    assert members_res.status_code == 200
    member_emails = [m["email"] for m in members_res.json()["members"]]
    assert "user2@example.com" in member_emails


@pytest.mark.asyncio
async def test_team_management(
    client: AsyncClient, authenticated_users
) -> None:
    headers1 = {"Authorization": f"Bearer {authenticated_users['user1_token']}"}

    # Get user1's org ID
    me_res = await client.get("/api/v1/auth/me", headers=headers1)
    org_id = me_res.json()["organizations"][0]["organization"]["id"]

    headers1_org = {
        "Authorization": f"Bearer {authenticated_users['user1_token']}",
        "X-Organization-ID": org_id
    }

    # 1. Create a Team
    team_payload = {
        "name": "Engineering Alpha",
        "description": "Primary engineering pod",
        "organization_id": org_id
    }
    create_res = await client.post("/api/v1/teams/", json=team_payload, headers=headers1_org)
    assert create_res.status_code == 201
    team_data = create_res.json()
    team_id = team_data["id"]

    # 2. List teams
    list_res = await client.get("/api/v1/teams/", headers=headers1_org)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 3. Add User 2 to Team (Need to fetch User 2 user_id first)
    from tests.conftest import TestingSessionLocal
    async with TestingSessionLocal() as session:
        stmt = select(User).where(User.email == "user2@example.com")
        res_user2 = await session.execute(stmt)
        user2 = res_user2.scalar_one_or_none()
        assert user2 is not None
        user2_id = user2.id

    add_payload = {"user_id": str(user2_id), "role": "developer"}
    add_res = await client.post(f"/api/v1/teams/{team_id}/members", json=add_payload, headers=headers1_org)
    assert add_res.status_code == 201

    # 4. List Team members
    members_res = await client.get(f"/api/v1/teams/{team_id}/members", headers=headers1_org)
    assert members_res.status_code == 200
    assert members_res.json()["total"] == 2 # Creator (lead) + User 2 (developer)
