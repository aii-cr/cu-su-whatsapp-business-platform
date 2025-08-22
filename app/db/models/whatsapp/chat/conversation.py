"""
Conversation model for the WhatsApp Business Platform.
Represents chat conversations between customers and agents.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from enum import Enum
from app.db.models.base import PyObjectId

class ConversationStatus(str, Enum):
    """Conversation status options."""
    PENDING = "pending"  # Waiting for agent assignment
    ACTIVE = "active"    # Currently being handled
    WAITING = "waiting"  # Waiting for customer response
    RESOLVED = "resolved" # Closed/resolved
    TRANSFERRED = "transferred" # Being transferred
    ESCALATED = "escalated" # Escalated to supervisor

class ConversationPriority(str, Enum):
    """Conversation priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ConversationChannel(str, Enum):
    """Communication channel types."""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    FACEBOOK_MESSENGER = "facebook_messenger"
    WEB_CHAT = "web_chat"

class CustomerType(str, Enum):
    """Customer type classification."""
    NEW = "new"
    RETURNING = "returning"
    VIP = "vip"
    BUSINESS = "business"

class Conversation(BaseModel):
    """
    Conversation model representing customer-agent interactions.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core identification
    whatsapp_conversation_id: Optional[str] = Field(None, description="WhatsApp conversation ID")
    customer_phone: str = Field(..., description="Customer phone number (WhatsApp ID)")
    customer_name: Optional[str] = Field(None, description="Customer display name")
    customer_profile_url: Optional[str] = Field(None, description="Customer profile picture URL")
    
    # Customer information
    customer_type: CustomerType = Field(default=CustomerType.NEW)
    customer_metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "first_seen": None,
            "last_seen": None,
            "total_conversations": 0,
            "preferred_language": "en",
            "timezone": "UTC",
            "notes": []
        },
        description="Additional customer information"
    )
    
    # Conversation management
    status: ConversationStatus = Field(default=ConversationStatus.PENDING)
    priority: ConversationPriority = Field(default=ConversationPriority.NORMAL)
    channel: ConversationChannel = Field(default=ConversationChannel.WHATSAPP)
    
    # Assignment and routing
    assigned_agent_id: Optional[PyObjectId] = Field(None, description="Currently assigned agent")
    department_id: Optional[PyObjectId] = Field(None, description="Assigned department")
    previous_agents: List[PyObjectId] = Field(default_factory=list, description="History of assigned agents")
    # Participants
    participants: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of participants with roles: [{user_id, role, added_at}]"
    )
    
    # Conversation context
    subject: Optional[str] = Field(None, max_length=200, description="Conversation subject/title")
    initial_message: Optional[str] = Field(None, description="First customer message")
    last_message: Optional[str] = Field(None, description="Most recent message")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
    last_customer_message_at: Optional[datetime] = Field(None, description="Last customer message timestamp")
    last_agent_message_at: Optional[datetime] = Field(None, description="Last agent message timestamp")
    
    # Tagging and categorization (denormalized for performance)
    tags: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Denormalized tag data: [{id, name, slug, category, color, display_name}]"
    )
    categories: List[str] = Field(default_factory=list, description="Conversation categories")
    labels: List[Dict[str, str]] = Field(default_factory=list, description="Custom labels with values")
    
    # Metrics and tracking
    message_count: int = Field(default=0, description="Total message count")
    customer_message_count: int = Field(default=0, description="Customer message count")
    agent_message_count: int = Field(default=0, description="Agent message count")
    
    # Response time tracking
    first_response_time: Optional[int] = Field(None, description="Time to first response (seconds)")
    average_response_time: Optional[int] = Field(None, description="Average response time (seconds)")
    resolution_time: Optional[int] = Field(None, description="Total resolution time (seconds)")
    
    # SLA and escalation
    sla_deadline: Optional[datetime] = Field(None, description="SLA response deadline")
    escalation_deadline: Optional[datetime] = Field(None, description="Escalation deadline")
    is_overdue: bool = Field(default=False, description="Whether conversation is overdue")
    
    # Conversation flow
    is_bot_conversation: bool = Field(default=False, description="Whether bot is handling conversation")
    requires_human_takeover: bool = Field(default=False, description="Whether human intervention is needed")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="Customer satisfaction rating")
    feedback_comment: Optional[str] = Field(None, max_length=1000, description="Customer feedback")
    
    # Session management
    session_started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Conversation start time")
    session_ended_at: Optional[datetime] = Field(None, description="Conversation end time")
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last activity timestamp")
    inactivity_timeout_at: Optional[datetime] = Field(None, description="Inactivity timeout timestamp")
    
    # WhatsApp specific
    whatsapp_data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "phone_number_id": None,
            "business_account_id": None,
            "contact_name": None,
            "profile_name": None,
            "last_seen": None,
            "is_business_verified": False
        },
        description="WhatsApp-specific data"
    )
    
    # Internal flags and settings
    is_internal: bool = Field(default=False, description="Whether this is an internal conversation")
    is_archived: bool = Field(default=False, description="Whether conversation is archived")
    archived_at: Optional[datetime] = Field(None, description="When the conversation was archived (UTC)")
    deleted_at: Optional[datetime] = Field(None, description="When the conversation was soft-deleted (UTC)")
    auto_close_enabled: bool = Field(default=True, description="Whether auto-close is enabled")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[PyObjectId] = Field(None, description="User who created conversation")
    updated_by: Optional[PyObjectId] = Field(None, description="User who last updated conversation")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "customer_phone": "+1234567890",
                "customer_name": "John Doe",
                "status": "active",
                "priority": "normal",
                "channel": "whatsapp",
                "subject": "Product inquiry",
                "tags": ["sales", "product-info"],
                "department_id": "60a7c8b9f123456789abcdef"
            }
        }

class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    customer_phone: str
    customer_name: Optional[str] = None
    priority: ConversationPriority = ConversationPriority.NORMAL
    channel: ConversationChannel = ConversationChannel.WHATSAPP
    department_id: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=200)
    initial_message: Optional[str] = None
    tags: List[Dict[str, Any]] = Field(default_factory=list)
    customer_metadata: Optional[Dict[str, Any]] = None
    whatsapp_data: Optional[Dict[str, Any]] = None

class ConversationUpdate(BaseModel):
    """Schema for updating an existing conversation."""
    status: Optional[ConversationStatus] = None
    priority: Optional[ConversationPriority] = None
    assigned_agent_id: Optional[str] = None
    department_id: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=200)
    tags: Optional[List[Dict[str, Any]]] = None
    categories: Optional[List[str]] = None
    labels: Optional[List[Dict[str, str]]] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_comment: Optional[str] = Field(None, max_length=1000)
    is_archived: Optional[bool] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversationTransfer(BaseModel):
    """Schema for transferring conversations."""
    target_agent_id: Optional[str] = None
    target_department_id: Optional[str] = None
    transfer_reason: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)

class ConversationClose(BaseModel):
    """Schema for closing conversations."""
    resolution_notes: Optional[str] = Field(None, max_length=1000)
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_comment: Optional[str] = Field(None, max_length=1000)
    send_survey: bool = False
    tags: Optional[List[Dict[str, Any]]] = None

class ConversationResponse(BaseModel):
    """Schema for conversation responses."""
    id: str = Field(alias="_id")
    customer_phone: str
    customer_name: Optional[str]
    customer_type: CustomerType
    status: ConversationStatus
    priority: ConversationPriority
    channel: ConversationChannel
    assigned_agent_id: Optional[str]
    department_id: Optional[str]
    subject: Optional[str]
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    tags: List[Dict[str, Any]]
    categories: List[str]
    message_count: int
    satisfaction_rating: Optional[int]
    session_started_at: datetime
    session_ended_at: Optional[datetime]
    last_activity_at: datetime
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
