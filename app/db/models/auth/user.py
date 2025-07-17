"""
User model for the WhatsApp Business Platform.
Represents users (agents, admins) with roles and permissions.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId
from enum import Enum

class UserStatus(str, Enum):
    """User account status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class UserRole(str, Enum):
    """Basic user roles."""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    AGENT = "agent"
    READONLY = "readonly"

class User(BaseModel):
    """
    User model representing agents, supervisors, and administrators.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="User's email address (unique)")
    phone_number: Optional[str] = Field(None, max_length=20)
    password_hash: str = Field(..., description="Hashed password")
    
    # Role and Department Information
    role_ids: List[PyObjectId] = Field(default_factory=list, description="List of assigned role IDs")
    department_id: Optional[PyObjectId] = Field(None, description="Primary department ID")
    is_super_admin: bool = Field(default=False, description="Super admin privileges")
    
    # Profile Information
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    timezone: str = Field(default="UTC", description="User's timezone")
    language: str = Field(default="en", description="Preferred language")
    
    # Status and Activity
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    is_online: bool = Field(default=False, description="Current online status")
    last_seen: Optional[datetime] = Field(None, description="Last activity timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Agent-specific settings
    max_concurrent_chats: int = Field(default=5, ge=1, le=20, description="Maximum concurrent conversations")
    auto_assignment_enabled: bool = Field(default=True, description="Automatic chat assignment")
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email_notifications": True,
            "push_notifications": True,
            "sound_notifications": True,
            "desktop_notifications": True
        }
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="User ID who created this user")
    updated_by: Optional[PyObjectId] = Field(None, description="User ID who last updated this user")
    
    # Additional fields for analytics and management
    total_conversations: int = Field(default=0, description="Total conversations handled")
    average_response_time: Optional[float] = Field(None, description="Average response time in seconds")
    customer_satisfaction_rating: Optional[float] = Field(None, ge=0, le=5, description="Average satisfaction rating")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@company.com",
                "phone_number": "+1234567890",
                "department_id": "60a7c8b9f123456789abcdef",
                "status": "active",
                "timezone": "America/New_York",
                "language": "en",
                "max_concurrent_chats": 5,
                "auto_assignment_enabled": True
            }
        }

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, description="Plain text password (will be hashed)")
    role_ids: List[str] = Field(default_factory=list)
    department_id: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    max_concurrent_chats: int = Field(default=5, ge=1, le=20)
    auto_assignment_enabled: bool = True

class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    role_ids: Optional[List[str]] = None
    department_id: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = None
    language: Optional[str] = None
    status: Optional[UserStatus] = None
    max_concurrent_chats: Optional[int] = Field(None, ge=1, le=20)
    auto_assignment_enabled: Optional[bool] = None
    notification_preferences: Optional[Dict[str, bool]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    """Schema for user responses (excludes sensitive data)."""
    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    phone_number: Optional[str]
    role_ids: List[str]
    department_id: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    timezone: str
    language: str
    status: UserStatus
    is_online: bool
    last_seen: Optional[datetime]
    max_concurrent_chats: int
    auto_assignment_enabled: bool
    total_conversations: int
    average_response_time: Optional[float]
    customer_satisfaction_rating: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
