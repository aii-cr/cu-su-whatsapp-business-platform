"""
Audit log model for the WhatsApp Business Platform.
Tracks all system activities, changes, and user actions for compliance and monitoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId
from enum import Enum
from app.db.models.base import PyObjectId

class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Authentication actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # Role and permission management
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    
    # Conversation management
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_UPDATED = "conversation_updated"
    CONVERSATION_TRANSFERRED = "conversation_transferred"
    CONVERSATION_CLOSED = "conversation_closed"
    CONVERSATION_REOPENED = "conversation_reopened"
    
    # Message actions
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_FLAGGED = "message_flagged"
    
    # Media actions
    MEDIA_UPLOADED = "media_uploaded"
    MEDIA_DOWNLOADED = "media_downloaded"
    MEDIA_DELETED = "media_deleted"
    
    # System actions
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    CONFIGURATION_CHANGED = "configuration_changed"
    WEBHOOK_RECEIVED = "webhook_received"
    
    # Department actions
    DEPARTMENT_CREATED = "department_created"
    DEPARTMENT_UPDATED = "department_updated"
    DEPARTMENT_DELETED = "department_deleted"
    
    # Export and import
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"

class AuditLevel(str, Enum):
    """Audit log levels for categorization."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditLog(BaseModel):
    """
    Audit log model for tracking system activities and changes.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core audit information
    action: AuditAction = Field(..., description="Type of action performed")
    level: AuditLevel = Field(default=AuditLevel.INFO, description="Log level")
    description: str = Field(..., max_length=1000, description="Human-readable description of the action")
    
    # Actor information
    user_id: Optional[PyObjectId] = Field(None, description="ID of user who performed the action")
    user_email: Optional[str] = Field(None, description="Email of user who performed the action")
    user_name: Optional[str] = Field(None, description="Name of user who performed the action")
    user_role: Optional[str] = Field(None, description="Role of user who performed the action")
    
    # System context
    ip_address: Optional[str] = Field(None, description="IP address of the actor")
    user_agent: Optional[str] = Field(None, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Target resource information
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected")
    resource_name: Optional[str] = Field(None, description="Name/title of the resource affected")
    
    # Change tracking
    changes: Dict[str, Any] = Field(
        default_factory=lambda: {
            "before": {},
            "after": {},
            "fields_changed": []
        },
        description="Details of changes made"
    )
    
    # Additional context
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context and metadata"
    )
    
    # Related entities
    conversation_id: Optional[PyObjectId] = Field(None, description="Related conversation ID")
    message_id: Optional[PyObjectId] = Field(None, description="Related message ID")
    department_id: Optional[PyObjectId] = Field(None, description="Related department ID")
    
    # Result and status
    success: bool = Field(default=True, description="Whether the action was successful")
    error_message: Optional[str] = Field(None, description="Error message if action failed")
    error_code: Optional[str] = Field(None, description="Error code if action failed")
    
    # Compliance and retention
    retention_period_days: int = Field(default=2555, description="Retention period in days (7 years default)")
    is_sensitive: bool = Field(default=False, description="Contains sensitive information")
    compliance_tags: List[str] = Field(default_factory=list, description="Compliance classification tags")
    
    # Geolocation (if available)
    location_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Geolocation information"
    )
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the action occurred")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Indexing fields
    date_partition: str = Field(default_factory=lambda: datetime.now(datetime.UTC).strftime("%Y%m%d"))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "action": "conversation_created",
                "level": "info",
                "description": "New conversation created for customer +1234567890",
                "user_id": "60a7c8b9f123456789abcdef",
                "user_email": "agent@company.com",
                "resource_type": "conversation",
                "resource_id": "60a7c8b9f123456789abcdef",
                "success": True
            }
        }

class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries."""
    action: AuditAction
    level: AuditLevel = AuditLevel.INFO
    description: str = Field(..., max_length=1000)
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    department_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    error_code: Optional[str] = None

class AuditLogResponse(BaseModel):
    """Schema for audit log responses."""
    id: str = Field(alias="_id")
    action: AuditAction
    level: AuditLevel
    description: str
    user_id: Optional[str]
    user_email: Optional[str]
    user_name: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    changes: Dict[str, Any]
    metadata: Dict[str, Any]
    conversation_id: Optional[str]
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        populate_by_name = True

class AuditLogQuery(BaseModel):
    """Schema for querying audit logs."""
    action: Optional[AuditAction] = None
    level: Optional[AuditLevel] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    conversation_id: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0) 