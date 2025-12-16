"""
This module contains the main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.api.endpoints import user, message, trainer
from src.core.config import settings

app = FastAPI()

# CORS middleware for frontend-backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust for your production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, tags=["user"])
app.include_router(message.router, tags=["message"])
app.include_router(trainer.router, tags=["trainer"])

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=settings.API_SERVER_PORT, reload=True)
