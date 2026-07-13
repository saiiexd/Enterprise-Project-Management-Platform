import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.auth.security import create_reset_token, create_verification_token


@pytest.mark.asyncio
async def test_complete_auth_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Register a new user & organization
    payload = {
        "email": "test@example.com",
        "password": "supersecurepassword123",
        "full_name": "Test User",
        "organization_name": "Acme Corp",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_verified"] is False  # Must verify email first

    # Verify user exists in database
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is False

    # 2. Verify Email via verification token
    v_token = create_verification_token("test@example.com")
    v_res = await client.post("/api/v1/auth/verify-email", json={"token": v_token})
    assert v_res.status_code == 200
    assert v_res.json()["message"] == "Email verified successfully."

    # Verify in DB
    await db_session.refresh(user)
    assert user.is_verified is True

    # 3. Login to get access & refresh tokens
    login_data = {"username": "test@example.com", "password": "supersecurepassword123"}
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]
    token_data["refresh_token"]

    # 4. Profile /me
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["is_verified"] is True

    # 5. Forgot Password & Reset Password Flow
    forgot_res = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
    )
    assert forgot_res.status_code == 200

    reset_token = create_reset_token("test@example.com")
    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "brandnewpassword999"},
    )
    assert reset_res.status_code == 200

    # Try login with old password (fails)
    bad_login_response = await client.post("/api/v1/auth/login", data=login_data)
    assert bad_login_response.status_code == 400

    # Login with new password (succeeds)
    good_login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "brandnewpassword999"},
    )
    assert good_login_response.status_code == 200

    # 6. OAuth Google Mock Callback Flow
    # Exchanging oauth code provisions or links account
    oauth_res = await client.post(
        "/api/v1/auth/google/callback", json={"code": "mock_code"}
    )
    assert oauth_res.status_code == 200
    oauth_token_data = oauth_res.json()
    assert "access_token" in oauth_token_data

    # Check that google user exists in DB
    result_google = await db_session.execute(
        select(User).where(User.email == "google-user@example.com")
    )
    google_user = result_google.scalar_one_or_none()
    assert google_user is not None
    assert google_user.provider == "google"
    assert google_user.is_verified is True
