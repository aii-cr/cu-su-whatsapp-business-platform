"""List permissions endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from bson import ObjectId

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.permission import PermissionResponse, PermissionListResponse
from app.services.auth import require_permissions, permission_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/list", response_model=PermissionListResponse)
async def list_permissions(
    search: Optional[str] = Query(None, description="Search by permission name, key, or description"),
    category: Optional[str] = Query(None, description="Filter by permission category"),
    action: Optional[str] = Query(None, description="Filter by permission action"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_system_permission: Optional[bool] = Query(None, description="Filter by system permission status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_permissions(["permissions:read"]))
):
    """
    List all permissions with filtering and pagination.
    
    Requires 'permissions:read' permission.
    
    Query parameters:
    - search: Search by permission name, key, or description
    - category: Filter by permission category
    - action: Filter by permission action
    - resource: Filter by resource
    - is_active: Filter by active status (true/false)
    - is_system_permission: Filter by system permission status (true/false)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    
    Returns paginated list of permissions.
    """
    try:
        # Get permissions using service
        result = await permission_service.list_permissions(
            search=search,
            category=category,
            action=action,
            resource=resource,
            is_active=is_active,
            is_system_permission=is_system_permission,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"✅ [LIST_PERMISSIONS] Retrieved {len(result['permissions'])} permissions by {current_user.email}")
        
        # Convert permissions to PermissionResponse objects
        permissions = [PermissionResponse(**permission) for permission in result["permissions"]]
        
        return PermissionListResponse(
            permissions=permissions,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"❌ [LIST_PERMISSIONS] Error listing permissions: {str(e)}")
        raise handle_database_error(e, "list_permissions", "permission") 