import logging
import sys
from typing import Annotated, Any

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Helper to parse list of CORS origins
def parse_cors_origins(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list):
        return [str(i) for i in v]
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    PROJECT_NAME: str = "Enterprise Project Management Platform"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkeychangethisinproduction1234567890!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors_origins)] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/epmp"

    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379/0"

    # Mail Configuration
    MAIL_HOST: str = "mailhog"
    MAIL_PORT: int = 1025
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@epmp.local"

    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None


settings = Settings()


# Configure Logging
def setup_logging() -> None:
    logging_level = logging.INFO
    if settings.ENVIRONMENT == "development":
        logging_level = logging.DEBUG

    logging.basicConfig(
        level=logging_level,
        format=(
            "%(asctime)s [%(levelname)s] %(name)s "
            "(%(filename)s:%(lineno)d) - %(message)s"
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
    )
