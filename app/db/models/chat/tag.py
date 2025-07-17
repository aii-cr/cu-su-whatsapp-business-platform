"""
Tag model for the WhatsApp Business Platform.
Provides flexible labeling system for conversations, messages, and other entities.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.db.models.base import PyObjectId

class TagType(str, Enum):
    """Types of tags for different use cases."""
    GENERAL = "general"
    PRIORITY = "priority"
    CATEGORY = "category"
    STATUS = "status"
    DEPARTMENT = "department"
    PRODUCT = "product"
    ISSUE = "issue"
    SENTIMENT = "sentiment"
    CUSTOM = "custom"

class TagScope(str, Enum):
    """Scope of tag application."""
    CONVERSATION = "conversation"
    MESSAGE = "message"
    USER = "user"
    DEPARTMENT = "department"
    GLOBAL = "global"

class Tag(BaseModel):
    """
    Tag model for flexible labeling and categorization.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core tag information
    name: str = Field(..., min_length=1, max_length=50, description="Tag name (unique within scope)")
    display_name: str = Field(..., min_length=1, max_length=100, description="Human-readable tag name")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")
    
    # Tag categorization
    tag_type: TagType = Field(default=TagType.GENERAL, description="Type of tag")
    scope: TagScope = Field(default=TagScope.CONVERSATION, description="Scope where tag can be applied")
    
    # Visual properties
    color: str = Field(default="#6B7280", description="Tag display color (hex code)")
    icon: Optional[str] = Field(None, description="Icon identifier for the tag")
    
    # Hierarchy and relationships
    parent_tag_id: Optional[PyObjectId] = Field(None, description="Parent tag for hierarchical structure")
    child_tags: List[PyObjectId] = Field(default_factory=list, description="Child tag IDs")
    
    # Configuration
    is_system_tag: bool = Field(default=False, description="Whether this is a system-defined tag")
    is_active: bool = Field(default=True, description="Whether tag is active and can be used")
    is_required: bool = Field(default=False, description="Whether tag assignment is required in scope")
    
    # Access control
    department_ids: List[PyObjectId] = Field(
        default_factory=list, 
        description="Departments that can use this tag (empty = all)"
    )
    role_ids: List[PyObjectId] = Field(
        default_factory=list, 
        description="Roles that can use this tag (empty = all)"
    )
    
    # Automation and rules
    auto_assignment_rules: Dict[str, Any] = Field(
        default_factory=lambda: {
            "keywords": [],
            "conditions": [],
            "enabled": False
        },
        description="Rules for automatic tag assignment"
    )
    
    # Analytics and insights
    analytics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "usage_count": 0,
            "last_used": None,
            "trending_score": 0,
            "sentiment_impact": None
        },
        description="Tag usage analytics"
    )
    
    # Lifecycle management
    expires_at: Optional[datetime] = Field(None, description="Tag expiration date")
    archived_at: Optional[datetime] = Field(None, description="Tag archival date")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="User who created this tag")
    updated_by: Optional[PyObjectId] = Field(None, description="User who last updated this tag")
    
    # Additional properties
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom properties"
    )
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        schema_extra = {
            "example": {
                "name": "urgent",
                "display_name": "Urgent",
                "description": "High priority conversations requiring immediate attention",
                "tag_type": "priority",
                "scope": "conversation",
                "color": "#EF4444",
                "is_system_tag": True
            }
        }

class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tag_type: TagType = TagType.GENERAL
    scope: TagScope = TagScope.CONVERSATION
    color: str = "#6B7280"
    icon: Optional[str] = None
    parent_tag_id: Optional[str] = None
    department_ids: List[str] = Field(default_factory=list)
    role_ids: List[str] = Field(default_factory=list)
    auto_assignment_rules: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None

class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    is_required: Optional[bool] = None
    department_ids: Optional[List[str]] = None
    role_ids: Optional[List[str]] = None
    auto_assignment_rules: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TagAssignment(BaseModel):
    """Schema for assigning tags to entities."""
    tag_id: str
    entity_type: str  # conversation, message, user, etc.
    entity_id: str
    assigned_by: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    auto_assigned: bool = False

class TagResponse(BaseModel):
    """Schema for tag responses."""
    id: str = Field(alias="_id")
    name: str
    display_name: str
    description: Optional[str]
    tag_type: TagType
    scope: TagScope
    color: str
    icon: Optional[str]
    parent_tag_id: Optional[str]
    is_system_tag: bool
    is_active: bool
    is_required: bool
    department_ids: List[str]
    role_ids: List[str]
    analytics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True 