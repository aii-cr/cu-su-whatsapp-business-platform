"""Role-related request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

# Role Creation
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")
    permission_ids: List[PyObjectId] = Field(default=[], description="List of permission IDs")
    is_system_role: bool = Field(False, description="Whether this is a system role")
    is_active: bool = Field(True, description="Whether the role is active")
    settings: Dict[str, Any] = Field(default={}, description="Role-specific settings")

# Role Update
class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated role name")
    description: Optional[str] = Field(None, max_length=500, description="Updated role description")
    permission_ids: Optional[List[PyObjectId]] = Field(None, description="Updated list of permission IDs")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    settings: Optional[Dict[str, Any]] = Field(None, description="Updated role-specific settings")

# Role Response
class RoleResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    description: Optional[str] = None
    permission_ids: List[PyObjectId] = []
    is_system_role: bool
    is_active: bool
    settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    user_count: int = 0  # Number of users with this role

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Role with Permissions Response
class RoleWithPermissionsResponse(RoleResponse):
    permissions: List[Dict[str, Any]] = []  # Full permission details

# Role List Response
class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Role Assignment
class RoleAssignment(BaseModel):
    user_id: PyObjectId = Field(..., description="User ID to assign role to")
    role_id: PyObjectId = Field(..., description="Role ID to assign")

# Role Unassignment
class RoleUnassignment(BaseModel):
    user_id: PyObjectId = Field(..., description="User ID to remove role from")
    role_id: PyObjectId = Field(..., description="Role ID to remove")

# Role Query Parameters
class RoleQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in role name or description")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_system_role: Optional[bool] = Field(None, description="Filter by system role status")
    include_permissions: bool = Field(False, description="Include permission details")
    sort_by: str = Field("name", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

# Role Statistics
class RoleStatsResponse(BaseModel):
    total_roles: int
    active_roles: int
    system_roles: int
    custom_roles: int
    most_assigned_roles: List[Dict[str, Any]]  # Top 5 roles by user count 