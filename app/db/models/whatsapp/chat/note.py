"""
Note model for the WhatsApp Business Platform.
Handles internal notes and annotations for conversations and other entities.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from app.db.models.base import PyObjectId

class NoteType(str, Enum):
    """Types of notes for different purposes."""
    GENERAL = "general"
    TRANSFER = "transfer"
    ESCALATION = "escalation"
    RESOLUTION = "resolution"
    FOLLOW_UP = "follow_up"
    CUSTOMER_INFO = "customer_info"
    ISSUE = "issue"
    FEEDBACK = "feedback"
    SYSTEM = "system"

class NotePriority(str, Enum):
    """Priority levels for notes."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NoteVisibility(str, Enum):
    """Visibility levels for notes."""
    PRIVATE = "private"        # Only visible to author
    DEPARTMENT = "department"  # Visible to department members
    AGENT = "agent"           # Visible to assigned agents
    PUBLIC = "public"         # Visible to all users

class Note(BaseModel):
    """
    Note model for internal annotations and comments.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core note information
    content: str = Field(..., min_length=1, max_length=5000, description="Note content")
    note_type: NoteType = Field(default=NoteType.GENERAL, description="Type of note")
    priority: NotePriority = Field(default=NotePriority.NORMAL, description="Note priority")
    
    # Author information
    author_id: PyObjectId = Field(..., description="ID of user who created the note")
    author_name: Optional[str] = Field(None, description="Name of the author at time of creation")
    author_role: Optional[str] = Field(None, description="Role of the author at time of creation")
    
    # Target entity
    entity_type: str = Field(..., description="Type of entity this note is attached to")
    entity_id: PyObjectId = Field(..., description="ID of the entity this note is attached to")
    
    # Specific entity references
    conversation_id: Optional[PyObjectId] = Field(None, description="Related conversation ID")
    message_id: Optional[PyObjectId] = Field(None, description="Related message ID")
    customer_phone: Optional[str] = Field(None, description="Related customer phone")
    
    # Visibility and access control
    visibility: NoteVisibility = Field(default=NoteVisibility.DEPARTMENT)
    visible_to_departments: List[PyObjectId] = Field(
        default_factory=list,
        description="Departments that can see this note"
    )
    visible_to_users: List[PyObjectId] = Field(
        default_factory=list,
        description="Specific users who can see this note"
    )
    visible_to_roles: List[PyObjectId] = Field(
        default_factory=list,
        description="Roles that can see this note"
    )
    
    # Note properties
    is_pinned: bool = Field(default=False, description="Whether note is pinned to top")
    is_reminder: bool = Field(default=False, description="Whether note is a reminder")
    reminder_date: Optional[datetime] = Field(None, description="When to remind about this note")
    
    # Categorization
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the note")
    category: Optional[str] = Field(None, description="Note category")
    
    # Rich content
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="File attachments related to the note"
    )
    mentions: List[PyObjectId] = Field(
        default_factory=list,
        description="User IDs mentioned in the note"
    )
    
    # Context and metadata
    context: Dict[str, Any] = Field(
        default_factory=lambda: {
            "conversation_status": None,
            "agent_assigned": None,
            "customer_sentiment": None,
            "related_issues": []
        },
        description="Contextual information at time of note creation"
    )
    
    # Follow-up and tracking
    requires_follow_up: bool = Field(default=False, description="Whether note requires follow-up")
    follow_up_date: Optional[datetime] = Field(None, description="When to follow up")
    follow_up_assigned_to: Optional[PyObjectId] = Field(None, description="User assigned for follow-up")
    
    # Resolution and closure
    is_resolved: bool = Field(default=False, description="Whether note/issue is resolved")
    resolved_at: Optional[datetime] = Field(None, description="When note was resolved")
    resolved_by: Optional[PyObjectId] = Field(None, description="Who resolved the note")
    resolution_details: Optional[str] = Field(None, max_length=1000, description="Resolution details")
    
    # Edit tracking
    is_edited: bool = Field(default=False, description="Whether note has been edited")
    edit_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of edits made to the note"
    )
    last_edited_at: Optional[datetime] = Field(None, description="When note was last edited")
    last_edited_by: Optional[PyObjectId] = Field(None, description="Who last edited the note")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(None, description="Soft deletion timestamp")
    
    # Search and indexing
    searchable_content: Optional[str] = Field(None, description="Processed content for search")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "content": "Customer mentioned they prefer morning calls between 9-11 AM",
                "note_type": "customer_info",
                "priority": "normal",
                "author_id": "60a7c8b9f123456789abcdef",
                "entity_type": "conversation",
                "entity_id": "60a7c8b9f123456789abcdef",
                "visibility": "department",
                "tags": ["customer-preference", "schedule"]
            }
        }

class NoteCreate(BaseModel):
    """Schema for creating a new note."""
    content: str = Field(..., min_length=1, max_length=5000)
    note_type: NoteType = NoteType.GENERAL
    priority: NotePriority = NotePriority.NORMAL
    entity_type: str
    entity_id: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    visibility: NoteVisibility = NoteVisibility.DEPARTMENT
    visible_to_departments: List[str] = Field(default_factory=list)
    visible_to_users: List[str] = Field(default_factory=list)
    visible_to_roles: List[str] = Field(default_factory=list)
    is_pinned: bool = False
    is_reminder: bool = False
    reminder_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    requires_follow_up: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_assigned_to: Optional[str] = None

class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    note_type: Optional[NoteType] = None
    priority: Optional[NotePriority] = None
    visibility: Optional[NoteVisibility] = None
    visible_to_departments: Optional[List[str]] = None
    visible_to_users: Optional[List[str]] = None
    visible_to_roles: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_reminder: Optional[bool] = None
    reminder_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_assigned_to: Optional[str] = None
    is_resolved: Optional[bool] = None
    resolution_details: Optional[str] = Field(None, max_length=1000)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoteResponse(BaseModel):
    """Schema for note responses."""
    id: str = Field(alias="_id")
    content: str
    note_type: NoteType
    priority: NotePriority
    author_id: str
    author_name: Optional[str]
    author_role: Optional[str]
    entity_type: str
    entity_id: str
    conversation_id: Optional[str]
    message_id: Optional[str]
    visibility: NoteVisibility
    is_pinned: bool
    is_reminder: bool
    reminder_date: Optional[datetime]
    tags: List[str]
    category: Optional[str]
    requires_follow_up: bool
    follow_up_date: Optional[datetime]
    follow_up_assigned_to: Optional[str]
    is_resolved: bool
    resolved_at: Optional[datetime]
    is_edited: bool
    last_edited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True 