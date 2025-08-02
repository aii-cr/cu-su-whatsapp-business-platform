from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.services import department_service, audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.post("/{department_id}/users/{user_id}")
async def add_user_to_department(
    department_id: str,
    user_id: str,
    current_user: User = Depends(require_permissions(["departments:manage_users"])),
):
    """
    Add a user to a department.
    Requires 'departments:manage_users' permission.
    """
    try:
        # Validate IDs
        try:
            ObjectId(department_id)
            ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department or user ID"
            )
        
        # Get department for audit
        department = await department_service.get_department(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        # Add user to department
        success = await department_service.add_user_to_department(department_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add user to department"
            )
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_user_added_to_department(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            department_id=department_id,
            department_name=department["name"],
            user_id=user_id,
            correlation_id=correlation_id
        )
        
        logger.info(f"User {user_id} added to department {department_id} by user {current_user.id}")
        
        return {"message": "User added to department successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error adding user {user_id} to department {department_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add user to department"
        ) 