"""
Authentication schemas for the WhatsApp Business Platform.
Defines request/response models for authentication operations.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema for user login requests."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Extended session duration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "agent@company.com",
                "password": "securepassword123",
                "remember_me": False
            }
        }

class LoginResponse(BaseModel):
    """Schema for successful login responses."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: dict = Field(..., description="User information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "60a7c8b9f123456789abcdef",
                    "email": "agent@company.com",
                    "name": "John Doe"
                }
            }
        }

class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }

class RefreshTokenResponse(BaseModel):
    """Schema for token refresh responses."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        }

class PasswordResetRequest(BaseModel):
    """Schema for password reset requests."""
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@company.com"
            }
        }

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")

class TwoFactorAuthRequest(BaseModel):
    """Schema for two-factor authentication requests."""
    code: str = Field(..., min_length=6, max_length=6, description="2FA code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "123456"
            }
        }

class RegisterRequest(BaseModel):
    """Schema for user registration requests."""
    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    department_id: Optional[str] = Field(None, description="Department ID")
    role_ids: List[str] = Field(default_factory=list, description="Role IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@company.com",
                "password": "securepassword123",
                "phone_number": "+1234567890",
                "department_id": "60a7c8b9f123456789abcdef",
                "role_ids": ["60a7c8b9f123456789abcdef"]
            }
        }

class LogoutRequest(BaseModel):
    """Schema for logout requests."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")

class AuthStatus(BaseModel):
    """Schema for authentication status responses."""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    roles: List[str] = Field(default_factory=list, description="User roles")
    session_expires_at: Optional[datetime] = Field(None, description="Session expiration time")

class ApiKeyRequest(BaseModel):
    """Schema for API key generation requests."""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    permissions: List[str] = Field(default_factory=list, description="API key permissions")

class ApiKeyResponse(BaseModel):
    """Schema for API key responses."""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key: str = Field(..., description="API key value (only shown once)")
    description: Optional[str] = Field(None, description="API key description")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    permissions: List[str] = Field(..., description="API key permissions")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")

class SessionInfo(BaseModel):
    """Schema for session information."""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    is_active: bool = Field(..., description="Whether session is active")
    expires_at: datetime = Field(..., description="Session expiration time") 