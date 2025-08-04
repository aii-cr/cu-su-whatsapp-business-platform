"""Create role endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.schemas.auth.role import RoleCreate, RoleResponse
from app.services.auth import require_permissions, role_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.post("/create", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_permissions(["roles:create"]))
):
    """
    Create a new role.
    
    Requires 'roles:create' permission.
    
    Request body:
    {
        "name": "agent",
        "description": "Customer service agent role",
        "permission_ids": ["permission_id_1", "permission_id_2"],
        "is_system_role": false,
        "is_active": true,
        "settings": {
            "max_concurrent_chats": 5,
            "can_transfer_chats": true
        }
    }
    
    Returns the created role.
    """
    try:
        # Create role using service
        created_role = await role_service.create_role(
            role_data=role_data,
            created_by=current_user.id
        )
        
        logger.info(f"✅ [CREATE_ROLE] Role '{role_data.name}' created successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_role_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            role_id=str(created_role["_id"]),
            role_name=role_data.name,
            is_system_role=role_data.is_system_role,
            correlation_id=correlation_id
        )
        
        return RoleResponse(**created_role)
        
    except ValueError as e:
        logger.warning(f"⚠️ [CREATE_ROLE] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [CREATE_ROLE] Error creating role: {str(e)}")
        raise handle_database_error(e, "create_role", "role") 