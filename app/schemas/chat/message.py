"""Message-related request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from app.db.models.base import PyObjectId

# Base Message Creation
class MessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    type: str = Field(..., pattern="^(text|image|audio|video|document|location|contact|template|interactive|sticker)$")
    content: Dict[str, Any] = Field(..., description="Message content based on type")
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message ID this is replying to")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

# Text Message Creation
class TextMessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    text: str = Field(..., min_length=1, max_length=4096, description="Message text")
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message ID this is replying to")
    preview_url: bool = Field(True, description="Whether to generate link previews")

# Media Message Creation
class MediaMessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    media_id: PyObjectId = Field(..., description="Media ID from media upload")
    caption: Optional[str] = Field(None, max_length=1024, description="Media caption")
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message ID this is replying to")

# Template Message Creation
class TemplateMessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    template_name: str = Field(..., description="Template name")
    language_code: str = Field("en_US", description="Template language code")
    parameters: List[Dict[str, Any]] = Field(default=[], description="Template parameters")
    components: Optional[List[Dict[str, Any]]] = Field(None, description="Template components")

# Location Message Creation
class LocationMessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    latitude: float = Field(..., ge=-90, le=90, description="Location latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Location longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message ID this is replying to")

# Contact Message Creation
class ContactMessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    contacts: List[Dict[str, Any]] = Field(..., min_items=1, description="Contact information")
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message ID this is replying to")

# Interactive Message Creation
class InteractiveMessageCreate(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    interactive_type: str = Field(..., pattern="^(button|list)$", description="Interactive message type")
    body: str = Field(..., description="Message body")
    footer: Optional[str] = Field(None, description="Message footer")
    action: Dict[str, Any] = Field(..., description="Interactive action configuration")
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message ID this is replying to")

# Message Update
class MessageUpdate(BaseModel):
    content: Optional[Dict[str, Any]] = Field(None, description="Updated message content")
    status: Optional[str] = Field(None, description="Updated message status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

# Message Response
class MessageResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    conversation_id: PyObjectId
    whatsapp_message_id: Optional[str] = None
    type: str
    direction: str  # inbound, outbound
    sender_role: str  # customer, agent, system
    sender_id: Optional[PyObjectId] = None
    content: Dict[str, Any]
    status: str  # sent, delivered, read, failed
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    reply_to_message_id: Optional[PyObjectId] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Message with Context Response
class MessageDetailResponse(MessageResponse):
    sender_name: Optional[str] = None
    conversation_customer_name: Optional[str] = None
    conversation_customer_phone: str
    reply_to_message: Optional[Dict[str, Any]] = None
    media_info: Optional[Dict[str, Any]] = None

# Message List Response
class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    per_page: int
    pages: int
    conversation_id: PyObjectId

# Message Query Parameters
class MessageQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    conversation_id: Optional[PyObjectId] = Field(None, description="Filter by conversation")
    type: Optional[str] = Field(None, description="Filter by message type")
    direction: Optional[str] = Field(None, description="Filter by direction")
    sender_role: Optional[str] = Field(None, description="Filter by sender role")
    status: Optional[str] = Field(None, description="Filter by status")
    from_date: Optional[datetime] = Field(None, description="Filter messages from this date")
    to_date: Optional[datetime] = Field(None, description="Filter messages to this date")
    search: Optional[str] = Field(None, description="Search in message content")
    has_media: Optional[bool] = Field(None, description="Filter messages with media")
    sort_by: str = Field("timestamp", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

# Message Status Update
class MessageStatusUpdate(BaseModel):
    message_id: PyObjectId = Field(..., description="Message ID")
    status: str = Field(..., pattern="^(sent|delivered|read|failed)$", description="New status")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    timestamp: Optional[datetime] = Field(None, description="Status timestamp")

# Bulk Message Status Update
class BulkMessageStatusUpdate(BaseModel):
    message_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="List of message IDs")
    status: str = Field(..., pattern="^(sent|delivered|read|failed)$", description="New status")
    timestamp: Optional[datetime] = Field(None, description="Status timestamp")

# Message Read Receipt
class MessageReadReceipt(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    message_ids: List[PyObjectId] = Field(..., description="Message IDs that were read")
    read_by_agent_id: PyObjectId = Field(..., description="Agent who read the messages")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")

# Message Statistics
class MessageStatsResponse(BaseModel):
    total_messages: int
    messages_by_type: Dict[str, int]
    messages_by_direction: Dict[str, int]
    messages_by_status: Dict[str, int]
    media_messages_count: int
    template_messages_count: int
    average_response_time_minutes: float
    message_volume_by_hour: List[Dict[str, Any]]

# Message Content Validation
class MessageContentValidation(BaseModel):
    type: str = Field(..., description="Message type to validate")
    content: Dict[str, Any] = Field(..., description="Content to validate")

# Message Search
class MessageSearchParams(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    conversation_ids: Optional[List[PyObjectId]] = Field(None, description="Limit search to specific conversations")
    message_types: Optional[List[str]] = Field(None, description="Limit search to specific message types")
    sender_roles: Optional[List[str]] = Field(None, description="Limit search to specific sender roles")
    from_date: Optional[datetime] = Field(None, description="Search messages from this date")
    to_date: Optional[datetime] = Field(None, description="Search messages to this date")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

# Message Export Request
class MessageExportRequest(BaseModel):
    conversation_ids: Optional[List[PyObjectId]] = Field(None, description="Specific conversations to export")
    from_date: Optional[datetime] = Field(None, description="Export messages from this date")
    to_date: Optional[datetime] = Field(None, description="Export messages to this date")
    format: str = Field("csv", pattern="^(csv|json|xlsx)$", description="Export format")
    include_media: bool = Field(False, description="Include media files in export")
    email_to: Optional[str] = Field(None, description="Email address to send export")

# Quick Reply
class QuickReply(BaseModel):
    conversation_id: PyObjectId = Field(..., description="Conversation ID")
    template_id: str = Field(..., description="Quick reply template ID")
    variables: Dict[str, str] = Field(default={}, description="Template variables")

# Message Reaction
class MessageReaction(BaseModel):
    message_id: PyObjectId = Field(..., description="Message ID to react to")
    emoji: str = Field(..., description="Reaction emoji")
    action: str = Field("add", pattern="^(add|remove)$", description="Reaction action")

# WhatsApp Webhook Message
class WhatsAppWebhookMessage(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    statuses: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None 