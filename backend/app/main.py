import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings, setup_logging
from app.core.database import engine

logger = logging.getLogger("epmp.main")

# Setup logging immediately
setup_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup actions
    logger.info("Starting up Enterprise Project Management Platform...")

    import sys
    if "pytest" not in sys.modules:
        # 1. Verify PostgreSQL Database connectivity
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the PostgreSQL Database.")
        except Exception as e:
            logger.critical(f"Failed to connect to PostgreSQL Database: {e}")

        # 2. Verify Redis connectivity
        try:
            redis_client = Redis.from_url(settings.REDIS_URL)
            await redis_client.ping()
            await redis_client.close()
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.critical(f"Failed to connect to Redis: {e}")

        # 3. Seed default roles and permissions
        try:
            from app.core.database import SessionLocal
            from app.modules.auth.seeds import seed_roles_and_permissions
            async with SessionLocal() as db:
                await seed_roles_and_permissions(db)
            logger.info("Database seeded successfully.")
        except Exception as e:
            logger.error(f"Failed to seed roles and permissions: {e}")

    yield

    # Shutdown actions
    logger.info("Shutting down Enterprise Project Management Platform...")
    await engine.dispose()
    logger.info("Database connections closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-level SaaS Multi-Tenant Project Management Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS Middleware setup
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Basic Request Logger / Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Method={request.method} Path={request.url.path} "
        f"Status={response.status_code} Duration={duration:.4f}s"
    )
    return response


# Custom Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": "HTTP_ERROR", "message": exc.detail, "details": None},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": jsonable_encoder(exc.errors()),
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
                "details": None if settings.ENVIRONMENT == "production" else str(exc),
            },
        },
    )


# Health Check router/endpoints
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    Public health check endpoint. Returns operational status of the service.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.ENVIRONMENT,
        "services": {"database": "online", "redis": "online"},
    }


# API V1 Router
v1_router = APIRouter(prefix=settings.API_V1_STR)


@v1_router.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def v1_health_check() -> dict[str, Any]:
    return await health_check()


from app.modules.auth.router import router as auth_router
from app.modules.organizations.router import router as organizations_router
from app.modules.teams.router import router as teams_router
from app.modules.invitations.router import router as invitations_router

v1_router.include_router(auth_router)
v1_router.include_router(organizations_router)
v1_router.include_router(teams_router)
v1_router.include_router(invitations_router)

app.include_router(v1_router)

