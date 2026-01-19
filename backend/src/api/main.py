"""
This module contains the main FastAPI application.
"""
import warnings
# Suppress known deprecation warnings from libraries (LangChain, websockets, uvicorn)
warnings.filterwarnings("ignore", message=".*migrating_memory.*")
warnings.filterwarnings("ignore", message=".*websockets.legacy.*")
warnings.filterwarnings("ignore", message=".*WebSocketServerProtocol.*")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
import uvicorn  # noqa: E402
import os  # noqa: E402


from src.api.endpoints import user, message, trainer, memory, workout, stats, nutrition, weight, metabolism, hevy, onboarding  # noqa: E402
from src.core.config import settings  # noqa: E402
from src.core.deps import get_mongo_database, get_mem0_client  # noqa: E402
from src.core.logs import logger  # noqa: E402
from src.core.limiter import limiter, RATE_LIMITING_ENABLED  # noqa: E402

app = FastAPI(
    title="AI Personal Trainer API",
    description="Backend API for the AI Personal Trainer application, featuring AI chat, workout tracking, nutrition logging, and more.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Rate limiting setup (only if slowapi is installed)
if RATE_LIMITING_ENABLED and limiter:
    from slowapi.errors import RateLimitExceeded
    app.state.limiter = limiter
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

# CORS middleware for frontend-backend integration
logger.info(f"Allowed Origins: {settings.ALLOWED_ORIGINS}")
logger.info(f"Mongo URI: {settings.MONGO_URI.split('@')[-1]}") # Mask password
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
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
app.include_router(hevy.router, prefix="/integrations/hevy", tags=["integrations"])
app.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])





@app.get("/health")
def health_check() -> JSONResponse:
    """
    Health check endpoint to verify service status.
    
    Checks:
    - MongoDB connection
    - Mem0 client availability
    
    Returns:
        JSONResponse: Status of the application and its dependencies.
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check MongoDB
    try:
        db = get_mongo_database()
        db.client.admin.command('ping')
        health_status["services"]["mongodb"] = "healthy"
    except Exception as e:
        logger.error("MongoDB health check failed: %s", e)
        health_status["status"] = "unhealthy"
        health_status["services"]["mongodb"] = f"unhealthy: {str(e)}"
    
    # Check Mem0
    try:
        mem0 = get_mem0_client()
        # Mem0 doesn't have a direct ping, so we check if it's instantiated
        if mem0 is not None:
            health_status["services"]["mem0"] = "healthy"
        else:
            health_status["services"]["mem0"] = "unhealthy: client is None"
            health_status["status"] = "unhealthy"
    except Exception as e:
        logger.error("Mem0 health check failed: %s", e)
        health_status["status"] = "unhealthy"
        health_status["services"]["mem0"] = f"unhealthy: {str(e)}"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


if __name__ == "__main__":
    # PORT is injected by Render in production (default 10000)
    port = int(os.environ.get("PORT", settings.API_SERVER_PORT))
    # RENDER env var is automatically defined on Render
    is_production = os.environ.get("RENDER", "false").lower() == "true"
    
    uvicorn.run(
        "src.api.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=not is_production  # reload only locally
    )


