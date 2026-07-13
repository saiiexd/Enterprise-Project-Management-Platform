import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


@pytest.mark.asyncio
async def test_register_and_login(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Register a new user & organization
    from app.modules.auth.schemas import UserRegister

    print("USER REGISTER FIELDS:", UserRegister.model_fields)
    payload = {
        "email": "test@example.com",
        "password": "supersecurepassword123",
        "full_name": "Test User",
        "organization_name": "Acme Corp",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    if response.status_code != 201:
        print("ERROR RESPONSE:", response.json())
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert len(data["organizations"]) == 1
    assert data["organizations"][0]["organization"]["name"] == "Acme Corp"
    assert data["organizations"][0]["role"] == "owner"
    org_id = data["organizations"][0]["organization"]["id"]

    # Verify user exists in database
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == "Test User"

    # 2. Login to get access & refresh tokens
    login_data = {"username": "test@example.com", "password": "supersecurepassword123"}
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 3. Test get profile (/me)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "test@example.com"

    # 4. Test Token Refreshing
    refresh_payload = {"refresh_token": refresh_token}
    refresh_response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert refresh_response.status_code == 200
    new_token_data = refresh_response.json()
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data

    # 5. Test Organization Context Header isolation
    # Set valid X-Organization-ID header
    org_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-ID": org_id,
    }
    # Since we don't have modules implementing business logic yet, we can mock/check organization
    # resolution in a test endpoint or dependencies directly. Let's make sure invalid org returns 403.
    import uuid

    invalid_org_id = str(uuid.uuid4())
    bad_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-ID": invalid_org_id,
    }
    # Let's create a temp router inside test_auth to verify get_current_organization dependency
    from fastapi import Depends

    from app.main import app
    from app.modules.auth.dependencies import get_current_organization
    from app.modules.organizations.models import Organization

    @app.get("/api/v1/test-org-isolation")
    async def test_org_endpoint(org: Organization = Depends(get_current_organization)):
        return {"organization_id": str(org.id), "slug": org.slug}

    # Valid org query
    org_check_res = await client.get("/api/v1/test-org-isolation", headers=org_headers)
    assert org_check_res.status_code == 200
    assert org_check_res.json()["organization_id"] == org_id

    # Invalid org query (Tenant Isolation)
    bad_org_check_res = await client.get(
        "/api/v1/test-org-isolation", headers=bad_headers
    )
    assert bad_org_check_res.status_code == 403
