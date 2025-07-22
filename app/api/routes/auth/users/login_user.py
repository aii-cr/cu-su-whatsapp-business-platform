"""User login endpoint."""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone

from app.services.auth import create_access_token, create_refresh_token, verify_password
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.schemas.auth import UserLogin, TokenResponse, UserResponse
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin):
    """
    Authenticate user and return access/refresh tokens.
    """
    db = database.db
    
    # Find user by email
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_CREDENTIALS
        )
    
    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.AUTH_USER_INACTIVE
        )
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user["_id"])})
    refresh_token = create_refresh_token(data={"sub": str(user["_id"])})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user)
    ) 