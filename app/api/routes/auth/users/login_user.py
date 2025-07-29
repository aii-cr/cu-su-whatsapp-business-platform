"""User login endpoint."""

from fastapi import APIRouter, HTTPException, status
from bson import ObjectId

from app.services import auth_service
from app.config.error_codes import ErrorCode
from app.schemas.auth import UserLogin, TokenResponse, UserResponse
from app.core.logger import logger
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin):
    """
    Authenticate user and return access/refresh tokens.
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorCode.INVALID_CREDENTIALS
            )
        
        # Update last login
        await auth_service.update_last_login(user["_id"])
        
        # Create tokens
        tokens = await auth_service.create_tokens(user["_id"])
        
        logger.info(f"User {user['email']} logged in successfully")
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise handle_database_error(e, "login", "user") 