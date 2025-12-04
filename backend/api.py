from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import API_SERVER_PORT

from .auth import user_login, user_logout, verify_token
from .database import get_trainer_profile as db_get_trainer_profile
from .database import get_user_profile as db_get_user_profile
from .database import save_trainer_profile as db_save_trainer_profile
from .database import save_user_profile as db_save_user_profile
from .logs import logger
from .models import LoginRequest, MessageRequest, TrainerProfile, UserProfile
from .services import AITrainerBrain

CurrentUser = Annotated[str, Depends(verify_token)]

app = FastAPI()

# CORS middleware for frontend-backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajuste para seu domínio em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login")
def login(data: LoginRequest) -> dict:
    """
    Authenticates a user with the provided email and password.

    Args:
        data (LoginRequest): The login request body containing email and password.

    Returns:
        tuple[dict, int]: A tuple containing a response dictionary and an HTTP status code.
            - If authentication fails, returns ({"message": "Invalid credentials"}, 401).
            - If authentication succeeds, returns ({"token": <JWT token>}, 200).

    Logs:
        - Logs failed login attempts and successful logins.
    """
    try:
        token = user_login(data.email, data.password)
        logger.info("User logged in successfully: %s", data.email)
        return {"token": token}
    except ValueError as exc:
        logger.info("Failed login attempt for email: %s", data.email)
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc


@app.post("/message")
def message_ai(message: MessageRequest, user_email: CurrentUser) -> JSONResponse:
    """
    Handles an AI messaging request for an authenticated user.

    Args:
        message (MessageRequest): The user's message input.
        user (dict, optional): The authenticated user's information, injected via dependency.

    Returns:
        JSONResponse: A JSON response containing the AI-generated reply.

    Raises:
        HTTPException: If the user profile is not found (404).
    """
    brain = AITrainerBrain()
    user_profile = db_get_user_profile(user_email)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    response_generator = brain.send_message_ai(
        profile=user_profile, user_input=message.user_message, session_id=user_email
    )
    return JSONResponse(content={"response": "".join(response_generator)})


@app.get("/profile")
def get_profile(user_email: CurrentUser) -> UserProfile:
    """
    Retrieve the profile information for the authenticated user.

    Args:
        user (dict, optional): The authenticated user information,
        injected by dependency (verify_token).

    Returns:
        UserProfile: The user's profile data.

    Raises:
        HTTPException: If the user profile is not found (404).
    """
    user_profile = db_get_user_profile(user_email)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile


@app.post("/update_profile")
def update_profile(profile: UserProfile, user_email: CurrentUser) -> JSONResponse:
    """
    Updates the user profile with the provided information,
    ensuring the update is associated with the authenticated user.

    Args:
        profile (UserProfile): The user profile data to update.
        user (dict, optional): The authenticated user information,
        injected by dependency (verify_token).

    Returns:
        JSONResponse: A response indicating the profile was updated successfully.
    """
    # Ensure the profile update is associated with the authenticated user
    profile.email = user_email
    db_save_user_profile(profile)
    return JSONResponse(content={"message": "Profile updated successfully"})


@app.post("/update_trainer_profile")
def update_trainer_profile(
    profile: TrainerProfile, user_email: CurrentUser
) -> JSONResponse:
    """
    Updates the trainer profile with the provided information,
    ensuring the update is associated with the authenticated user.

    Args:
       profile (TrainerProfile): The trainer profile data to update.
       user_email (CurrentUser): The authenticated user information,
       injected by dependency (verify_token).

    Returns:
     JSONResponse: A response indicating the profile was updated successfully.
    """
    # Ensure the profile update is associated with the authenticated user
    profile.user_email = user_email
    db_save_trainer_profile(profile)
    return JSONResponse(content={"message": "Profile updated successfully"})


@app.get("/trainer_profile")
def get_trainer_profile(user_email: CurrentUser) -> TrainerProfile:
    """
    Retrieves the trainer profile associated with the authenticated user.

    Args:
     user_email (CurrentUser): The authenticated user information,
     injected by dependency (verify_token).

    Returns:
    TrainerProfile: The trainer profile associated with the authenticated user.
    """
    trainer_profile = db_get_trainer_profile(user_email)
    if not trainer_profile:
        raise HTTPException(status_code=404, detail="Trainer profile not found")
    return trainer_profile


@app.get("/logout")
def logout() -> JSONResponse:
    """
    Logs out the current user by calling the user_logout function
    and returns a JSON response indicating success.

    Returns:
        JSONResponse: A response object with a message confirming successful logout.
    """
    user_logout()
    return JSONResponse(content={"message": "Logged out successfully"})


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=API_SERVER_PORT, reload=True)
