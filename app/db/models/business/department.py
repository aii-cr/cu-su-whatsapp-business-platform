"""
Department model for the WhatsApp Business Platform.
Represents organizational departments for user management and chat routing.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum
from app.db.models.base import PyObjectId

class DepartmentStatus(str, Enum):
    """Department status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class Department(BaseModel):
    """
    Department model for organizing users and managing routing.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100, description="Department name (unique)")
    display_name: str = Field(..., min_length=1, max_length=100, description="Human-readable department name")
    description: Optional[str] = Field(None, max_length=500, description="Department description")
    
    # Department settings
    status: DepartmentStatus = Field(default=DepartmentStatus.ACTIVE)
    is_default: bool = Field(default=False, description="Whether this is the default department")
    
    # Contact and routing information
    email: Optional[str] = Field(None, description="Department contact email")
    phone: Optional[str] = Field(None, description="Department contact phone")
    manager_id: Optional[PyObjectId] = Field(None, description="Department manager user ID")
    
    # Operational settings
    business_hours: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timezone": "UTC",
            "monday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "tuesday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "wednesday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "thursday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "friday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "saturday": {"enabled": False, "start": "09:00", "end": "17:00"},
            "sunday": {"enabled": False, "start": "09:00", "end": "17:00"}
        },
        description="Department business hours"
    )
    
    # Chat routing and management settings
    routing_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "auto_assignment": True,
            "round_robin": True,
            "max_queue_size": 100,
            "priority_level": 1,
            "escalation_timeout_minutes": 30,
            "require_agent_acceptance": False
        },
        description="Chat routing configuration"
    )
    
    # Service level agreement settings
    sla_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "first_response_minutes": 5,
            "resolution_hours": 24,
            "escalation_hours": 4,
            "inactivity_timeout_hours": 12
        },
        description="Service level agreement settings"
    )
    
    # WhatsApp specific settings
    whatsapp_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "phone_number_id": None,
            "business_account_id": None,
            "welcome_message": "Hello! How can we help you today?",
            "auto_responses_enabled": True,
            "template_namespace": None
        },
        description="WhatsApp Business API settings"
    )
    
    # Tags and categorization
    tags: List[str] = Field(default_factory=list, description="Department tags for categorization")
    
    # Metrics and analytics
    metrics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "total_conversations": 0,
            "active_conversations": 0,
            "average_response_time": 0,
            "satisfaction_rating": 0,
            "resolution_rate": 0
        },
        description="Department performance metrics"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="User ID who created this department")
    updated_by: Optional[PyObjectId] = Field(None, description="User ID who last updated this department")
    
    # Relationships
    user_count: int = Field(default=0, description="Number of users in this department")
    active_user_count: int = Field(default=0, description="Number of active users in this department")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        schema_extra = {
            "example": {
                "name": "customer_service",
                "display_name": "Customer Service",
                "description": "Main customer service department handling general inquiries",
                "email": "support@company.com",
                "phone": "+1234567890",
                "status": "active",
                "is_default": True,
                "business_hours": {
                    "timezone": "America/New_York",
                    "monday": {"enabled": True, "start": "09:00", "end": "17:00"}
                },
                "sla_settings": {
                    "first_response_minutes": 5,
                    "resolution_hours": 24
                }
            }
        }

class DepartmentCreate(BaseModel):
    """Schema for creating a new department."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = None
    phone: Optional[str] = None
    manager_id: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    routing_settings: Optional[Dict[str, Any]] = None
    sla_settings: Optional[Dict[str, Any]] = None
    whatsapp_settings: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)

class DepartmentUpdate(BaseModel):
    """Schema for updating an existing department."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = None
    phone: Optional[str] = None
    manager_id: Optional[str] = None
    status: Optional[DepartmentStatus] = None
    is_default: Optional[bool] = None
    business_hours: Optional[Dict[str, Any]] = None
    routing_settings: Optional[Dict[str, Any]] = None
    sla_settings: Optional[Dict[str, Any]] = None
    whatsapp_settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DepartmentResponse(BaseModel):
    """Schema for department responses."""
    id: str = Field(alias="_id")
    name: str
    display_name: str
    description: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    manager_id: Optional[str]
    status: DepartmentStatus
    is_default: bool
    business_hours: Dict[str, Any]
    routing_settings: Dict[str, Any]
    sla_settings: Dict[str, Any]
    whatsapp_settings: Dict[str, Any]
    tags: List[str]
    metrics: Dict[str, Any]
    user_count: int
    active_user_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True 