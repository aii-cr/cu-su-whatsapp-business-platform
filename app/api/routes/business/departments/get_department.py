from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department ID"
            )
        
        # Get department
        department = await department_service.get_department(department_id)
        
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        return DepartmentResponse(**department)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting department {department_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get department"
        ) 