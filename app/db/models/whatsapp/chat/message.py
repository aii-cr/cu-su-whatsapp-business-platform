"""
Message model for the WhatsApp Business Platform.
Represents individual messages within conversations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from bson import ObjectId
from enum import Enum
from app.db.models.base import PyObjectId

class MessageType(str, Enum):
    """Message content types."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"
    SYSTEM = "system"  # System generated messages

class MessageDirection(str, Enum):
    """Message direction."""
    INBOUND = "inbound"   # From customer
    OUTBOUND = "outbound" # To customer

class MessageStatus(str, Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class SenderRole(str, Enum):
    """Message sender role."""
    CUSTOMER = "customer"
    AGENT = "agent"
    AI_ASSISTANT = "ai_assistant"
    BOT = "bot"
    SYSTEM = "system"

class Message(BaseModel):
    """
    Message model representing individual messages in conversations.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core identification
    conversation_id: PyObjectId = Field(..., description="Parent conversation ID")
    whatsapp_message_id: Optional[str] = Field(None, description="WhatsApp message ID")
    
    # Sender information
    sender_id: Optional[PyObjectId] = Field(None, description="Sender user ID (null for customers)")
    sender_role: SenderRole = Field(..., description="Role of message sender")
    sender_phone: Optional[str] = Field(None, description="Sender phone number")
    sender_name: Optional[str] = Field(None, description="Sender display name")
    
    # Message content
    message_type: MessageType = Field(..., description="Type of message content")
    direction: MessageDirection = Field(..., description="Message direction")
    
    # Text content
    text_content: Optional[str] = Field(None, description="Text message content")
    
    # Media content
    media_id: Optional[PyObjectId] = Field(None, description="Media file reference ID")
    media_url: Optional[str] = Field(None, description="Media file URL")
    media_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Media metadata (filename, size, mimetype, etc.)"
    )
    
    # Interactive content (buttons, lists, etc.)
    interactive_content: Optional[Dict[str, Any]] = Field(
        None,
        description="Interactive message content (buttons, lists, etc.)"
    )
    
    # Template message data
    template_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Template message data and parameters"
    )
    
    # Location data
    location_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Location coordinates and details"
    )
    
    # Contact data
    contact_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Contact card information"
    )
    
    # Message status and delivery
    status: MessageStatus = Field(default=MessageStatus.PENDING)
    delivery_status: Dict[str, Any] = Field(
        default_factory=lambda: {
            "sent_at": None,
            "delivered_at": None,
            "read_at": None,
            "failed_at": None,
            "error_code": None,
            "error_message": None
        },
        description="Delivery status tracking"
    )
    
    # Threading and replies
    reply_to_message_id: Optional[PyObjectId] = Field(None, description="Message being replied to")
    is_forwarded: bool = Field(default=False, description="Whether message was forwarded")
    forward_count: int = Field(default=0, description="Number of times forwarded")
    
    # Message context
    context: Dict[str, Any] = Field(
        default_factory=lambda: {
            "platform": "whatsapp",
            "device_type": None,
            "user_agent": None,
            "ip_address": None,
            "referred_product": None
        },
        description="Message context and metadata"
    )
    
    # AI and automation
    is_automated: bool = Field(default=False, description="Whether message was automated")
    bot_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Bot-related data (intent, confidence, etc.)"
    )
    
    # Content analysis
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Sentiment analysis score")
    language_detected: Optional[str] = Field(None, description="Detected language code")
    contains_sensitive_data: bool = Field(default=False, description="Contains PII or sensitive information")
    
    # Moderation and compliance
    is_flagged: bool = Field(default=False, description="Flagged for review")
    moderation_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Content moderation results"
    )
    
    # Internal annotations
    internal_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Internal notes and annotations"
    )
    
    # WhatsApp specific data
    whatsapp_data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "phone_number_id": None,
            "business_account_id": None,
            "context": None,
            "errors": [],
            "pricing": None
        },
        description="WhatsApp API specific data"
    )
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Search and indexing
    searchable_content: Optional[str] = Field(None, description="Processed content for search indexing")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "conversation_id": "60a7c8b9f123456789abcdef",
                "sender_role": "customer",
                "sender_phone": "+1234567890",
                "message_type": "text",
                "direction": "inbound",
                "text_content": "Hello, I need help with my order",
                "status": "delivered"
            }
        }

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    conversation_id: str
    sender_role: SenderRole
    sender_phone: Optional[str] = None
    message_type: MessageType
    direction: MessageDirection
    text_content: Optional[str] = None
    media_id: Optional[str] = None
    media_url: Optional[str] = None
    media_metadata: Optional[Dict[str, Any]] = None
    interactive_content: Optional[Dict[str, Any]] = None
    template_data: Optional[Dict[str, Any]] = None
    location_data: Optional[Dict[str, Any]] = None
    contact_data: Optional[Dict[str, Any]] = None
    reply_to_message_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    whatsapp_data: Optional[Dict[str, Any]] = None

class MessageUpdate(BaseModel):
    """Schema for updating message status."""
    status: Optional[MessageStatus] = None
    delivery_status: Optional[Dict[str, Any]] = None
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    language_detected: Optional[str] = None
    is_flagged: Optional[bool] = None
    moderation_data: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MessageSend(BaseModel):
    """Schema for sending a new message."""
    conversation_id: str
    message_type: MessageType = MessageType.TEXT
    text_content: Optional[str] = None
    media_id: Optional[str] = None
    interactive_content: Optional[Dict[str, Any]] = None
    template_data: Optional[Dict[str, Any]] = None
    reply_to_message_id: Optional[str] = None

class MessageResponse(BaseModel):
    """Schema for message responses."""
    id: str = Field(alias="_id")
    conversation_id: str
    sender_id: Optional[str]
    sender_role: SenderRole
    sender_phone: Optional[str]
    sender_name: Optional[str]
    message_type: MessageType
    direction: MessageDirection
    text_content: Optional[str]
    media_id: Optional[str]
    media_url: Optional[str]
    media_metadata: Optional[Dict[str, Any]]
    interactive_content: Optional[Dict[str, Any]]
    status: MessageStatus
    delivery_status: Dict[str, Any]
    reply_to_message_id: Optional[str]
    is_forwarded: bool
    is_automated: bool
    sentiment_score: Optional[float]
    language_detected: Optional[str]
    is_flagged: bool
    timestamp: datetime
    created_at: datetime
    
    class Config:
        populate_by_name = True
