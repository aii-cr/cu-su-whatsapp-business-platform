from pydantic import BaseModel
from datetime import datetime


class Message(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_role: str  # "customer", "agent", "chatbot"
    message: str
    timestamp: datetime
    message_type: str  # "text", "image", etc.
