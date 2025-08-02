from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.business.department import DepartmentListResponse
from app.services import department_service
from app.services.auth import require_permissions

router = APIRouter()

@router.get("/", response_model=DepartmentListResponse)
async def list_departments(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name or display_name"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_permissions(["departments:read"])),
):
    """
    List departments with optional filtering.
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
        
        return DepartmentListResponse(**result)
        
    except Exception as e:
        logger.error(f"Unexpected error listing departments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list departments"
        ) 