"""
This module contains the main FastAPI application.
"""

import os
import warnings
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.endpoints import (
    user,
    message,
    trainer,
    memory,
    workout,
    stats,
    nutrition,
    weight,
    metabolism,
    hevy,
    onboarding,
    telegram,
    admin_users,
    admin_logs,
    admin_prompts,
    admin_tokens,
    admin_memory,
    admin_analytics,
    dashboard,
)
from src.core.config import settings
from src.core.deps import get_mongo_database
from src.core.logs import logger, set_log_level
from src.core.limiter import limiter, RATE_LIMITING_ENABLED

# Configure log level based on settings
set_log_level(settings.LOG_LEVEL)
logger.info(f"Log level set to: {settings.LOG_LEVEL}")

# Suppress known deprecation warnings from libraries
warnings.filterwarnings("ignore", message=".*migrating_memory.*")
warnings.filterwarnings("ignore", message=".*websockets.legacy.*")
warnings.filterwarnings("ignore", message=".*WebSocketServerProtocol.*")

app = FastAPI(
    title="AI Personal Trainer API",
    description=(
        "Backend API for the AI Personal Trainer application, "
        "featuring AI chat, workout tracking, nutrition logging, and more."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Rate limiting setup (only if slowapi is installed)
if RATE_LIMITING_ENABLED and limiter:
    from slowapi.errors import RateLimitExceeded

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, _exc: RateLimitExceeded):
        """Handler for rate limit exceeded errors."""
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )


# CORS middleware for frontend-backend integration
cors_origins = settings.ALLOWED_ORIGINS
allow_credentials_ = True

if "*" in cors_origins or cors_origins == ["*"]:
    logger.warning(
        "CORS: Allowing all origins ('*'). "
        "Credentials will be disabled as per CORS spec when using wildcard."
    )
    cors_origins = ["*"]
    allow_credentials_ = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials_,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(message.router, prefix="/message", tags=["message"])
app.include_router(trainer.router, prefix="/trainer", tags=["trainer"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(workout.router, prefix="/workout", tags=["workout"])
app.include_router(stats.router, prefix="/workout", tags=["workout"])
app.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
app.include_router(weight.router, prefix="/weight", tags=["weight"])
app.include_router(metabolism.router, prefix="/metabolism", tags=["metabolism"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(hevy.router, prefix="/integrations/hevy", tags=["integrations"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
app.include_router(telegram.router, prefix="/telegram", tags=["telegram"])

# Admin routers (require admin role)
app.include_router(admin_users.router, tags=["admin"])
app.include_router(admin_logs.router, tags=["admin"])
app.include_router(admin_prompts.router, tags=["admin"])
app.include_router(admin_tokens.router, tags=["admin"])
app.include_router(admin_memory.router, tags=["admin"])
app.include_router(admin_analytics.router, tags=["admin"])


@app.get("/health")
def health_check() -> JSONResponse:
    """
    Health check endpoint to verify service status.
    """
    health_status: dict[str, Any] = {"status": "healthy", "services": {}}

    # Check MongoDB
    try:
        db = get_mongo_database()
        db.client.admin.command("ping")
        health_status["services"]["mongodb"] = "healthy"
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("MongoDB health check failed: %s", e)
        health_status["status"] = "unhealthy"
        health_status["services"]["mongodb"] = f"unhealthy: {str(e)}"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


if __name__ == "__main__":
    # PORT is injected by Render in production (default 10000)
    port_env = int(os.environ.get("PORT", settings.API_SERVER_PORT))
    # RENDER env var is automatically defined on Render
    is_prod = os.environ.get("RENDER", "false").lower() == "true"

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port_env,
        reload=not is_prod,  # reload only locally
    )
