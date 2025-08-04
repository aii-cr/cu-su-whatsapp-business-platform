from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.business.department import DepartmentResponse
from app.services import department_service, audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.delete("/{department_id}")
async def delete_department(
    department_id: str,
    current_user: User = Depends(require_permissions(["departments:delete"])),
):
    """
    Delete a department by ID.
    Requires 'departments:delete' permission.
    """
    try:
        # Validate department ID
        try:
            ObjectId(department_id)
        except Exception:
            logger.warning(f"Invalid department ID format: {department_id}")
            error_response = get_error_response(ErrorCode.VALIDATION_ERROR, "Invalid department ID format")
            raise HTTPException(
                status_code=error_response["status_code"],
                detail=error_response["detail"]
            )
        
        # Get department for audit
        department = await department_service.get_department(department_id)
        if not department:
            logger.warning(f"Department not found: {department_id}")
            error_response = get_error_response(ErrorCode.DEPARTMENT_NOT_FOUND)
            raise HTTPException(
                status_code=error_response["status_code"],
                detail=error_response["detail"]
            )
        
        # Delete department
        success = await department_service.delete_department(department_id)
        
        if not success:
            logger.warning(f"Failed to delete department: {department_id}")
            error_response = get_error_response(ErrorCode.DEPARTMENT_IN_USE, "Department cannot be deleted")
            raise HTTPException(
                status_code=error_response["status_code"],
                detail=error_response["detail"]
            )
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_department_deleted(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            department_id=department_id,
            department_name=department["name"],
            correlation_id=correlation_id
        )
        
        logger.info(f"Department {department_id} deleted by user {current_user.id}")
        
        return {"message": "Department deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting department {department_id}: {str(e)}")
        error_response = get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        ) 