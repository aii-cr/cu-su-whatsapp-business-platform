from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.business.department import DepartmentUpdate, DepartmentResponse
from app.services import department_service, audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_update: DepartmentUpdate,
    current_user: User = Depends(require_permissions(["departments:update"])),
):
    """
    Update a department by ID.
    Requires 'departments:update' permission.
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
        
        # Get current department for audit
        current_department = await department_service.get_department(department_id)
        if not current_department:
            logger.warning(f"Department not found: {department_id}")
            error_response = get_error_response(ErrorCode.DEPARTMENT_NOT_FOUND)
            raise HTTPException(
                status_code=error_response["status_code"],
                detail=error_response["detail"]
            )
        
        # Prepare update data
        update_data = department_update.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user.id
            
            # Update department
            updated_department = await department_service.update_department(
                department_id=department_id,
                update_data=update_data,
                updated_by=current_user.id
            )
            
            if not updated_department:
                logger.warning(f"Department not found during update: {department_id}")
                error_response = get_error_response(ErrorCode.DEPARTMENT_NOT_FOUND)
                raise HTTPException(
                    status_code=error_response["status_code"],
                    detail=error_response["detail"]
                )
            
            # ===== AUDIT LOGGING =====
            correlation_id = get_correlation_id()
            await audit_service.user_management.log_department_updated(
                actor_id=str(current_user.id),
                actor_name=current_user.name or current_user.email,
                department_id=department_id,
                department_name=current_department["name"],
                changes=update_data,
                correlation_id=correlation_id
            )
            
            logger.info(f"Department {department_id} updated by user {current_user.id}")
            
            return DepartmentResponse(**updated_department)
        else:
            # No changes to update
            return DepartmentResponse(**current_department)
        
    except ValueError as e:
        logger.warning(f"Validation error updating department {department_id}: {str(e)}")
        error_response = get_error_response(ErrorCode.DEPARTMENT_ALREADY_EXISTS, str(e))
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating department {department_id}: {str(e)}")
        error_response = get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        ) 