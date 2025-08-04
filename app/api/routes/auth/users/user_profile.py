"""User profile management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth import get_current_active_user
from app.services import auth_service
from app.config.error_codes import ErrorCode
from app.schemas.auth import UserProfileResponse
from app.core.logger import logger
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user = Depends(get_current_active_user)):
    """
    Get current user's profile with permissions and roles.
    """
    try:
        # Get user profile with roles and permissions
        user_profile = await auth_service.get_user_profile(current_user.id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.USER_NOT_FOUND
            )
        
        logger.info(f"Retrieved profile for user {current_user.email}")
        
        return UserProfileResponse(**user_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        raise handle_database_error(e, "get_profile", "user") 