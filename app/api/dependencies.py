"""
Common API dependencies for the WhatsApp Business Platform.
Shared dependencies for authentication, pagination, and request validation.
"""

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from typing import Optional
from bson import ObjectId

from app.core.security import get_current_user, get_current_active_user
from app.db.models.auth import User

security = HTTPBearer()

# Authentication dependencies
async def get_authenticated_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current authenticated and active user."""
    return current_user

# Pagination dependencies
class PaginationParams:
    """Common pagination parameters."""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.per_page = per_page
        self.skip = (page - 1) * per_page

# Sorting dependencies
class SortingParams:
    """Common sorting parameters."""
    
    def __init__(
        self,
        sort_by: str = Query("created_at", description="Field to sort by"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.sort_direction = 1 if sort_order == "asc" else -1

# Search dependencies
class SearchParams:
    """Common search parameters."""
    
    def __init__(
        self,
        search: Optional[str] = Query(None, description="Search query")
    ):
        self.search = search

# Object ID validation
def validate_object_id(object_id: str) -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(object_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid object ID format"
        )

# Combined query parameters
class CommonQueryParams:
    """Combined common query parameters for list endpoints."""
    
    def __init__(
        self,
        pagination: PaginationParams = Depends(),
        sorting: SortingParams = Depends(),
        search: SearchParams = Depends()
    ):
        self.pagination = pagination
        self.sorting = sorting
        self.search = search
