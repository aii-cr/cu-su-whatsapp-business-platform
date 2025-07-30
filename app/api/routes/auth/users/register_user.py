"""User registration endpoint."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.schemas.auth.user import UserRegister, UserResponse
from app.services.auth import require_permissions, user_service
from app.db.models.auth import User
from app.services import audit_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister, current_user: User = Depends(require_permissions(["users:create"]))
):
    """
    Register a new user.
    
    Requires 'users:create' permission or super admin status.
    Can create super admin users if current user is super admin.
    
    Request body:
    {
        "first_name": "John",
        "last_name": "Doe", 
        "email": "john.doe@company.com",
        "phone": "+1234567890",
        "password": "SecurePassword123",
        "role_ids": ["role_id_1", "role_id_2"],
        "department_id": "department_id"
    }
    
    Returns the created user (without password).
    """
    try:
        # Create user using service
        created_user = await user_service.create_user(
            user_data=user_data,
            created_by=current_user.id,
            is_super_admin=False
        )
        
        logger.info(f"✅ [REGISTER_USER] User {user_data.email} created successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_user_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            created_user_id=str(created_user["_id"]),
            created_user_email=user_data.email,
            is_super_admin=False,
            department_id=str(user_data.department_id) if user_data.department_id else None,
            correlation_id=correlation_id
        )
        
        return UserResponse(**created_user)
        
    except ValueError as e:
        logger.warning(f"⚠️ [REGISTER_USER] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [REGISTER_USER] Error creating user: {str(e)}")
        raise handle_database_error(e, "register_user", "user")

@router.post("/register/super-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_super_admin(
    user_data: UserRegister, current_user: User = Depends(require_permissions(["users:create"]))
):
    """
    Register a new super admin user.
    
    Only super admins can create other super admin users.
    
    Request body:
    {
        "first_name": "Super",
        "last_name": "Admin",
        "email": "admin@company.com", 
        "phone": "+1234567890",
        "password": "SecurePassword123",
        "role_ids": ["role_id_1"],
        "department_id": "department_id"
    }
    
    Returns the created super admin user.
    """
    try:
        # Check if current user is super admin
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can create other super admin users"
            )
        
        # Create super admin user using service
        created_user = await user_service.create_user(
            user_data=user_data,
            created_by=current_user.id,
            is_super_admin=True
        )
        
        logger.info(f"✅ [REGISTER_SUPER_ADMIN] Super admin {user_data.email} created successfully by {current_user.email}")
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_user_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            created_user_id=str(created_user["_id"]),
            created_user_email=user_data.email,
            is_super_admin=True,
            department_id=str(user_data.department_id) if user_data.department_id else None,
            correlation_id=correlation_id
        )
        
        return UserResponse(**created_user)
        
    except ValueError as e:
        logger.warning(f"⚠️ [REGISTER_SUPER_ADMIN] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [REGISTER_SUPER_ADMIN] Error creating super admin: {str(e)}")
        raise handle_database_error(e, "register_super_admin", "user") 