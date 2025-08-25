"""
Message schemas for WhatsApp Business Platform.
Handles request/response validation for message operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.whatsapp.chat.message import MessageType, MessageDirection, MessageStatus, SenderRole

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    conversation_id: str = Field(..., description="Conversation ID")
    sender_role: SenderRole = Field(..., description="Role of message sender")
    sender_phone: Optional[str] = Field(None, description="Sender phone number")
    message_type: MessageType = Field(..., description="Type of message content")
    direction: MessageDirection = Field(..., description="Message direction")
    text_content: Optional[str] = Field(None, description="Text message content")
    media_url: Optional[str] = Field(None, description="Media file URL")
    media_metadata: Optional[Dict[str, Any]] = Field(None, description="Media metadata")
    interactive_content: Optional[Dict[str, Any]] = Field(None, description="Interactive message content")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template message data")
    location_data: Optional[Dict[str, Any]] = Field(None, description="Location coordinates and details")
    contact_data: Optional[Dict[str, Any]] = Field(None, description="Contact card information")
    reply_to_message_id: Optional[str] = Field(None, description="Message being replied to")
    context: Optional[Dict[str, Any]] = Field(None, description="Message context and metadata")
    whatsapp_data: Optional[Dict[str, Any]] = Field(None, description="WhatsApp API specific data")

class MessageUpdate(BaseModel):
    """Schema for updating message status."""
    status: Optional[MessageStatus] = Field(None, description="Message status")
    delivery_status: Optional[Dict[str, Any]] = Field(None, description="Delivery status tracking")
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Sentiment analysis score")
    language_detected: Optional[str] = Field(None, description="Detected language code")
    is_flagged: Optional[bool] = Field(None, description="Flagged for review")
    moderation_data: Optional[Dict[str, Any]] = Field(None, description="Content moderation results")

class MessageSend(BaseModel):
    """Schema for sending a new message."""
    conversation_id: str = Field(..., description="Conversation ID")
    message_type: MessageType = Field(default=MessageType.TEXT, description="Type of message content")
    text_content: Optional[str] = Field(None, description="Text message content")
    media_url: Optional[str] = Field(None, description="Media file URL")
    interactive_content: Optional[Dict[str, Any]] = Field(None, description="Interactive message content")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template message data")
    reply_to_message_id: Optional[str] = Field(None, description="Message being replied to")

class MessageReadRequest(BaseModel):
    """Schema for marking messages as read."""
    conversation_id: str = Field(..., description="Conversation ID to mark messages as read")

class MessageReadResponse(BaseModel):
    """Schema for message read response."""
    conversation_id: str = Field(..., description="Conversation ID")
    messages_marked_read: int = Field(..., description="Number of messages marked as read")
    timestamp: datetime = Field(..., description="Timestamp when messages were marked as read")

class MessageResponse(BaseModel):
    """Schema for message responses."""
    id: str = Field(alias="_id", description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    sender_id: Optional[str] = Field(None, description="Sender user ID")
    sender_role: SenderRole = Field(..., description="Role of message sender")
    sender_phone: Optional[str] = Field(None, description="Sender phone number")
    sender_name: Optional[str] = Field(None, description="Sender display name")
    message_type: MessageType = Field(..., description="Type of message content")
    direction: MessageDirection = Field(..., description="Message direction")
    text_content: Optional[str] = Field(None, description="Text message content")
    media_url: Optional[str] = Field(None, description="Media file URL")
    media_metadata: Optional[Dict[str, Any]] = Field(None, description="Media metadata")
    interactive_content: Optional[Dict[str, Any]] = Field(None, description="Interactive message content")
    status: MessageStatus = Field(..., description="Message status")
    delivery_status: Dict[str, Any] = Field(..., description="Delivery status tracking")
    reply_to_message_id: Optional[str] = Field(None, description="Message being replied to")
    is_forwarded: bool = Field(..., description="Whether message was forwarded")
    is_automated: bool = Field(..., description="Whether message was automated")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score")
    language_detected: Optional[str] = Field(None, description="Detected language code")
    is_flagged: bool = Field(..., description="Flagged for review")
    timestamp: datetime = Field(..., description="Message timestamp")
    created_at: datetime = Field(..., description="Message creation timestamp")
    whatsapp_data: Optional[Dict[str, Any]] = Field(None, description="WhatsApp API specific data")

class MessageListResponse(BaseModel):
    """Schema for message list responses."""
    messages: List[MessageResponse] = Field(..., description="List of messages")
    total_count: int = Field(..., description="Total number of messages")
    has_next_page: bool = Field(..., description="Whether there are more messages to load")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")

class MessageStatusUpdate(BaseModel):
    """Schema for message status updates."""
    message_id: str = Field(..., description="Message ID")
    status: MessageStatus = Field(..., description="New message status")
    timestamp: datetime = Field(..., description="Status update timestamp")
    error_code: Optional[str] = Field(None, description="Error code if status is failed")
    error_message: Optional[str] = Field(None, description="Error message if status is failed") 