"""Admin backend service - separate from main backend for security"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Project imports
from src.core.deps import get_admin_db
from src.api.endpoints import admin_analytics, admin_users, admin_prompts, admin_tokens

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Admin API", version="0.1.0")

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")
if not ADMIN_SECRET_KEY:
    raise ValueError("ADMIN_SECRET_KEY environment variable is not set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours for admin

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3001,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    token: str

class UserResponse(BaseModel):
    email: str
    role: str
    name: Optional[str] = None

# Helpers
def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Initialize admin_users collection on startup
@app.on_event("startup")
def startup_event():
    """Initialize admin_users collection and create default admin"""
    try:
        db = get_admin_db()
        # Ensure unique index
        db.admin_users.create_index("email", unique=True)
        print("✅ Admin collection initialized")

        # Create default admin if none exists
        if db.admin_users.count_documents({}) == 0:
            default_email = os.getenv("INITIAL_ADMIN_EMAIL", "rafacolucci@gmail.com")
            default_password = os.getenv("INITIAL_ADMIN_PASSWORD")

            if not default_password:
                print("⚠️  INITIAL_ADMIN_PASSWORD not set. Skipping default admin creation.")
                return

            hashed_pw = get_password_hash(default_password)
            db.admin_users.insert_one({
                "email": default_email,
                "password_hash": hashed_pw,
                "role": "admin",
                "name": os.getenv("INITIAL_ADMIN_NAME", "System Admin"),
                "created_at": datetime.now(timezone.utc)
            })
            print(f"👤 Created default admin: {default_email}")

    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"⚠️  Admin collection init warning: {e}")

# Admin authentication middleware
@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next): # pylint: disable=too-many-return-statements
    """Verify JWT token and X-Admin-Key header for admin endpoints"""

    # Skip auth for OPTIONS (CORS preflight) and public endpoints
    if request.method == "OPTIONS" or request.url.path in ["/health", "/docs", "/openapi.json", "/user/login"]:
        return await call_next(request)

    # Check X-Admin-Key header (Shield protection)
    admin_key = request.headers.get("X-Admin-Key")
    if not ADMIN_SECRET_KEY or admin_key != ADMIN_SECRET_KEY:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Invalid admin shield key"}
        )

    # Verify JWT Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid token"}
        )

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return JSONResponse(status_code=401, content={"detail": "Invalid token payload"})

        # Check if email exists in admin_users
        db = get_admin_db()
        admin_user = db.admin_users.find_one({"email": email})
        if not admin_user:
            return JSONResponse(status_code=403, content={"detail": "Admin access required"})

        request.state.user = admin_user
    except jwt.PyJWTError:
        return JSONResponse(status_code=401, content={"detail": "Could not validate credentials"})

    return await call_next(request)

# Include Routers
app.include_router(admin_analytics.router)
app.include_router(admin_users.router)
app.include_router(admin_prompts.router)
app.include_router(admin_tokens.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "db": "connected"}

@app.post("/user/login", response_model=Token)
async def login(data: LoginRequest):
    """Admin login endpoint"""
    db = get_admin_db()
    user = db.admin_users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Credenciais inválidas"}
        )

    access_token = create_access_token(data={"sub": user["email"]})
    return {"token": access_token}

@app.get("/user/me", response_model=UserResponse)
async def get_me(request: Request):
    """Returns basic information about the currently authenticated admin user."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "email": user["email"],
        "role": user.get("role", "admin"),
        "name": user.get("name", user["email"].split("@")[0]),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
