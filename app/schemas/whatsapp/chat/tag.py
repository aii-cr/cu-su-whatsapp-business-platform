"""
Tag schemas for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models.whatsapp.chat.tag import TagCategory, TagColor, TagStatus
import re
import unicodedata


class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=40, description="Tag name")
    display_name: Optional[str] = Field(None, max_length=60, description="Display name for UI")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")
    category: TagCategory = Field(default=TagCategory.GENERAL, description="Tag category")
    color: TagColor = Field(default=TagColor.BLUE, description="Tag color")
    parent_tag_id: Optional[str] = Field(None, description="Parent tag ID for hierarchy")
    department_ids: List[str] = Field(default_factory=list, description="Allowed department IDs")
    user_ids: List[str] = Field(default_factory=list, description="Allowed user IDs")
    is_auto_assignable: bool = Field(default=True, description="Can be auto-assigned")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and clean tag name."""
        if not v or not v.strip():
            raise ValueError("Tag name cannot be empty")
        
        cleaned = v.strip()
        
        # Allow letters, numbers, spaces, hyphens, underscores, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()]+$', cleaned):
            raise ValueError("Tag name contains invalid characters. Only letters, numbers, spaces, hyphens, underscores, and basic punctuation are allowed.")
        
        return cleaned
    
    @validator('display_name')
    def validate_display_name(cls, v):
        """Validate display name."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=40, description="Tag name")
    display_name: Optional[str] = Field(None, max_length=60, description="Display name for UI")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")
    category: Optional[TagCategory] = Field(None, description="Tag category")
    color: Optional[TagColor] = Field(None, description="Tag color")
    parent_tag_id: Optional[str] = Field(None, description="Parent tag ID for hierarchy")
    department_ids: Optional[List[str]] = Field(None, description="Allowed department IDs")
    user_ids: Optional[List[str]] = Field(None, description="Allowed user IDs")
    is_auto_assignable: Optional[bool] = Field(None, description="Can be auto-assigned")
    status: Optional[TagStatus] = Field(None, description="Tag status")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate tag name."""
        if v is not None:
            if not v.strip():
                raise ValueError("Tag name cannot be empty")
            
            cleaned = v.strip()
            if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()]+$', cleaned):
                raise ValueError("Tag name contains invalid characters")
            
            return cleaned
        return v


class TagResponse(BaseModel):
    """Schema for tag responses."""
    id: str = Field(alias="_id", description="Tag ID")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="URL-safe slug")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Tag description")
    category: TagCategory = Field(..., description="Tag category")
    color: TagColor = Field(..., description="Tag color")
    parent_tag_id: Optional[str] = Field(None, description="Parent tag ID")
    child_tags: List[str] = Field(default_factory=list, description="Child tag IDs")
    status: TagStatus = Field(..., description="Tag status")
    is_system_tag: bool = Field(..., description="Is system tag")
    is_auto_assignable: bool = Field(..., description="Can be auto-assigned")
    usage_count: int = Field(..., description="Usage count")
    department_ids: List[str] = Field(default_factory=list, description="Allowed departments")
    user_ids: List[str] = Field(default_factory=list, description="Allowed users")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    
    class Config:
        populate_by_name = True


class TagSummaryResponse(BaseModel):
    """Lightweight tag response for autocomplete and lists."""
    id: str = Field(alias="_id", description="Tag ID")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="URL-safe slug")
    display_name: Optional[str] = Field(None, description="Display name")
    category: TagCategory = Field(..., description="Tag category")
    color: TagColor = Field(..., description="Tag color")
    usage_count: int = Field(..., description="Usage count")
    
    class Config:
        populate_by_name = True


class TagSuggestRequest(BaseModel):
    """Schema for tag suggestion requests."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    category: Optional[TagCategory] = Field(None, description="Filter by category")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    exclude_ids: List[str] = Field(default_factory=list, description="Tag IDs to exclude")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query."""
        return v.strip()


class TagSuggestResponse(BaseModel):
    """Schema for tag suggestion responses."""
    tags: List[TagSummaryResponse] = Field(..., description="Suggested tags")
    total: int = Field(..., description="Total available results")
    query: str = Field(..., description="Original query")


class ConversationTagAssignRequest(BaseModel):
    """Schema for assigning tags to conversations."""
    tag_ids: List[str] = Field(..., min_items=1, description="Tag IDs to assign")
    auto_assigned: bool = Field(default=False, description="Whether tags were auto-assigned")
    confidence_scores: Optional[Dict[str, float]] = Field(
        None, 
        description="Confidence scores for auto-assigned tags (tag_id -> score)"
    )
    
    @validator('confidence_scores')
    def validate_confidence_scores(cls, v, values):
        """Validate confidence scores."""
        if v is not None and 'tag_ids' in values:
            for tag_id in values['tag_ids']:
                if tag_id in v:
                    score = v[tag_id]
                    if not (0.0 <= score <= 1.0):
                        raise ValueError(f"Confidence score for tag {tag_id} must be between 0.0 and 1.0")
        return v


class ConversationTagUnassignRequest(BaseModel):
    """Schema for unassigning tags from conversations."""
    tag_ids: List[str] = Field(..., min_items=1, description="Tag IDs to unassign")


class ConversationTagResponse(BaseModel):
    """Schema for conversation tag assignment responses."""
    conversation_id: str = Field(..., description="Conversation ID")
    tag: TagSummaryResponse = Field(..., description="Tag data")
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    assigned_by: Optional[str] = Field(None, description="User who assigned the tag")
    auto_assigned: bool = Field(..., description="Whether auto-assigned")
    confidence_score: Optional[float] = Field(None, description="Auto-assignment confidence")
    
    class Config:
        populate_by_name = True


class TagListRequest(BaseModel):
    """Schema for tag listing requests."""
    category: Optional[TagCategory] = Field(None, description="Filter by category")
    status: Optional[TagStatus] = Field(None, description="Filter by status")
    department_id: Optional[str] = Field(None, description="Filter by department access")
    search: Optional[str] = Field(None, max_length=100, description="Search query")
    parent_tag_id: Optional[str] = Field(None, description="Filter by parent tag")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")
    sort_by: str = Field(default="name", description="Sort field")
    sort_order: str = Field(default="asc", description="Sort order (asc/desc)")
    
    @validator('search')
    def validate_search(cls, v):
        """Validate search query."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort field."""
        allowed_fields = ['name', 'category', 'usage_count', 'created_at', 'updated_at']
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Must be one of: {', '.join(allowed_fields)}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()


class TagListResponse(BaseModel):
    """Schema for tag listing responses."""
    tags: List[TagResponse] = Field(..., description="Tag list")
    total: int = Field(..., description="Total available results")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
    has_more: bool = Field(..., description="Whether more results are available")


def generate_slug(name: str) -> str:
    """Generate URL-safe slug from tag name."""
    # Normalize unicode characters
    normalized = unicodedata.normalize('NFKD', name.lower())
    
    # Convert to ASCII, removing accents
    ascii_str = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9\-_]', '-', ascii_str)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure minimum length
    if not slug:
        slug = "tag"
    
    return slug