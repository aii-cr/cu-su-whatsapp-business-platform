from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from app.db.models.base import PyObjectId

class MessageSend(BaseModel):
    """Schema for sending a text message. Accepts either conversation_id or customer_phone."""
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    customer_phone: Optional[str] = Field(None, description="Customer phone number (WhatsApp ID)")
    text_content: str = Field(..., min_length=1, max_length=496, description="Message text")
    reply_to_message_id: Optional[str] = Field(None, description="Message ID to reply to")

    @model_validator(mode='after')
    def require_conversation_id_or_phone(self):
        if not self.conversation_id and not self.customer_phone:
            raise ValueError("Either conversation_id or customer_phone must be provided.")
        return self

class TemplateMessageSend(BaseModel):
    """Schema for sending a template message. Accepts either conversation_id or customer_phone."""
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    customer_phone: Optional[str] = Field(None, description="Customer phone number (WhatsApp ID)")
    template_name: str = Field(..., description="Template name")
    language_code: str = Field("en_US", description="Template language code")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="Template parameters")

    @model_validator(mode='after')
    def require_conversation_id_or_phone(self):
        if not self.conversation_id and not self.customer_phone:
            raise ValueError("Either conversation_id or customer_phone must be provided.")
        return self

class MediaMessageSend(BaseModel):
    """Schema for sending a media message."""
    conversation_id: str = Field(..., description="Conversation ID")
    media_type: str = Field(..., description="Media type (image, audio, video, document)")
    media_url: str = Field(..., description="Media file URL")
    caption: Optional[str] = Field(None, description="Media caption")
    filename: Optional[str] = Field(None, description="Media filename")

class InteractiveMessageSend(BaseModel):
    """Schema for sending an interactive message."""
    conversation_id: str = Field(..., description="Conversation ID")
    interactive_type: str = Field(..., description="Interactive type (button, list)")
    header: Optional[Dict[str, Any]] = Field(None, description="Interactive header")
    body: Dict[str, Any] = Field(..., description="Interactive body")
    footer: Optional[Dict[str, Any]] = Field(None, description="Interactive footer")
    action: Dict[str, Any] = Field(..., description="Interactive action")

class LocationMessageSend(BaseModel):
    """Schema for sending a location message."""
    conversation_id: str = Field(..., description="Conversation ID")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")

class ContactMessageSend(BaseModel):
    """Schema for sending a contact message."""
    conversation_id: str = Field(..., description="Conversation ID")
    contacts: List[Dict[str, Any]] = Field(..., description="Contact information")

class MessageStatusUpdate(BaseModel):
    """Schema for updating message status."""
    status: str = Field(..., description="New message status")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class BulkMessageSend(BaseModel):
    """Schema for bulk message sending."""
    messages: List[MessageSend] = Field(..., description="List of messages to send")
    delay_seconds: Optional[int] = Field(0, description="Delay between messages in seconds") 