"""Conversation timeline/history schemas."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.db.models.base import PyObjectId


class HistoryItem(BaseModel):
    type: str
    ts_utc: datetime
    actor: Optional[Dict[str, Any]] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class HistoryResponse(BaseModel):
    conversation_id: PyObjectId
    items: List[HistoryItem]


