"""Tag schemas following frontend model expectations."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Tag status and category enums to match frontend
class TagStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"


class TagCategory:
    GENERAL = "general"
    DEPARTMENT = "department"  
    PRIORITY = "priority"
    CUSTOMER_TYPE = "customer_type"
    ISSUE_TYPE = "issue_type"
    PRODUCT = "product"
    STATUS = "status"
    CUSTOM = "custom"


# REQUEST SCHEMAS
class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=40, description="Tag name")
    color: str = Field(default="#2563eb", description="Hex color code")
    category: str = Field(default=TagCategory.GENERAL, description="Tag category")
    description: Optional[str] = Field(None, description="Tag description")


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=40, description="Tag name")
    color: Optional[str] = Field(None, description="Hex color code")
    category: Optional[str] = Field(None, description="Tag category")
    description: Optional[str] = Field(None, description="Tag description")
    status: Optional[str] = Field(None, description="Tag status")


class TagAssign(BaseModel):
    """Schema for assigning tags to conversation."""
    tag_ids: List[str] = Field(..., min_items=1, description="Tag IDs to assign")
    auto_assigned: bool = Field(default=False, description="Whether tags were auto-assigned")


class TagUnassign(BaseModel):
    """Schema for unassigning tags from conversation."""
    tag_ids: List[str] = Field(..., min_items=1, description="Tag IDs to unassign")


class TagListRequest(BaseModel):
    """Schema for listing tags with filters."""
    limit: int = Field(default=20, ge=1, le=100, description="Number of tags to return")
    offset: int = Field(default=0, ge=0, description="Number of tags to skip")
    search: Optional[str] = Field(None, description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    status: str = Field(default=TagStatus.ACTIVE, description="Filter by status")
    sort_by: str = Field(default="usage_count", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")


class TagSuggestRequest(BaseModel):
    """Schema for tag suggestions/autocomplete."""
    query: str = Field("", description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Number of suggestions")
    category: Optional[str] = Field(None, description="Filter by category")
    exclude_ids: Optional[List[str]] = Field(default=[], description="Tag IDs to exclude")


# RESPONSE SCHEMAS  
class TagSummary(BaseModel):
    """Schema for tag summary (lightweight)."""
    id: str = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="Tag slug")
    display_name: Optional[str] = Field(None, description="Display name")
    category: str = Field(..., description="Tag category")
    color: str = Field(..., description="Tag color")
    usage_count: int = Field(..., description="Usage count")


class TagResponse(BaseModel):
    """Schema for full tag response."""
    id: str = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    slug: str = Field(..., description="Tag slug")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Tag description")
    category: str = Field(..., description="Tag category")
    color: str = Field(..., description="Tag color")
    parent_tag_id: Optional[str] = Field(None, description="Parent tag ID")
    child_tags: List[str] = Field(default=[], description="Child tag IDs")
    status: str = Field(..., description="Tag status")
    is_system_tag: bool = Field(..., description="Is system tag")
    is_auto_assignable: bool = Field(..., description="Can be auto-assigned")
    usage_count: int = Field(..., description="Usage count")
    department_ids: List[str] = Field(default=[], description="Department IDs")
    user_ids: List[str] = Field(default=[], description="User IDs")
    created_at: str = Field(..., description="Created timestamp")
    updated_at: str = Field(..., description="Updated timestamp") 
    created_by: Optional[str] = Field(None, description="Creator ID")
    updated_by: Optional[str] = Field(None, description="Updater ID")


class TagListResponse(BaseModel):
    """Schema for tag list response."""
    tags: List[TagResponse] = Field(..., description="List of tags")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Request limit")
    offset: int = Field(..., description="Request offset")
    has_more: bool = Field(..., description="Has more results")


class TagSuggestResponse(BaseModel):
    """Schema for tag suggestions response."""
    suggestions: List[TagSummary] = Field(..., description="Tag suggestions")
    total: int = Field(..., description="Total matches")


class TagSearchResponse(BaseModel):
    """Schema for tag search response."""
    tags: List[TagResponse] = Field(..., description="Found tags")
    total: int = Field(..., description="Total count")


# CONVERSATION TAG SCHEMAS
class ConversationTag(BaseModel):
    """Schema for conversation tag (matches frontend expectations)."""
    tag: TagSummary = Field(..., description="Tag information")
    assigned_at: str = Field(..., description="Assignment timestamp")
    assigned_by: Optional[str] = Field(None, description="User who assigned")
    auto_assigned: bool = Field(default=False, description="Was auto-assigned")


class ConversationTagResponse(BaseModel):
    """Schema for conversation tag response (legacy, for backward compatibility)."""
    id: str = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name") 
    color: str = Field(..., description="Tag color")
    assigned_at: datetime = Field(..., description="Assignment timestamp")


class TagOperationResponse(BaseModel):
    """Schema for tag operations response."""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Response message") 
    tags: List[ConversationTag] = Field(default=[], description="Updated tags")


class TagUnassignResponse(BaseModel):
    """Schema for tag unassign response (matches frontend expectations)."""
    message: str = Field(..., description="Response message")
    unassigned_count: int = Field(..., description="Number of tags unassigned")


class TagSettingsResponse(BaseModel):
    """Schema for tag settings response."""
    max_tags_per_conversation: int = Field(default=10, description="Max tags per conversation")
