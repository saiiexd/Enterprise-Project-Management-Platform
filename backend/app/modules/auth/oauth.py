import logging

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("epmp.oauth")


class GoogleOAuth:
    @staticmethod
    def get_google_auth_url() -> str:
        # Construct the authentication URL to redirect user to Google
        client_id = settings.GOOGLE_CLIENT_ID or "placeholder_client_id"
        redirect_uri = "http://localhost:3000/api/auth/callback/google"
        scope = "openid email profile"
        state = "state"
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code&client_id={client_id}&"
            f"redirect_uri={redirect_uri}&scope={scope}&state={state}"
        )

    @staticmethod
    async def verify_google_code(code: str) -> dict:
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        redirect_uri = "http://localhost:3000/api/auth/callback/google"

        if (
            not client_id
            or not client_secret
            or client_id == "placeholder_client_id"
            or client_secret == "placeholder_client_secret"
        ):
            logger.warning(
                "Google OAuth credentials missing or placeholders, using mock user profile."
            )
            # Provisioning a mock user profile for local tests/development if oauth keys are missing
            return {
                "email": "google-user@example.com",
                "name": "Google User",
                "picture": "https://lh3.googleusercontent.com/a/default-user",
                "verified_email": True,
            }

        async with httpx.AsyncClient() as client:
            try:
                # Exchange Authorization Code for Token
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                token_res.raise_for_status()
                tokens = token_res.json()
                access_token = tokens.get("access_token")

                # Fetch User Information using access token
                user_res = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                user_res.raise_for_status()
                return user_res.json()
            except Exception as e:
                logger.error(f"Google OAuth verification error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to authenticate with Google OAuth.",
                )


google_oauth = GoogleOAuth()
