"""Get multiple users by IDs endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from pydantic import BaseModel

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.user import UserResponse
from app.services.auth import require_permissions
from app.services import user_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

class BulkUsersRequest(BaseModel):
    user_ids: List[str]

@router.post("/bulk", response_model=List[UserResponse])
async def get_users_bulk(
    request: BulkUsersRequest,
    current_user: User = Depends(require_permissions(["users:read"]))
):
    """
    Get multiple users by their IDs.
    
    Requires 'users:read' permission.
    
    Args:
        request: Object containing list of user IDs
        current_user: Current authenticated user
        
    Returns:
        List of user information
    """
    try:
        # Validate user IDs format
        user_obj_ids = []
        invalid_ids = []
        
        for user_id in request.user_ids:
            try:
                user_obj_ids.append(ObjectId(user_id))
            except Exception:
                invalid_ids.append(user_id)
        
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user ID format(s): {', '.join(invalid_ids)}"
            )
        
        # Get users using service
        users = await user_service.get_users_by_ids(user_obj_ids)
        
        logger.info(f"✅ [GET_USERS_BULK] Retrieved {len(users)} users by {current_user.email}")
        
        # Convert to UserResponse objects
        user_responses = [UserResponse(**user) for user in users]
        
        return user_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET_USERS_BULK] Error retrieving users: {str(e)}")
        raise handle_database_error(e, "get_users_bulk", "user") 