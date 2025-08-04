from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.business.department import DepartmentResponse
from app.services import department_service
from app.services.auth import require_permissions

router = APIRouter()

@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: str,
    current_user: User = Depends(require_permissions(["departments:read"])),
):
    """
    Get a department by ID.
    Requires 'departments:read' permission.
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
        
        # Get department
        department = await department_service.get_department(department_id)
        
        if not department:
            logger.warning(f"Department not found: {department_id}")
            error_response = get_error_response(ErrorCode.DEPARTMENT_NOT_FOUND)
            raise HTTPException(
                status_code=error_response["status_code"],
                detail=error_response["detail"]
            )
        
        return DepartmentResponse(**department)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting department {department_id}: {str(e)}")
        error_response = get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        ) 