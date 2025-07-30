"""List users endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from bson import ObjectId

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.auth.user import UserResponse, UserListResponse
from app.services.auth import require_permissions, user_service
from app.db.models.auth import User
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/list", response_model=UserListResponse)
async def list_users(
    search: Optional[str] = Query(None, description="Search by name, email, first name, or last name"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    email: Optional[str] = Query(None, description="Filter by exact email address"),
    phone: Optional[str] = Query(None, description="Filter by phone number"),
    first_name: Optional[str] = Query(None, description="Filter by first name"),
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    role_id: Optional[str] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_super_admin: Optional[bool] = Query(None, description="Filter by super admin status"),
    status: Optional[str] = Query(None, description="Filter by user status"),
    created_after: Optional[str] = Query(None, description="Filter users created after this date (ISO format)"),
    created_before: Optional[str] = Query(None, description="Filter users created before this date (ISO format)"),
    last_login_after: Optional[str] = Query(None, description="Filter users who logged in after this date (ISO format)"),
    last_login_before: Optional[str] = Query(None, description="Filter users who logged in before this date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_permissions(["users:read"]))
):
    """
    List all users with comprehensive filtering and pagination.
    
    Requires 'users:read' permission.
    
    Query parameters:
    - search: Search by name, email, first name, or last name
    - user_id: Filter by specific user ID
    - email: Filter by exact email address
    - phone: Filter by phone number
    - first_name: Filter by first name
    - last_name: Filter by last name
    - department_id: Filter by department ID
    - role_id: Filter by role ID
    - is_active: Filter by active status (true/false)
    - is_super_admin: Filter by super admin status (true/false)
    - status: Filter by user status
    - created_after: Filter users created after this date (ISO format)
    - created_before: Filter users created before this date (ISO format)
    - last_login_after: Filter users who logged in after this date (ISO format)
    - last_login_before: Filter users who logged in before this date (ISO format)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    
    Returns paginated list of users.
    """
    try:
        # Convert string IDs to ObjectId if provided
        user_obj_id = None
        department_obj_id = None
        role_obj_id = None
        
        if user_id:
            try:
                user_obj_id = ObjectId(user_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format"
                )
        
        if department_id:
            try:
                department_obj_id = ObjectId(department_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid department ID format"
                )
        
        if role_id:
            try:
                role_obj_id = ObjectId(role_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role ID format"
                )
        
        # Parse date filters
        from datetime import datetime
        created_after_date = None
        created_before_date = None
        last_login_after_date = None
        last_login_before_date = None
        
        if created_after:
            try:
                created_after_date = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_after date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        if created_before:
            try:
                created_before_date = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_before date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        if last_login_after:
            try:
                last_login_after_date = datetime.fromisoformat(last_login_after.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid last_login_after date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        if last_login_before:
            try:
                last_login_before_date = datetime.fromisoformat(last_login_before.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid last_login_before date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )
        
        # Get users using service with enhanced filtering
        result = await user_service.list_users(
            search=search,
            user_id=user_obj_id,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            department_id=department_obj_id,
            role_id=role_obj_id,
            is_active=is_active,
            is_super_admin=is_super_admin,
            status=status,
            created_after=created_after_date,
            created_before=created_before_date,
            last_login_after=last_login_after_date,
            last_login_before=last_login_before_date,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"✅ [LIST_USERS] Retrieved {len(result['users'])} users by {current_user.email}")
        
        # Convert users to UserResponse objects
        users = [UserResponse(**user) for user in result["users"]]
        
        return UserListResponse(
            users=users,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [LIST_USERS] Error listing users: {str(e)}")
        raise handle_database_error(e, "list_users", "user") 