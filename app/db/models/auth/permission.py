"""
Permission model for the WhatsApp Business Platform RBAC system.
Defines granular permissions that can be assigned to roles.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from app.db.models.base import PyObjectId

class PermissionCategory(str, Enum):
    """Categories for organizing permissions."""
    USER_MANAGEMENT = "user_management"
    ROLE_MANAGEMENT = "role_management"
    CONVERSATION_MANAGEMENT = "conversation_management"
    MESSAGE_MANAGEMENT = "message_management"
    MEDIA_MANAGEMENT = "media_management"
    DEPARTMENT_MANAGEMENT = "department_management"
    COMPANY_SETTINGS = "company_settings"
    ANALYTICS_REPORTS = "analytics_reports"
    SYSTEM_ADMINISTRATION = "system_administration"
    WHATSAPP_MANAGEMENT = "whatsapp_management"

class PermissionAction(str, Enum):
    """Standard CRUD actions for permissions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ASSIGN = "assign"
    TRANSFER = "transfer"
    EXPORT = "export"

class Permission(BaseModel):
    """
    Permission model for granular access control.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    key: str = Field(..., min_length=1, max_length=100, description="Unique permission key (e.g., 'conversations.create')")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable permission name")
    description: str = Field(..., min_length=1, max_length=500, description="Detailed permission description")
    
    # Categorization
    category: PermissionCategory = Field(..., description="Permission category")
    action: PermissionAction = Field(..., description="Action type")
    resource: str = Field(..., min_length=1, max_length=50, description="Resource being accessed")
    
    # Permission properties
    is_system_permission: bool = Field(default=True, description="Whether this is a system-defined permission")
    is_active: bool = Field(default=True, description="Whether this permission is active")
    requires_approval: bool = Field(default=False, description="Whether actions with this permission require approval")
    
    # Scope and constraints
    scope: Dict[str, Any] = Field(
        default_factory=lambda: {
            "department_scoped": False,
            "self_only": False,
            "conditions": []
        },
        description="Permission scope and constraints"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[PyObjectId] = Field(None, description="User ID who created this permission")
    updated_by: Optional[PyObjectId] = Field(None, description="User ID who last updated this permission")
    
    # Usage statistics
    role_count: int = Field(default=0, description="Number of roles with this permission")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "key": "conversations.create",
                "name": "Create Conversations",
                "description": "Allows creating new conversations with customers",
                "category": "conversation_management",
                "action": "create",
                "resource": "conversations",
                "is_system_permission": True,
                "scope": {
                    "department_scoped": False,
                    "self_only": False,
                    "conditions": []
                }
            }
        }

class PermissionCreate(BaseModel):
    """Schema for creating a new permission."""
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    category: PermissionCategory
    action: PermissionAction
    resource: str = Field(..., min_length=1, max_length=50)
    requires_approval: bool = False
    scope: Optional[Dict[str, Any]] = None

class PermissionUpdate(BaseModel):
    """Schema for updating an existing permission."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None
    scope: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PermissionResponse(BaseModel):
    """Schema for permission responses."""
    id: str = Field(alias="_id")
    key: str
    name: str
    description: str
    category: PermissionCategory
    action: PermissionAction
    resource: str
    is_system_permission: bool
    is_active: bool
    requires_approval: bool
    scope: Dict[str, Any]
    role_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True

# Predefined system permissions
SYSTEM_PERMISSIONS = [
    # User Management
    {"key": "users.create", "name": "Create Users", "description": "Create new user accounts", 
     "category": PermissionCategory.USER_MANAGEMENT, "action": PermissionAction.CREATE, "resource": "users"},
    {"key": "users.read", "name": "View Users", "description": "View user accounts and profiles", 
     "category": PermissionCategory.USER_MANAGEMENT, "action": PermissionAction.READ, "resource": "users"},
    {"key": "users.update", "name": "Update Users", "description": "Modify user accounts and profiles", 
     "category": PermissionCategory.USER_MANAGEMENT, "action": PermissionAction.UPDATE, "resource": "users"},
    {"key": "users.delete", "name": "Delete Users", "description": "Delete user accounts", 
     "category": PermissionCategory.USER_MANAGEMENT, "action": PermissionAction.DELETE, "resource": "users"},
    
    # Role Management
    {"key": "roles.create", "name": "Create Roles", "description": "Create new user roles", 
     "category": PermissionCategory.ROLE_MANAGEMENT, "action": PermissionAction.CREATE, "resource": "roles"},
    {"key": "roles.read", "name": "View Roles", "description": "View user roles and permissions", 
     "category": PermissionCategory.ROLE_MANAGEMENT, "action": PermissionAction.READ, "resource": "roles"},
    {"key": "roles.update", "name": "Update Roles", "description": "Modify user roles and permissions", 
     "category": PermissionCategory.ROLE_MANAGEMENT, "action": PermissionAction.UPDATE, "resource": "roles"},
    {"key": "roles.delete", "name": "Delete Roles", "description": "Delete user roles", 
     "category": PermissionCategory.ROLE_MANAGEMENT, "action": PermissionAction.DELETE, "resource": "roles"},
    {"key": "roles.assign", "name": "Assign Roles", "description": "Assign roles to users", 
     "category": PermissionCategory.ROLE_MANAGEMENT, "action": PermissionAction.ASSIGN, "resource": "roles"},
    
    # Conversation Management
    {"key": "conversations.create", "name": "Create Conversations", "description": "Start new conversations", 
     "category": PermissionCategory.CONVERSATION_MANAGEMENT, "action": PermissionAction.CREATE, "resource": "conversations"},
    {"key": "conversations.read", "name": "View Conversations", "description": "View conversation details and history", 
     "category": PermissionCategory.CONVERSATION_MANAGEMENT, "action": PermissionAction.READ, "resource": "conversations"},
    {"key": "conversations.update", "name": "Update Conversations", "description": "Modify conversation details and status", 
     "category": PermissionCategory.CONVERSATION_MANAGEMENT, "action": PermissionAction.UPDATE, "resource": "conversations"},
    {"key": "conversations.transfer", "name": "Transfer Conversations", "description": "Transfer conversations to other agents", 
     "category": PermissionCategory.CONVERSATION_MANAGEMENT, "action": PermissionAction.TRANSFER, "resource": "conversations"},
    {"key": "conversations.close", "name": "Close Conversations", "description": "Close and resolve conversations", 
     "category": PermissionCategory.CONVERSATION_MANAGEMENT, "action": PermissionAction.UPDATE, "resource": "conversations"},
    {"key": "conversations.delete", "name": "Delete Conversations", "description": "Delete conversations and all associated data", 
     "category": PermissionCategory.CONVERSATION_MANAGEMENT, "action": PermissionAction.DELETE, "resource": "conversations"},
    
    # Message Management
    {"key": "messages.create", "name": "Send Messages", "description": "Send messages in conversations", 
     "category": PermissionCategory.MESSAGE_MANAGEMENT, "action": PermissionAction.CREATE, "resource": "messages"},
    {"key": "messages.read", "name": "View Messages", "description": "View message history", 
     "category": PermissionCategory.MESSAGE_MANAGEMENT, "action": PermissionAction.READ, "resource": "messages"},
    {"key": "messages.delete", "name": "Delete Messages", "description": "Delete messages from conversations", 
     "category": PermissionCategory.MESSAGE_MANAGEMENT, "action": PermissionAction.DELETE, "resource": "messages"},
    
    # Media Management
    {"key": "media.upload", "name": "Upload Media", "description": "Upload media files", 
     "category": PermissionCategory.MEDIA_MANAGEMENT, "action": PermissionAction.CREATE, "resource": "media"},
    {"key": "media.download", "name": "Download Media", "description": "Download media files", 
     "category": PermissionCategory.MEDIA_MANAGEMENT, "action": PermissionAction.READ, "resource": "media"},
    {"key": "media.delete", "name": "Delete Media", "description": "Delete media files", 
     "category": PermissionCategory.MEDIA_MANAGEMENT, "action": PermissionAction.DELETE, "resource": "media"},
    
    # Department Management
    {"key": "departments.create", "name": "Create Departments", "description": "Create new departments", 
     "category": PermissionCategory.DEPARTMENT_MANAGEMENT, "action": PermissionAction.CREATE, "resource": "departments"},
    {"key": "departments.read", "name": "View Departments", "description": "View department information", 
     "category": PermissionCategory.DEPARTMENT_MANAGEMENT, "action": PermissionAction.READ, "resource": "departments"},
    {"key": "departments.update", "name": "Update Departments", "description": "Modify department information", 
     "category": PermissionCategory.DEPARTMENT_MANAGEMENT, "action": PermissionAction.UPDATE, "resource": "departments"},
    {"key": "departments.delete", "name": "Delete Departments", "description": "Delete departments", 
     "category": PermissionCategory.DEPARTMENT_MANAGEMENT, "action": PermissionAction.DELETE, "resource": "departments"},
    
    # Company Settings
    {"key": "company.read", "name": "View Company Settings", "description": "View company profile and settings", 
     "category": PermissionCategory.COMPANY_SETTINGS, "action": PermissionAction.READ, "resource": "company"},
    {"key": "company.update", "name": "Update Company Settings", "description": "Modify company profile and settings", 
     "category": PermissionCategory.COMPANY_SETTINGS, "action": PermissionAction.UPDATE, "resource": "company"},
    
    # Analytics and Reports
    {"key": "analytics.read", "name": "View Analytics", "description": "View analytics and reports", 
     "category": PermissionCategory.ANALYTICS_REPORTS, "action": PermissionAction.READ, "resource": "analytics"},
    {"key": "analytics.export", "name": "Export Reports", "description": "Export analytics and reports", 
     "category": PermissionCategory.ANALYTICS_REPORTS, "action": PermissionAction.EXPORT, "resource": "analytics"},
    
    # System Administration
    {"key": "system.admin", "name": "System Administration", "description": "Full system administration access", 
     "category": PermissionCategory.SYSTEM_ADMINISTRATION, "action": PermissionAction.EXECUTE, "resource": "system"},
    {"key": "audit_logs.read", "name": "View Audit Logs", "description": "View system audit logs", 
     "category": PermissionCategory.SYSTEM_ADMINISTRATION, "action": PermissionAction.READ, "resource": "audit_logs"},
] 