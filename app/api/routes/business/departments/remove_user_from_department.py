from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.services import department_service, audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.delete("/{department_id}/users/{user_id}")
async def remove_user_from_department(
    department_id: str,
    user_id: str,
    current_user: User = Depends(require_permissions(["departments:manage_users"])),
):
    """
    Remove a user from a department.
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
        
        # Remove user from department
        success = await department_service.remove_user_from_department(department_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove user from department"
            )
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_user_removed_from_department(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            department_id=department_id,
            department_name=department["name"],
            user_id=user_id,
            correlation_id=correlation_id
        )
        
        logger.info(f"User {user_id} removed from department {department_id} by user {current_user.id}")
        
        return {"message": "User removed from department successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error removing user {user_id} from department {department_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user from department"
        ) 