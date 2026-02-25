"""Admin backend service - separate from main backend for security"""
import os
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="Admin API", version="0.1.0")

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3001").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize admin_users collection on startup
@app.on_event("startup")
async def startup_event():
    """Initialize admin_users collection"""
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "aitrainer")

    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]

        # Create collection if missing
        if "admin_users" not in await db.list_collection_names():
            await db.create_collection("admin_users")

        # Ensure unique index
        await db.admin_users.create_index("email", unique=True)
        print("✅ Admin collection initialized")

        client.close()
    except Exception as e:
        print(f"⚠️  Admin collection init warning: {e}")

# Admin authentication middleware
@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    """Verify JWT token and X-Admin-Key header for admin endpoints"""

    # Public endpoints
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    # Check X-Admin-Key header
    admin_key = request.headers.get("X-Admin-Key")
    expected_key = os.getenv("ADMIN_SECRET_KEY", "")

    if not expected_key or admin_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials"
        )

    # TODO: Verify JWT token has is_admin: true
    # For now, assuming key provides sufficient protection

    return await call_next(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# TODO: Mount admin routes from backend/src/api/endpoints/admin.py
# This will be done in the next implementation step

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
