"""Permission-related request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

# Permission Creation
class PermissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    description: Optional[str] = Field(None, max_length=500, description="Permission description")
    category: str = Field(..., description="Permission category")
    action: str = Field(..., description="Permission action")
    resource: str = Field(..., description="Resource this permission applies to")
    is_system_permission: bool = Field(False, description="Whether this is a system permission")
    conditions: Dict[str, Any] = Field(default={}, description="Permission conditions")

# Permission Update
class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated permission name")
    description: Optional[str] = Field(None, max_length=500, description="Updated permission description")
    category: Optional[str] = Field(None, description="Updated permission category")
    action: Optional[str] = Field(None, description="Updated permission action")
    resource: Optional[str] = Field(None, description="Updated resource")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Updated permission conditions")

# Permission Response
class PermissionResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    description: Optional[str] = None
    category: str
    action: str
    resource: str
    is_system_permission: bool
    conditions: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    role_count: int = 0  # Number of roles with this permission

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Permission List Response
class PermissionListResponse(BaseModel):
    permissions: List[PermissionResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Grouped Permissions Response
class GroupedPermissionsResponse(BaseModel):
    categories: Dict[str, List[PermissionResponse]]
    total: int

# Permission Query Parameters
class PermissionQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in permission name or description")
    category: Optional[str] = Field(None, description="Filter by category")
    action: Optional[str] = Field(None, description="Filter by action")
    resource: Optional[str] = Field(None, description="Filter by resource")
    is_system_permission: Optional[bool] = Field(None, description="Filter by system permission status")
    group_by_category: bool = Field(False, description="Group permissions by category")
    sort_by: str = Field("category", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

# Permission Check Request
class PermissionCheckRequest(BaseModel):
    user_id: PyObjectId = Field(..., description="User ID to check permissions for")
    permission: str = Field(..., description="Permission to check")
    resource_id: Optional[str] = Field(None, description="Specific resource ID")
    context: Dict[str, Any] = Field(default={}, description="Additional context for permission check")

# Permission Check Response
class PermissionCheckResponse(BaseModel):
    has_permission: bool
    permission: str
    user_id: PyObjectId
    resource_id: Optional[str] = None
    reasons: List[str] = []  # Reasons why permission was granted/denied

# Bulk Permission Assignment
class BulkPermissionAssignment(BaseModel):
    role_id: PyObjectId = Field(..., description="Role ID to assign permissions to")
    permission_ids: List[PyObjectId] = Field(..., description="List of permission IDs to assign")

# Permission Statistics
class PermissionStatsResponse(BaseModel):
    total_permissions: int
    system_permissions: int
    custom_permissions: int
    permissions_by_category: Dict[str, int]
    most_used_permissions: List[Dict[str, Any]]  # Top 10 permissions by role count 