"""Get role endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.role import RoleResponse
from app.services.auth import require_permissions, role_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: User = Depends(require_permissions(["roles:read"]))
):
    """
    Get a specific role by ID.
    
    Requires 'roles:read' permission.
    
    Path parameter:
    - role_id: Role ID
    
    Returns the role details.
    """
    try:
        try:
            role_obj_id = ObjectId(role_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role ID format"
            )
        
        role = await role_service.get_role_by_id(role_obj_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.ROLE_NOT_FOUND
            )
        
        logger.info(f"✅ [GET_ROLE] Retrieved role '{role['name']}' by {current_user.email}")
        
        return RoleResponse(**role)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET_ROLE] Error getting role: {str(e)}")
        raise handle_database_error(e, "get_role", "role") 