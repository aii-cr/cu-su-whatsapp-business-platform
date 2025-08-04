from fastapi import APIRouter, Depends, HTTPException, Query

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.business.department import DepartmentListResponse, DepartmentResponse
from app.services import department_service
from app.services.auth import require_permissions

router = APIRouter()

@router.get("/", response_model=DepartmentListResponse)
async def list_departments(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search in department name"),
    status: str = Query(None, description="Filter by status"),
    current_user: User = Depends(require_permissions(["departments:read"])),
):
    """
    List departments with pagination and filtering.
    Requires 'departments:read' permission.
    """
    try:
        # Get departments
        result = await department_service.list_departments(
            status=status,
            search=search,
            page=page,
            per_page=per_page
        )
        
        # Convert to response format
        departments = []
        for dept in result["departments"]:
            try:
                departments.append(DepartmentResponse(**dept))
            except Exception as e:
                logger.warning(f"Error converting department {dept.get('_id')}: {str(e)}")
                continue
        
        return DepartmentListResponse(
            departments=departments,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Unexpected error listing departments: {str(e)}")
        error_response = get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        ) 