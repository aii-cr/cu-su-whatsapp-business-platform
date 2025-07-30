"""Get permission endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.permission import PermissionResponse
from app.services.auth import require_permissions, permission_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    current_user: User = Depends(require_permissions(["permissions:read"]))
):
    """
    Get a specific permission by ID.
    
    Requires 'permissions:read' permission.
    
    Path parameter:
    - permission_id: Permission ID
    
    Returns the permission details.
    """
    try:
        # Validate permission ID format
        try:
            permission_obj_id = ObjectId(permission_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid permission ID format"
            )
        
        # Get permission using service
        permission = await permission_service.get_permission_by_id(permission_obj_id)
        
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PERMISSION_NOT_FOUND
            )
        
        logger.info(f"✅ [GET_PERMISSION] Retrieved permission '{permission['key']}' by {current_user.email}")
        
        return PermissionResponse(**permission)
        
    except Exception as e:
        logger.error(f"❌ [GET_PERMISSION] Error getting permission: {str(e)}")
        raise handle_database_error(e, "get_permission", "permission") 