"""Delete permission endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.services.auth import require_permissions, permission_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: str,
    current_user: User = Depends(require_permissions(["permissions:delete"]))
):
    """
    Delete a permission.
    
    Requires 'permissions:delete' permission.
    Cannot delete system permissions or permissions assigned to roles.
    
    Path parameter:
    - permission_id: Permission ID to delete
    
    Returns success message.
    """
    try:
        try:
            permission_obj_id = ObjectId(permission_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid permission ID format"
            )
        
        # Get existing permission for audit logging
        existing_permission = await permission_service.get_permission_by_id(permission_obj_id)
        if not existing_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PERMISSION_NOT_FOUND
            )
        
        # Delete permission using service
        success = await permission_service.delete_permission(
            permission_id=permission_obj_id,
            deleted_by=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PERMISSION_NOT_FOUND
            )
        
        logger.info(f"✅ [DELETE_PERMISSION] Permission '{existing_permission['name']}' deleted successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_permission_deleted(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            permission_id=permission_id,
            permission_key=existing_permission.get("key", existing_permission.get("name", "Unknown")),
            correlation_id=correlation_id
        )
        
        return {"message": f"Permission '{existing_permission['name']}' deleted successfully"}
        
    except ValueError as e:
        logger.warning(f"⚠️ [DELETE_PERMISSION] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE_PERMISSION] Error deleting permission: {str(e)}")
        raise handle_database_error(e, "delete_permission", "permission") 