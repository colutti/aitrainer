"""
Admin authentication and authorization utilities.
Extends the existing auth system with admin role checking.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase


def verify_admin(
    email: str = Depends(verify_token),
    db: MongoDatabase = Depends(get_mongo_database)
) -> str:
    """
    Verifica se o usuário autenticado é admin.

    Args:
        email: User email from verify_token dependency
        db: MongoDB database instance

    Returns:
        str: Admin user email

    Raises:
        HTTPException: 403 if user is not admin
        HTTPException: 404 if user not found
    """
    # Busca o usuário no banco
    user = db.users.get_profile(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verifica se é admin
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return email


# Type alias para uso em endpoints
AdminUser = Annotated[str, Depends(verify_admin)]
