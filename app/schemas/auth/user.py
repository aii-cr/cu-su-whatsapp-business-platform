"""User-related request/response schemas."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId
from app.db.models.auth import User

# User Registration
class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    department_id: Optional[PyObjectId] = Field(None, description="Department ID")
    role_ids: Optional[List[PyObjectId]] = Field(default=[], description="List of role IDs")

    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# User Login
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

# User Update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Updated email address")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Updated first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Updated last name")
    phone: Optional[str] = Field(None, description="Updated phone number")
    department_id: Optional[PyObjectId] = Field(None, description="Updated department ID")
    role_ids: Optional[List[PyObjectId]] = Field(None, description="Updated list of role IDs")
    is_active: Optional[bool] = Field(None, description="User active status")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")

# Password Change
class PasswordChange(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    @validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# Password Reset Request
class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address for password reset")

# Password Reset Confirm
class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

    @validator('new_password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

# User Response
class UserResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    department_id: Optional[PyObjectId] = None
    role_ids: List[PyObjectId] = []
    is_active: bool
    status: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    preferences: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# User List Response
class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int

# User Profile Response (includes sensitive fields for self)
class UserProfileResponse(UserResponse):
    permissions: List[str] = []
    department_name: Optional[str] = None
    role_names: List[str] = []

# Token Response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# Token Refresh
class TokenRefresh(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

# User Query Parameters
class UserQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in name or email")
    department_id: Optional[PyObjectId] = Field(None, description="Filter by department")
    role_id: Optional[PyObjectId] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    status: Optional[str] = Field(None, description="Filter by user status")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

# User Statistics
class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    users_by_department: Dict[str, int]
    users_by_role: Dict[str, int]
    recent_logins: int  # Last 24 hours 