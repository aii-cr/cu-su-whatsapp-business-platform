"""WhatsApp webhook related schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Webhook Verification Challenge
class WebhookChallenge(BaseModel):
    hub_mode: str = Field(alias="hub.mode")
    hub_verify_token: str = Field(alias="hub.verify_token")
    hub_challenge: str = Field(alias="hub.challenge")

    class Config:
        populate_by_name = True

# Webhook Entry
class WebhookEntry(BaseModel):
    id: str = Field(..., description="WhatsApp Business Account ID")
    changes: List[Dict[str, Any]] = Field(..., description="List of changes")

# Main Webhook Payload
class WhatsAppWebhookPayload(BaseModel):
    object: str = Field(..., description="Webhook object type")
    entry: List[WebhookEntry] = Field(..., description="Webhook entries")

# Contact Information
class ContactInfo(BaseModel):
    profile: Dict[str, str] = Field(default={}, description="Contact profile")
    wa_id: str = Field(..., description="WhatsApp ID")

# Message Context (for replies)
class MessageContext(BaseModel):
    from_: str = Field(alias="from", description="Original message sender")
    id: str = Field(..., description="Original message ID")

# Text Message
class TextMessage(BaseModel):
    body: str = Field(..., description="Message text")

# Media Message Base
class MediaMessage(BaseModel):
    id: str = Field(..., description="Media ID")
    mime_type: str = Field(..., description="MIME type")
    sha256: Optional[str] = Field(None, description="SHA256 hash")
    caption: Optional[str] = Field(None, description="Media caption")

# Image Message
class ImageMessage(MediaMessage):
    pass

# Audio Message
class AudioMessage(MediaMessage):
    voice: Optional[bool] = Field(None, description="Is voice message")

# Video Message
class VideoMessage(MediaMessage):
    pass

# Document Message
class DocumentMessage(MediaMessage):
    filename: Optional[str] = Field(None, description="Document filename")

# Sticker Message
class StickerMessage(MediaMessage):
    animated: Optional[bool] = Field(None, description="Is animated sticker")

# Location Message
class LocationMessage(BaseModel):
    latitude: float = Field(..., description="Location latitude")
    longitude: float = Field(..., description="Location longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")

# Contact Message
class ContactMessage(BaseModel):
    contacts: List[Dict[str, Any]] = Field(..., description="Contact information")

# Interactive Message
class InteractiveMessage(BaseModel):
    type: str = Field(..., description="Interactive type")
    button_reply: Optional[Dict[str, str]] = Field(None, description="Button reply")
    list_reply: Optional[Dict[str, str]] = Field(None, description="List reply")

# Order Message (for WhatsApp Business Commerce)
class OrderMessage(BaseModel):
    catalog_id: str = Field(..., description="Catalog ID")
    text: str = Field(..., description="Order text")
    product_items: List[Dict[str, Any]] = Field(..., description="Product items")

# System Message
class SystemMessage(BaseModel):
    body: str = Field(..., description="System message body")
    type: str = Field(..., description="System message type")

# Incoming WhatsApp Message
class IncomingMessage(BaseModel):
    id: str = Field(..., description="Message ID")
    from_: str = Field(alias="from", description="Sender phone number")
    timestamp: str = Field(..., description="Message timestamp")
    type: str = Field(..., description="Message type")
    context: Optional[MessageContext] = Field(None, description="Message context for replies")
    
    # Message content based on type
    text: Optional[TextMessage] = None
    image: Optional[ImageMessage] = None
    audio: Optional[AudioMessage] = None
    video: Optional[VideoMessage] = None
    document: Optional[DocumentMessage] = None
    sticker: Optional[StickerMessage] = None
    location: Optional[LocationMessage] = None
    contacts: Optional[ContactMessage] = None
    interactive: Optional[InteractiveMessage] = None
    order: Optional[OrderMessage] = None
    system: Optional[SystemMessage] = None

    class Config:
        populate_by_name = True

# Message Status Update
class MessageStatus(BaseModel):
    id: str = Field(..., description="Message ID")
    status: str = Field(..., description="Message status")
    timestamp: str = Field(..., description="Status timestamp")
    recipient_id: str = Field(..., description="Recipient WhatsApp ID")
    conversation: Optional[Dict[str, Any]] = Field(None, description="Conversation info")
    pricing: Optional[Dict[str, Any]] = Field(None, description="Pricing info")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error information")

# Webhook Change (messages or statuses)
class WebhookChange(BaseModel):
    value: Dict[str, Any] = Field(..., description="Change value")
    field: str = Field(..., description="Field that changed")

# Processed Webhook Data
class ProcessedWebhookData(BaseModel):
    webhook_id: str = Field(..., description="Unique webhook processing ID")
    business_account_id: str = Field(..., description="WhatsApp Business Account ID")
    phone_number_id: str = Field(..., description="Phone number ID")
    
    # Processed data
    messages: List[IncomingMessage] = Field(default=[], description="Incoming messages")
    statuses: List[MessageStatus] = Field(default=[], description="Status updates")
    contacts: List[ContactInfo] = Field(default=[], description="Contact information")
    errors: List[Dict[str, Any]] = Field(default=[], description="Processing errors")
    
    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
# Webhook Processing Result
class WebhookProcessingResult(BaseModel):
    success: bool = Field(..., description="Processing success status")
    webhook_id: str = Field(..., description="Webhook ID")
    messages_processed: int = Field(default=0, description="Number of messages processed")
    statuses_processed: int = Field(default=0, description="Number of statuses processed")
    errors: List[str] = Field(default=[], description="Processing errors")
    processing_time_ms: float = Field(..., description="Total processing time")

# Outbound Message for WhatsApp API
class OutboundMessageRequest(BaseModel):
    messaging_product: str = Field("whatsapp", description="Messaging product")
    recipient_type: str = Field("individual", description="Recipient type")
    to: str = Field(..., description="Recipient phone number")
    type: str = Field(..., description="Message type")
    text: Optional[Dict[str, Any]] = Field(None, description="Text message content")
    image: Optional[Dict[str, Any]] = Field(None, description="Image message content")
    audio: Optional[Dict[str, Any]] = Field(None, description="Audio message content")
    video: Optional[Dict[str, Any]] = Field(None, description="Video message content")
    document: Optional[Dict[str, Any]] = Field(None, description="Document message content")
    location: Optional[Dict[str, Any]] = Field(None, description="Location message content")
    contacts: Optional[List[Dict[str, Any]]] = Field(None, description="Contact message content")
    interactive: Optional[Dict[str, Any]] = Field(None, description="Interactive message content")
    template: Optional[Dict[str, Any]] = Field(None, description="Template message content")
    context: Optional[Dict[str, str]] = Field(None, description="Message context for replies")

# WhatsApp API Response
class WhatsAppAPIResponse(BaseModel):
    messaging_product: str
    contacts: List[Dict[str, str]] = []
    messages: List[Dict[str, str]] = []
    error: Optional[Dict[str, Any]] = None

# Template Message Component
class TemplateComponent(BaseModel):
    type: str = Field(..., description="Component type")
    sub_type: Optional[str] = Field(None, description="Component sub-type")
    index: Optional[int] = Field(None, description="Component index")
    parameters: List[Dict[str, Any]] = Field(default=[], description="Component parameters")

# Template Message Request
class TemplateMessageRequest(BaseModel):
    messaging_product: str = Field("whatsapp", description="Messaging product")
    recipient_type: str = Field("individual", description="Recipient type")
    to: str = Field(..., description="Recipient phone number")
    type: str = Field("template", description="Message type")
    template: Dict[str, Any] = Field(..., description="Template configuration")

# Media Upload Response
class MediaUploadResponse(BaseModel):
    id: str = Field(..., description="Media ID")
    
# Webhook Subscription
class WebhookSubscription(BaseModel):
    webhook_url: str = Field(..., description="Webhook URL")
    verify_token: str = Field(..., description="Verify token")
    fields: List[str] = Field(default=["messages", "message_deliveries"], description="Subscribed fields")
    
# Rate Limit Information
class RateLimitInfo(BaseModel):
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining calls")
    reset_time: datetime = Field(..., description="Reset time")
    
# Error Response
class WhatsAppErrorResponse(BaseModel):
    error: Dict[str, Any] = Field(..., description="Error details")
    error_code: int = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_subcode: Optional[int] = Field(None, description="Error subcode")
    fbtrace_id: Optional[str] = Field(None, description="Facebook trace ID") 