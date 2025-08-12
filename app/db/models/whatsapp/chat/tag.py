"""
Tag model for the WhatsApp Business Platform.
Represents conversation tags with categories and hierarchical structure.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum
from app.db.models.base import PyObjectId
import re


class TagStatus(str, Enum):
    """Tag status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class TagCategory(str, Enum):
    """Predefined tag categories."""
    GENERAL = "general"
    DEPARTMENT = "department"
    PRIORITY = "priority"
    CUSTOMER_TYPE = "customer_type"
    ISSUE_TYPE = "issue_type"
    PRODUCT = "product"
    STATUS = "status"
    CUSTOM = "custom"


class TagColor(str, Enum):
    """Predefined tag colors."""
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    PURPLE = "purple"
    PINK = "pink"
    ORANGE = "orange"
    GRAY = "gray"
    INDIGO = "indigo"
    TEAL = "teal"


class Tag(BaseModel):
    """
    Tag model for categorizing and organizing conversations.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core identification
    name: str = Field(..., min_length=1, max_length=40, description="Tag name")
    slug: str = Field(..., description="URL-safe slug generated from name")
    display_name: Optional[str] = Field(None, max_length=60, description="Display name for UI")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")
    
    # Categorization
    category: TagCategory = Field(default=TagCategory.GENERAL, description="Tag category")
    color: TagColor = Field(default=TagColor.BLUE, description="Tag color for UI")
    
    # Hierarchy
    parent_tag_id: Optional[PyObjectId] = Field(None, description="Parent tag for hierarchical structure")
    child_tags: List[PyObjectId] = Field(default_factory=list, description="Child tag IDs")
    
    # Settings
    status: TagStatus = Field(default=TagStatus.ACTIVE, description="Tag status")
    is_system_tag: bool = Field(default=False, description="Whether this is a system-defined tag")
    is_auto_assignable: bool = Field(default=True, description="Whether tag can be auto-assigned")
    usage_count: int = Field(default=0, description="Number of times tag has been used")
    
    # Permissions and scope
    department_ids: List[PyObjectId] = Field(
        default_factory=list, 
        description="Department IDs that can use this tag (empty = all departments)"
    )
    user_ids: List[PyObjectId] = Field(
        default_factory=list,
        description="Specific user IDs that can use this tag (empty = all users)"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="User who created the tag")
    updated_by: Optional[PyObjectId] = Field(None, description="User who last updated the tag")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate tag name."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        
        # Allow letters, numbers, spaces, hyphens, underscores, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()]+$', v.strip()):
            raise ValueError("Tag name contains invalid characters")
        
        return v.strip()
    
    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        if not re.match(r'^[a-z0-9\-_]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, hyphens, and underscores")
        return v
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Sales Inquiry",
                "slug": "sales-inquiry",
                "category": "issue_type",
                "color": "blue",
                "description": "Customer inquiries about products or services"
            }
        }


class TagDenormalized(BaseModel):
    """
    Denormalized tag data stored in conversations for performance.
    This is what gets embedded in conversation documents.
    """
    id: PyObjectId = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="Tag slug")
    category: TagCategory = Field(..., description="Tag category")
    color: TagColor = Field(..., description="Tag color")
    display_name: Optional[str] = Field(None, description="Display name")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class ConversationTag(BaseModel):
    """
    Association between conversation and tag with additional metadata.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    tag: TagDenormalized = Field(..., description="Denormalized tag data")
    
    # Assignment metadata
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[PyObjectId] = Field(None, description="User who assigned the tag")
    auto_assigned: bool = Field(default=False, description="Whether tag was auto-assigned")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Auto-assignment confidence")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}