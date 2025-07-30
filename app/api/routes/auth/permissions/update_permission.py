"""Update permission endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.schemas.auth.permission import PermissionUpdate, PermissionResponse
from app.services.auth import require_permissions, permission_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    current_user: User = Depends(require_permissions(["permissions:update"]))
):
    """
    Update an existing permission.
    
    Requires 'permissions:update' permission.
    
    Path parameter:
    - permission_id: Permission ID to update
    
    Request body:
    {
        "name": "Updated Permission Name",
        "description": "Updated description",
        "category": "user_management",
        "action": "create",
        "resource": "users",
        "conditions": {}
    }
    
    Returns the updated permission.
    """
    try:
        try:
            permission_obj_id = ObjectId(permission_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid permission ID format"
            )
        
        # Get existing permission to track changes
        existing_permission = await permission_service.get_permission_by_id(permission_obj_id)
        if not existing_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PERMISSION_NOT_FOUND
            )
        
        # Update permission using service
        updated_permission = await permission_service.update_permission(
            permission_id=permission_obj_id,
            update_data=permission_data,
            updated_by=current_user.id
        )
        
        if not updated_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.PERMISSION_NOT_FOUND
            )
        
        logger.info(f"✅ [UPDATE_PERMISSION] Permission '{existing_permission['name']}' updated successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        
        # Track changes
        changes = {}
        if permission_data.name is not None and permission_data.name != existing_permission.get("name"):
            changes["name"] = {"from": existing_permission.get("name"), "to": permission_data.name}
        if permission_data.description is not None and permission_data.description != existing_permission.get("description"):
            changes["description"] = {"from": existing_permission.get("description"), "to": permission_data.description}
        if permission_data.category is not None and permission_data.category != existing_permission.get("category"):
            changes["category"] = {"from": existing_permission.get("category"), "to": permission_data.category}
        if permission_data.action is not None and permission_data.action != existing_permission.get("action"):
            changes["action"] = {"from": existing_permission.get("action"), "to": permission_data.action}
        if permission_data.resource is not None and permission_data.resource != existing_permission.get("resource"):
            changes["resource"] = {"from": existing_permission.get("resource"), "to": permission_data.resource}
        
        await audit_service.user_management.log_permission_updated(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            permission_id=permission_id,
            permission_key=existing_permission.get("key", existing_permission.get("name", "Unknown")),
            changes=changes,
            correlation_id=correlation_id
        )
        
        return PermissionResponse(**updated_permission)
        
    except ValueError as e:
        logger.warning(f"⚠️ [UPDATE_PERMISSION] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UPDATE_PERMISSION] Error updating permission: {str(e)}")
        raise handle_database_error(e, "update_permission", "permission") 