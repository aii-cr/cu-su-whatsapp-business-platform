"""List roles endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from bson import ObjectId

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.role import RoleResponse, RoleListResponse
from app.services.auth import require_permissions, role_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/list", response_model=RoleListResponse)
async def list_roles(
    search: Optional[str] = Query(None, description="Search by role name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_system_role: Optional[bool] = Query(None, description="Filter by system role status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_permissions(["roles:read"]))
):
    """
    List all roles with filtering and pagination.
    
    Requires 'roles:read' permission.
    
    Query parameters:
    - search: Search by role name or description
    - is_active: Filter by active status (true/false)
    - is_system_role: Filter by system role status (true/false)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    
    Returns paginated list of roles.
    """
    try:
        # Get roles using service
        result = await role_service.list_roles(
            search=search,
            is_active=is_active,
            is_system_role=is_system_role,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"✅ [LIST_ROLES] Retrieved {len(result['roles'])} roles by {current_user.email}")
        
        # Convert roles to RoleResponse objects
        roles = [RoleResponse(**role) for role in result["roles"]]
        
        return RoleListResponse(
            roles=roles,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"❌ [LIST_ROLES] Error listing roles: {str(e)}")
        raise handle_database_error(e, "list_roles", "role") 