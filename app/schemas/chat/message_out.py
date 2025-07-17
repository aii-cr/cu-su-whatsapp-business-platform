from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

class MessageResponse(BaseModel):
    """Response schema for a single message."""
    id: PyObjectId = Field(alias="_id")
    conversation_id: PyObjectId
    whatsapp_message_id: Optional[str] = None
    type: str
    direction: str  # inbound, outbound
    sender_role: str  # customer, agent, system
    sender_id: Optional[PyObjectId] = None
    sender_phone: Optional[str] = None
    sender_name: Optional[str] = None
    text_content: Optional[str] = None
    media_url: Optional[str] = None
    media_metadata: Optional[Dict[str, Any]] = None
    template_data: Optional[Dict[str, Any]] = None
    interactive_content: Optional[Dict[str, Any]] = None
    location_data: Optional[Dict[str, Any]] = None
    contact_data: Optional[Dict[str, Any]] = None
    status: str  # sent, delivered, read, failed
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    reply_to_message_id: Optional[PyObjectId] = None
    is_automated: bool = False
    whatsapp_data: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class MessageListResponse(BaseModel):
    """Response schema for a list of messages."""
    messages: List[MessageResponse]
    total: int
    limit: int
    offset: int

class MessageSendResponse(BaseModel):
    """Response schema for message sending operations."""
    message: MessageResponse
    whatsapp_response: Dict[str, Any]

class TemplateListResponse(BaseModel):
    """Response schema for available templates."""
    templates: List[Dict[str, Any]]
    total: int

class MessageStatsResponse(BaseModel):
    """Response schema for message statistics."""
    total_messages: int
    sent_messages: int
    delivered_messages: int
    read_messages: int
    failed_messages: int
    messages_by_type: Dict[str, int]
    messages_by_direction: Dict[str, int]
    average_response_time: Optional[float] = None 