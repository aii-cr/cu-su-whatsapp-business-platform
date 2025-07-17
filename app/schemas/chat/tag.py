"""Tag-related request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

# Tag Creation
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    category: str = Field(..., description="Tag category")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")
    color: str = Field("#007bff", pattern="^#[0-9A-Fa-f]{6}$", description="Tag color hex code")
    is_system_tag: bool = Field(False, description="Whether this is a system tag")
    auto_assign_rules: List[Dict[str, Any]] = Field(default=[], description="Auto-assignment rules")
    scope: str = Field("conversation", pattern="^(conversation|message|global)$", description="Tag scope")

# Tag Update
class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Updated tag name")
    category: Optional[str] = Field(None, description="Updated tag category")
    description: Optional[str] = Field(None, max_length=200, description="Updated tag description")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Updated tag color")
    auto_assign_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Updated auto-assignment rules")
    is_active: Optional[bool] = Field(None, description="Updated active status")

# Tag Response
class TagResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    category: str
    description: Optional[str] = None
    color: str
    is_system_tag: bool
    is_active: bool
    scope: str
    auto_assign_rules: List[Dict[str, Any]] = []
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Tag List Response
class TagListResponse(BaseModel):
    tags: List[TagResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Grouped Tags Response
class GroupedTagsResponse(BaseModel):
    categories: Dict[str, List[TagResponse]]
    total: int

# Tag Query Parameters
class TagQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in tag name or description")
    category: Optional[str] = Field(None, description="Filter by category")
    scope: Optional[str] = Field(None, description="Filter by scope")
    is_system_tag: Optional[bool] = Field(None, description="Filter by system tag status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    group_by_category: bool = Field(False, description="Group tags by category")
    sort_by: str = Field("name", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

# Tag Assignment
class TagAssignment(BaseModel):
    tag_ids: List[PyObjectId] = Field(..., min_items=1, description="Tag IDs to assign")
    target_type: str = Field(..., pattern="^(conversation|message)$", description="Target type")
    target_id: PyObjectId = Field(..., description="Target ID")
    assigned_by: str = Field("manual", pattern="^(manual|auto|system)$", description="Assignment method")
    notes: Optional[str] = Field(None, max_length=500, description="Assignment notes")

# Tag Removal
class TagRemoval(BaseModel):
    tag_ids: List[PyObjectId] = Field(..., min_items=1, description="Tag IDs to remove")
    target_type: str = Field(..., pattern="^(conversation|message)$", description="Target type")
    target_id: PyObjectId = Field(..., description="Target ID")

# Bulk Tag Assignment
class BulkTagAssignment(BaseModel):
    tag_ids: List[PyObjectId] = Field(..., min_items=1, description="Tag IDs to assign")
    target_type: str = Field(..., pattern="^(conversation|message)$", description="Target type")
    target_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="Target IDs")
    assigned_by: str = Field("manual", pattern="^(manual|auto|system)$", description="Assignment method")

# Tag Statistics
class TagStatsResponse(BaseModel):
    total_tags: int
    active_tags: int
    system_tags: int
    tags_by_category: Dict[str, int]
    tags_by_scope: Dict[str, int]
    most_used_tags: List[Dict[str, Any]]
    least_used_tags: List[Dict[str, Any]]

# Tag Usage Analytics
class TagUsageAnalytics(BaseModel):
    tag_id: PyObjectId
    tag_name: str
    usage_over_time: List[Dict[str, Any]]  # Daily/weekly usage counts
    usage_by_department: Dict[str, int]
    usage_by_agent: Dict[str, int]
    auto_assignments_count: int
    manual_assignments_count: int

# Tag Auto-Assignment Rule
class TagAutoAssignRule(BaseModel):
    tag_id: PyObjectId = Field(..., description="Tag to auto-assign")
    conditions: List[Dict[str, Any]] = Field(..., description="Conditions for auto-assignment")
    priority: int = Field(1, ge=1, le=10, description="Rule priority")
    is_active: bool = Field(True, description="Whether rule is active")

# Tag Export Request
class TagExportRequest(BaseModel):
    tag_ids: Optional[List[PyObjectId]] = Field(None, description="Specific tags to export")
    include_usage_data: bool = Field(False, description="Include usage statistics")
    format: str = Field("csv", pattern="^(csv|json|xlsx)$", description="Export format") 