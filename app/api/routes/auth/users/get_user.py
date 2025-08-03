"""Get user by ID endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.user import UserResponse
from app.services.auth import require_permissions
from app.services import user_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permissions(["users:read"]))
):
    """
    Get a specific user by ID.
    
    Requires 'users:read' permission.
    
    Args:
        user_id: The ID of the user to retrieve
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    try:
        # Validate user ID format
        try:
            user_obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Get user using service
        user = await user_service.get_user_by_id(user_obj_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.USER_NOT_FOUND
            )
        
        logger.info(f"✅ [GET_USER] Retrieved user {user_id} by {current_user.email}")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET_USER] Error retrieving user {user_id}: {str(e)}")
        raise handle_database_error(e, "get_user", "user")