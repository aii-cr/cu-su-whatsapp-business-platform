"""Enhanced tag model for conversation categorization."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
from app.db.models.base import PyObjectId


def generate_slug(name: str) -> str:
    """Generate slug from tag name."""
    import re
    # Convert to lowercase, replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


class Tag(BaseModel):
    """Enhanced tag model to match frontend expectations."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="URL-friendly slug")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Tag description")
    category: str = Field(default="general", description="Tag category")
    color: str = Field(default="#2563eb", description="Hex color")
    parent_tag_id: Optional[PyObjectId] = Field(None, description="Parent tag ID")
    child_tags: List[PyObjectId] = Field(default=[], description="Child tag IDs")
    status: str = Field(default="active", description="Tag status")
    is_system_tag: bool = Field(default=False, description="Is system tag")
    is_auto_assignable: bool = Field(default=True, description="Can be auto-assigned")
    usage_count: int = Field(default=0, description="How many times used")
    department_ids: List[PyObjectId] = Field(default=[], description="Department IDs")
    user_ids: List[PyObjectId] = Field(default=[], description="User IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="Creator user ID")
    updated_by: Optional[PyObjectId] = Field(None, description="Updater user ID")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

    def __init__(self, **data):
        # Auto-generate slug if not provided
        if 'slug' not in data and 'name' in data:
            data['slug'] = generate_slug(data['name'])
        # Set display_name to name if not provided
        if 'display_name' not in data and 'name' in data:
            data['display_name'] = data['name']
        super().__init__(**data)


class ConversationTag(BaseModel):
    """Association between conversation and tag."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    tag_id: PyObjectId = Field(..., description="Tag ID")
    tag_name: str = Field(..., description="Tag name for quick access")
    tag_slug: str = Field(..., description="Tag slug for quick access")
    tag_color: str = Field(..., description="Tag color for quick access")
    tag_category: str = Field(default="general", description="Tag category for quick access")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[PyObjectId] = Field(None, description="User who assigned")
    auto_assigned: bool = Field(default=False, description="Was auto-assigned")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
