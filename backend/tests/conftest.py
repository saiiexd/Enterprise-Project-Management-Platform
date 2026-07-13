import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app as fastapi_app

# Ensure all models are registered on Base.metadata
import app.modules.auth.models  # noqa: F401
import app.modules.organizations.models  # noqa: F401
import app.modules.teams.models  # noqa: F401
import app.modules.invitations.models  # noqa: F401
import app.modules.audit_logs.models  # noqa: F401


# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_smtp(monkeypatch):
    import smtplib
    class MockSMTP:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args, **kwargs):
            pass
        def login(self, *args, **kwargs):
            pass
        def sendmail(self, *args, **kwargs):
            pass
    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    from app.services.redis_service import redis_service
    async def mock_blacklist(*args, **kwargs): return None
    async def mock_is_blacklisted(*args, **kwargs): return False
    async def mock_incr(*args, **kwargs): return 0
    async def mock_reset(*args, **kwargs): return None
    async def mock_rate_limit(*args, **kwargs): return True

    monkeypatch.setattr(redis_service, "blacklist_token", mock_blacklist)
    monkeypatch.setattr(redis_service, "is_token_blacklisted", mock_is_blacklisted)
    monkeypatch.setattr(redis_service, "increment_login_attempts", mock_incr)
    monkeypatch.setattr(redis_service, "reset_login_attempts", mock_reset)
    monkeypatch.setattr(redis_service, "rate_limit_check", mock_rate_limit)




@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed default roles and permissions for tests
    from app.modules.auth.seeds import seed_roles_and_permissions
    async with TestingSessionLocal() as db:
        await seed_roles_and_permissions(db)
        
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async client fixture for hitting FastAPI endpoints.
    """
    # Note: We need explicit ASGI Transport to prevent deprecation warnings in newer HTTPX
    # or keep it simple. Let's run it directly.
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac
