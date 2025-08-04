"""Note-related request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

# Note Creation
class NoteCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Associated conversation ID")
    content: str = Field(..., min_length=1, max_length=2000, description="Note content")
    type: str = Field("general", pattern="^(general|follow_up|escalation|resolution|customer_info)$", description="Note type")
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$", description="Note priority")
    visibility: str = Field("team", pattern="^(private|team|department|public)$", description="Note visibility")
    tags: List[str] = Field(default=[], description="Note tags")
    reminder_at: Optional[datetime] = Field(None, description="Reminder datetime")
    attachments: List[PyObjectId] = Field(default=[], description="Attached media IDs")

# Note Update
class NoteUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="Updated note content")
    type: Optional[str] = Field(None, pattern="^(general|follow_up|escalation|resolution|customer_info)$", description="Updated note type")
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$", description="Updated note priority")
    visibility: Optional[str] = Field(None, pattern="^(private|team|department|public)$", description="Updated note visibility")
    tags: Optional[List[str]] = Field(None, description="Updated note tags")
    reminder_at: Optional[datetime] = Field(None, description="Updated reminder datetime")
    attachments: Optional[List[PyObjectId]] = Field(None, description="Updated attached media IDs")

# Note Response
class NoteResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    conversation_id: PyObjectId
    author_id: PyObjectId
    content: str
    type: str
    priority: str
    visibility: str
    tags: List[str] = []
    reminder_at: Optional[datetime] = None
    reminder_sent: bool = False
    attachments: List[PyObjectId] = []
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Note with Author Response
class NoteDetailResponse(NoteResponse):
    author_name: str
    author_email: str
    conversation_customer_name: Optional[str] = None
    conversation_customer_phone: str
    attachment_details: List[Dict[str, Any]] = []

# Note List Response
class NoteListResponse(BaseModel):
    notes: List[NoteResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Note Query Parameters
class NoteQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    conversation_id: Optional[PyObjectId] = Field(None, description="Filter by conversation")
    author_id: Optional[PyObjectId] = Field(None, description="Filter by author")
    type: Optional[str] = Field(None, description="Filter by note type")
    priority: Optional[str] = Field(None, description="Filter by priority")
    visibility: Optional[str] = Field(None, description="Filter by visibility")
    has_reminder: Optional[bool] = Field(None, description="Filter notes with reminders")
    reminder_due: Optional[bool] = Field(None, description="Filter overdue reminders")
    is_pinned: Optional[bool] = Field(None, description="Filter pinned notes")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    from_date: Optional[datetime] = Field(None, description="Filter notes from this date")
    to_date: Optional[datetime] = Field(None, description="Filter notes to this date")
    search: Optional[str] = Field(None, description="Search in note content")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

# Note Pin/Unpin
class NotePinToggle(BaseModel):
    note_id: PyObjectId = Field(..., description="Note ID to pin/unpin")
    is_pinned: bool = Field(..., description="Pin status")

# Bulk Note Operations
class BulkNoteDelete(BaseModel):
    note_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="Note IDs to delete")

class BulkNoteTagUpdate(BaseModel):
    note_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="Note IDs to update")
    tags: List[str] = Field(..., description="Tags to apply")
    action: str = Field("replace", pattern="^(replace|add|remove)$", description="Tag action")

# Note Template
class NoteTemplate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    content: str = Field(..., min_length=1, max_length=2000, description="Template content")
    type: str = Field("general", description="Default note type")
    priority: str = Field("normal", description="Default priority")
    visibility: str = Field("team", description="Default visibility")
    tags: List[str] = Field(default=[], description="Default tags")
    variables: List[str] = Field(default=[], description="Template variables")

# Note Statistics
class NoteStatsResponse(BaseModel):
    total_notes: int
    notes_by_type: Dict[str, int]
    notes_by_priority: Dict[str, int]
    notes_by_visibility: Dict[str, int]
    notes_with_reminders: int
    overdue_reminders: int
    pinned_notes: int
    most_active_authors: List[Dict[str, Any]]

# Note Reminder
class NoteReminder(BaseModel):
    note_id: PyObjectId
    recipient_id: PyObjectId
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed

# Note Activity
class NoteActivity(BaseModel):
    note_id: PyObjectId
    activity_type: str  # created, updated, deleted, pinned, unpinned
    actor_id: PyObjectId
    actor_name: str
    timestamp: datetime
    details: Dict[str, Any] = {}

# Note Export Request
class NoteExportRequest(BaseModel):
    conversation_ids: Optional[List[PyObjectId]] = Field(None, description="Filter by conversations")
    author_ids: Optional[List[PyObjectId]] = Field(None, description="Filter by authors")
    from_date: Optional[datetime] = Field(None, description="Export notes from this date")
    to_date: Optional[datetime] = Field(None, description="Export notes to this date")
    include_attachments: bool = Field(False, description="Include attachment details")
    format: str = Field("csv", pattern="^(csv|json|xlsx)$", description="Export format") 