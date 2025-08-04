"""Update role endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.schemas.auth.role import RoleUpdate, RoleResponse
from app.services.auth import require_permissions, role_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: User = Depends(require_permissions(["roles:update"]))
):
    """
    Update an existing role.
    
    Requires 'roles:update' permission.
    
    Path parameter:
    - role_id: Role ID to update
    
    Request body:
    {
        "name": "Updated Role Name",
        "description": "Updated description",
        "permission_ids": ["permission_id_1", "permission_id_2"],
        "is_active": true,
        "settings": {
            "max_concurrent_chats": 10,
            "can_transfer_chats": true
        }
    }
    
    Returns the updated role.
    """
    try:
        try:
            role_obj_id = ObjectId(role_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role ID format"
            )
        
        # Get existing role to track changes
        existing_role = await role_service.get_role_by_id(role_obj_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.ROLE_NOT_FOUND
            )
        
        # Update role using service
        updated_role = await role_service.update_role(
            role_id=role_obj_id,
            update_data=role_data,
            updated_by=current_user.id
        )
        
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.ROLE_NOT_FOUND
            )
        
        logger.info(f"✅ [UPDATE_ROLE] Role '{existing_role['name']}' updated successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        
        # Track changes
        changes = {}
        if role_data.name is not None and role_data.name != existing_role.get("name"):
            changes["name"] = {"from": existing_role.get("name"), "to": role_data.name}
        if role_data.description is not None and role_data.description != existing_role.get("description"):
            changes["description"] = {"from": existing_role.get("description"), "to": role_data.description}
        if role_data.is_active is not None and role_data.is_active != existing_role.get("is_active"):
            changes["is_active"] = {"from": existing_role.get("is_active"), "to": role_data.is_active}
        if role_data.permission_ids is not None:
            changes["permission_ids"] = {"from": existing_role.get("permission_ids", []), "to": role_data.permission_ids}
        
        await audit_service.user_management.log_role_updated(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            role_id=role_id,
            role_name=existing_role.get("name", "Unknown"),
            changes=changes,
            correlation_id=correlation_id
        )
        
        return RoleResponse(**updated_role)
        
    except ValueError as e:
        logger.warning(f"⚠️ [UPDATE_ROLE] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UPDATE_ROLE] Error updating role: {str(e)}")
        raise handle_database_error(e, "update_role", "role") 