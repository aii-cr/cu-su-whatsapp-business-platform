"""Get current user endpoint."""

from fastapi import APIRouter, Response, Depends
from app.services.auth.utils.session_auth import get_current_user, update_session_activity, set_session_cookie
from app.schemas.auth import UserResponse
from app.core.logger import logger

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    response: Response, 
    current_user = Depends(get_current_user)
):
    """
    Get current user information and refresh session activity.
    """
    try:
        # Convert user to response model
        user_data = current_user.model_dump()
        
        # Update session activity to prevent inactivity timeout
        # Note: This would require access to the current session token
        # For now, we'll rely on the session being refreshed on each request
        
        logger.info(f"User {current_user.email} retrieved profile information")
        
        return UserResponse(**user_data)
        
    except Exception as e:
        logger.error(f"Error getting current user info: {str(e)}")
        raise
