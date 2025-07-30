"""Create permission endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.schemas.auth.permission import PermissionCreate, PermissionResponse
from app.services.auth import require_permissions, permission_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.post("/create", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_permissions(["permissions:create"]))
):
    """
    Create a new permission.
    
    Requires 'permissions:create' permission.
    
    Request body:
    {
        "name": "Create Users",
        "description": "Allow creating new user accounts",
        "category": "user_management",
        "action": "create",
        "resource": "users",
        "is_system_permission": false,
        "conditions": {}
    }
    
    Returns the created permission.
    """
    try:
        # Create permission using service
        created_permission = await permission_service.create_permission(
            permission_data=permission_data,
            created_by=current_user.id
        )
        
        logger.info(f"✅ [CREATE_PERMISSION] Permission '{permission_data.name}' created successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_permission_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            permission_id=str(created_permission["_id"]),
            permission_key=permission_data.name.lower().replace(" ", "_"),
            permission_name=permission_data.name,
            is_system_permission=permission_data.is_system_permission,
            correlation_id=correlation_id
        )
        
        return PermissionResponse(**created_permission)
        
    except ValueError as e:
        logger.warning(f"⚠️ [CREATE_PERMISSION] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [CREATE_PERMISSION] Error creating permission: {str(e)}")
        raise handle_database_error(e, "create_permission", "permission") 