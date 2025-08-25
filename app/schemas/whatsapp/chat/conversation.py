"""Conversation-related request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from app.db.models.base import PyObjectId

# Conversation Creation
class ConversationCreate(BaseModel):
    customer_phone: str = Field(..., description="Customer phone number")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_type: str = Field("b2c", pattern="^(b2c|b2b)$", description="Customer type")
    channel: str = Field("whatsapp", description="Communication channel")
    department_id: Optional[PyObjectId] = Field(None, description="Department ID")
    priority: str = Field("normal", pattern="^(low|normal|high|urgent)$", description="Conversation priority")
    tags: List[str] = Field(default=[], description="Initial tags")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

# Conversation Update
class ConversationUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, description="Updated customer name")
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$", description="Updated priority")
    department_id: Optional[PyObjectId] = Field(None, description="Updated department ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

# Conversation Transfer
class ConversationTransfer(BaseModel):
    from_agent_id: Optional[PyObjectId] = Field(None, description="Current agent ID (auto-filled if not provided)")
    to_agent_id: Optional[PyObjectId] = Field(None, description="Target agent ID")
    to_department_id: Optional[PyObjectId] = Field(None, description="Target department ID")
    reason: str = Field(..., min_length=1, max_length=500, description="Transfer reason")
    notes: Optional[str] = Field(None, max_length=1000, description="Transfer notes")

    @validator('to_agent_id', 'to_department_id')
    def validate_transfer_target(cls, v, values):
        if not v and not values.get('to_department_id') and not values.get('to_agent_id'):
            raise ValueError('Either to_agent_id or to_department_id must be provided')
        return v

# Conversation Close
class ConversationClose(BaseModel):
    reason: str = Field(..., description="Close reason")
    resolution: Optional[str] = Field(None, max_length=1000, description="Resolution details")
    customer_satisfied: Optional[bool] = Field(None, description="Customer satisfaction")
    send_survey: bool = Field(True, description="Whether to send survey to customer")
    notes: Optional[str] = Field(None, max_length=1000, description="Closing notes")

# Tag Summary for conversations
class ConversationTagSummary(BaseModel):
    id: str
    name: str
    slug: str
    display_name: Optional[str] = None
    category: str
    color: str
    usage_count: int = 0

# Conversation Response
class ConversationResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    customer_phone: str
    customer_name: Optional[str] = None
    customer_type: str = "individual"
    status: str = "pending"
    priority: str = "normal"
    channel: str = "whatsapp"
    department_id: Optional[PyObjectId] = None
    assigned_agent_id: Optional[PyObjectId] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: List[ConversationTagSummary] = []
    message_count: int = 0
    unread_count: int = 0
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    metadata: Dict[str, Any] = {}
    # Sentiment Analysis
    current_sentiment_emoji: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    last_sentiment_analysis_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Conversation with Details Response
class ConversationDetailResponse(ConversationResponse):
    department_name: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    transfer_history: List[Dict[str, Any]] = []
    recent_messages: List[Dict[str, Any]] = []
    notes_count: int = 0

# Conversation List Response
class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Conversation Query Parameters
class ConversationQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in customer name or phone")
    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    channel: Optional[str] = Field(None, description="Filter by channel")
    department_id: Optional[PyObjectId] = Field(None, description="Filter by department")
    assigned_agent_id: Optional[PyObjectId] = Field(None, description="Filter by assigned agent")
    customer_type: Optional[str] = Field(None, description="Filter by customer type")
    has_unread: Optional[bool] = Field(None, description="Filter by unread messages")
    created_from: Optional[datetime] = Field(None, description="Filter conversations created after this date")
    created_to: Optional[datetime] = Field(None, description="Filter conversations created before this date")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    sort_by: str = Field("last_message_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

# Conversation Assignment
class ConversationAssignment(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    agent_id: PyObjectId = Field(..., description="Agent ID to assign")
    notes: Optional[str] = Field(None, max_length=500, description="Assignment notes")

# Conversation Tag Management
class ConversationTagUpdate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    tags: List[str] = Field(..., description="Updated tags list")

# Conversation Bulk Actions
class ConversationBulkAction(BaseModel):
    conversation_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="List of conversation IDs")
    action: str = Field(..., pattern="^(assign|transfer|close|tag|priority)$", description="Bulk action type")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")

# Conversation Statistics
class ConversationStatsResponse(BaseModel):
    total_conversations: int
    active_conversations: int
    closed_conversations: int
    unassigned_conversations: int
    conversations_by_status: Dict[str, int] = {}
    conversations_by_priority: Dict[str, int] = {}
    conversations_by_channel: Dict[str, int] = {}
    average_response_time_minutes: float = 0.0
    average_resolution_time_minutes: float = 0.0
    customer_satisfaction_rate: float = 0.0

# Conversation Activity
class ConversationActivity(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    activity_type: str = Field(..., description="Activity type")
    description: str = Field(..., description="Activity description")
    metadata: Dict[str, Any] = Field(default={}, description="Activity metadata")

# SLA Status
class ConversationSLAStatus(BaseModel):
    conversation_id: PyObjectId
    response_sla_met: bool
    response_time_minutes: Optional[int]
    response_sla_threshold_minutes: int
    resolution_sla_met: bool
    resolution_time_minutes: Optional[int]
    resolution_sla_threshold_minutes: int
    escalation_required: bool 