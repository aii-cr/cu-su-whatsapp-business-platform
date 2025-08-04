"""User login endpoint."""

from fastapi import APIRouter, HTTPException, status, Response
from bson import ObjectId

from app.services import auth_service
from app.services.auth.utils.session_auth import set_session_cookie
from app.config.error_codes import ErrorCode
from app.schemas.auth import UserLogin, UserResponse
from app.core.logger import logger
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.post("/login", response_model=UserResponse)
async def login_user(user_credentials: UserLogin, response: Response):
    """
    Authenticate user and set session cookie.
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
        
        # Create session token
        session_token = await auth_service.create_session_token(
            user["_id"], 
            user["email"]
        )
        
        # Set session cookie
        set_session_cookie(response, session_token)
        
        logger.info(f"User {user['email']} logged in successfully")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise handle_database_error(e, "login", "user") 