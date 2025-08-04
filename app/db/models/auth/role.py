"""
Role model for the WhatsApp Business Platform RBAC system.
Represents roles that can be assigned to users with specific permissions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.models.base import PyObjectId

class Role(BaseModel):
    """
    Role model for role-based access control (RBAC).
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=50, description="Role name (unique)")
    display_name: str = Field(..., min_length=1, max_length=100, description="Human-readable role name")
    description: Optional[str] = Field(None, max_length=500, description="Role description")
    
    # Permissions
    permission_ids: List[PyObjectId] = Field(default_factory=list, description="List of permission IDs")
    
    # Role settings
    is_system_role: bool = Field(default=False, description="Whether this is a system-defined role")
    is_active: bool = Field(default=True, description="Whether this role is active")
    default_for_department: Optional[PyObjectId] = Field(None, description="Default role for specific department")
    
    # Hierarchy and inheritance
    parent_role_id: Optional[PyObjectId] = Field(None, description="Parent role for inheritance")
    inherits_permissions: bool = Field(default=False, description="Whether to inherit parent permissions")
    
    # Role-specific limits and settings
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_concurrent_chats": 5,
            "can_transfer_chats": True,
            "can_close_chats": True,
            "can_view_all_chats": False,
            "can_export_data": False,
            "session_timeout_minutes": 480
        },
        description="Role-specific settings and limits"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="User ID who created this role")
    updated_by: Optional[PyObjectId] = Field(None, description="User ID who last updated this role")
    
    # Usage statistics
    user_count: int = Field(default=0, description="Number of users with this role")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "agent",
                "display_name": "Customer Service Agent",
                "description": "Standard customer service agent with chat handling capabilities",
                "is_system_role": True,
                "is_active": True,
                "settings": {
                    "max_concurrent_chats": 5,
                    "can_transfer_chats": True,
                    "can_close_chats": True,
                    "can_view_all_chats": False
                }
            }
        }

class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: List[str] = Field(default_factory=list)
    parent_role_id: Optional[str] = None
    inherits_permissions: bool = False
    settings: Optional[Dict[str, Any]] = None

class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permission_ids: Optional[List[str]] = None
    is_active: Optional[bool] = None
    parent_role_id: Optional[str] = None
    inherits_permissions: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RoleResponse(BaseModel):
    """Schema for role responses."""
    id: str = Field(alias="_id")
    name: str
    display_name: str
    description: Optional[str]
    permission_ids: List[str]
    is_system_role: bool
    is_active: bool
    parent_role_id: Optional[str]
    inherits_permissions: bool
    settings: Dict[str, Any]
    user_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True 