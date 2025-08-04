"""Delete role endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.services.auth import require_permissions, role_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: User = Depends(require_permissions(["roles:delete"]))
):
    """
    Delete a role.
    
    Requires 'roles:delete' permission.
    Cannot delete system roles or roles assigned to users.
    
    Path parameter:
    - role_id: Role ID to delete
    
    Returns success message.
    """
    try:
        try:
            role_obj_id = ObjectId(role_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role ID format"
            )
        
        # Get existing role for audit logging
        existing_role = await role_service.get_role_by_id(role_obj_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.ROLE_NOT_FOUND
            )
        
        # Delete role using service
        success = await role_service.delete_role(
            role_id=role_obj_id,
            deleted_by=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.ROLE_NOT_FOUND
            )
        
        logger.info(f"✅ [DELETE_ROLE] Role '{existing_role['name']}' deleted successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_role_deleted(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            role_id=role_id,
            role_name=existing_role.get("name", "Unknown"),
            correlation_id=correlation_id
        )
        
        return {"message": f"Role '{existing_role['name']}' deleted successfully"}
        
    except ValueError as e:
        logger.warning(f"⚠️ [DELETE_ROLE] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE_ROLE] Error deleting role: {str(e)}")
        raise handle_database_error(e, "delete_role", "role") 